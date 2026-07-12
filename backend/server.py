"""
FastAPI backend for the SkyMind Travel Chatbot.
Streams LLM responses via Server-Sent Events (SSE).
Supports flights (flights.py) and hotels (hotels.py) MCP servers.
Supports configurable LLM provider: LM Studio (default) or Gemini.

Usage:
  cd backend
  uvicorn server:app --reload --port 8000

Environment variables (optional):
  LLM_PROVIDER    = "lmstudio" (default) | "gemini"
  LM_STUDIO_URL   = "http://127.0.0.1:1234/v1"
  LM_STUDIO_MODEL = "qwen/qwen2.5-vl-7b"
  GEMINI_API_KEY  = "your-key-here"
  GEMINI_MODEL    = "gemini-2.5-pro"
"""

import os
import sys
import json
import uuid
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# ── Add parent directory to path so we can import load_mcp ───────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from load_mcp import load_all_tools
from db import async_session
from models import ChatSession, ChatMessage

# ── LLM Provider Configuration ──────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()


def create_llm():
    """Create the LLM instance based on the configured provider."""
    if LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-pro"),
            api_key=os.getenv("GEMINI_API_KEY", ""),
            temperature=0.7,
        )
    else:  # lmstudio (default)
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            base_url=os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234/v1"),
            api_key=os.getenv("LM_STUDIO_API_KEY", "lm-studio"),
            model=os.getenv("LM_STUDIO_MODEL", "qwen/qwen2.5-vl-7b"),
            temperature=0.7,
        )


# ── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are SkyMind, a helpful and professional AI travel assistant with access to "
    "both flight search tools AND hotel search tools.\n\n"

    "GENERAL BEHAVIOR:\n"
    "- Be friendly, clear, and conversational.\n"
    "- Guide the user step-by-step when required information is missing.\n"
    "- Only call tools when all required parameters are confirmed.\n"
    "- Format your responses using Markdown for better readability.\n"
    "- Use bullet points, bold text, and headers to structure results.\n\n"

    "FLIGHT SEARCH RULES:\n"
    "1. ALWAYS call `get_current_date` FIRST before any flight search.\n"
    "2. Flight tools require 3-letter IATA airport codes (e.g., 'SEA', 'HND').\n"
    "3. If the user gives a city name, call `get_airport` to resolve the IATA code.\n"
    "4. ALL flight search tools REQUIRE `departure_date` in 'YYYY-MM-DD' format.\n"
    "5. For cities with multiple airports, use `search_flights_multi_airport`.\n"
    "6. For comparing prices across dates, use `search_flights_multi_date`.\n\n"

    "HOTEL SEARCH RULES:\n"
    "1. Hotel tools accept city names, abbreviations, or IATA codes for location.\n"
    "2. ALL hotel tools require `checkin_date` and `checkout_date` in 'YYYY-MM-DD' format.\n"
    "3. Use `search_hotels` for general queries, `get_cheapest_hotels` for budget queries,\n"
    "   `get_best_rated_hotels` for quality, `get_best_value_hotels` for value, and\n"
    "   `filter_hotels_by_amenities` when the user specifies amenities like 'pool' or 'wifi'.\n"
    "4. If the user hasn't specified check-in/check-out dates, ask before calling hotel tools.\n\n"

    "After receiving tool results, present them in a friendly, structured, Markdown format.\n"
)


# ── Persistence helpers ──────────────────────────────────────────────────────
# Chat history now lives in Postgres (see db.py, models.py) instead of an
# in-memory dict, so it survives restarts and works across multiple workers.

CHAT_HISTORY_LIMIT = 20  # capped so token cost doesn't grow unbounded per session


async def get_or_create_chat_session(db: AsyncSession, session_id: str | None) -> ChatSession:
    """Look up an existing chat session by id, or create a new one."""
    if session_id:
        try:
            sid = uuid.UUID(session_id)
        except ValueError:
            sid = None
        if sid is not None:
            result = await db.execute(select(ChatSession).where(ChatSession.id == sid))
            existing = result.scalar_one_or_none()
            if existing is not None:
                return existing

    new_session = ChatSession()
    db.add(new_session)
    await db.flush()  # populate the server-generated id
    return new_session


async def load_recent_messages(
    db: AsyncSession, chat_session_id, limit: int = CHAT_HISTORY_LIMIT
) -> list[ChatMessage]:
    """Load the last `limit` messages for a session, oldest first."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == chat_session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    rows = list(result.scalars().all())
    rows.reverse()
    return rows


def history_to_lc_messages(rows: list[ChatMessage]) -> list:
    """Convert stored ChatMessage rows into LangChain message objects for the agent."""
    messages: list = []
    for row in rows:
        if row.role == "user":
            messages.append(HumanMessage(content=row.content))
        elif row.role == "ai":
            messages.append(AIMessage(content=row.content))
    return messages


# ── Global MCP context holder ────────────────────────────────────────────────
mcp_tools = None
agent_executor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start MCP connection and agent on server startup; clean up on shutdown."""
    global mcp_tools, agent_executor

    # We need to keep the MCP context alive for the lifetime of the server.
    # Use `async with` so the contexts remain properly nested in the same task.
    async with load_all_tools() as tools:
        mcp_tools = tools

        llm = create_llm()

        from langgraph.prebuilt import create_react_agent
        agent_executor = create_react_agent(model=llm, tools=tools, prompt=SYSTEM_PROMPT)

        print(f"✅ Server ready | LLM: {LLM_PROVIDER} | Tools: {len(tools)}")

        yield


# ── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(title="Flights Chatbot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


# ── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "llm_provider": LLM_PROVIDER,
        "tools_loaded": len(mcp_tools) if mcp_tools else 0,
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Stream agent responses via Server-Sent Events (SSE)."""
    user_msg = request.message.strip()

    if not user_msg:
        return {"error": "Empty message", "session_id": request.session_id}

    # Resolve (or create) the chat session and load its recent history from Postgres.
    async with async_session() as db:
        chat_session = await get_or_create_chat_session(db, request.session_id)
        session_id = str(chat_session.id)

        history_rows = await load_recent_messages(db, chat_session.id)
        chat_history = history_to_lc_messages(history_rows)
        chat_history.append(HumanMessage(content=user_msg))

        db.add(ChatMessage(session_id=chat_session.id, role="user", content=user_msg))
        await db.commit()

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generate SSE events from the agent stream."""
        try:
            inputs = {"messages": chat_history}
            final_ai_content = ""
            collected_tool_events: list[dict] = []

            async for event in agent_executor.astream(inputs, stream_mode="values"):
                message = event["messages"][-1]

                # Skip the user message we just added
                if message.type == "human" and message.content == user_msg:
                    continue

                if message.type == "ai":
                    if message.content:
                        final_ai_content = message.content
                        data = json.dumps({
                            "type": "ai_message",
                            "content": message.content,
                            "session_id": session_id,
                        })
                        yield f"data: {data}\n\n"

                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tc in message.tool_calls:
                            collected_tool_events.append({
                                "type": "tool_call",
                                "tool_name": tc["name"],
                            })
                            tool_data = json.dumps({
                                "type": "tool_call",
                                "tool_name": tc["name"],
                                "session_id": session_id,
                            })
                            yield f"data: {tool_data}\n\n"

                elif message.type == "tool":
                    result_content = str(message.content)[:500]
                    collected_tool_events.append({
                        "type": "tool_result",
                        "content": result_content,
                    })
                    tool_result = json.dumps({
                        "type": "tool_result",
                        "content": result_content,
                        "session_id": session_id,
                    })
                    yield f"data: {tool_result}\n\n"

            # Persist the AI turn (with any tool badges) now that streaming is done.
            async with async_session() as db:
                db.add(ChatMessage(
                    session_id=chat_session.id,
                    role="ai",
                    content=final_ai_content,
                    tool_events=collected_tool_events or None,
                ))
                await db.commit()

            # Send done event
            done = json.dumps({"type": "done", "session_id": session_id})
            yield f"data: {done}\n\n"

        except Exception as e:
            error_data = json.dumps({
                "type": "error",
                "content": str(e),
                "session_id": session_id,
            })
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-ID": session_id,
        },
    )


@app.post("/api/reset")
async def reset_session(request: ChatRequest):
    """Reset a chat session to clear history."""
    session_id = request.session_id
    if session_id:
        try:
            sid = uuid.UUID(session_id)
        except ValueError:
            sid = None
        if sid is not None:
            async with async_session() as db:
                await db.execute(delete(ChatSession).where(ChatSession.id == sid))
                await db.commit()
    return {"status": "reset", "session_id": session_id}
