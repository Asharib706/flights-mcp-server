"""
FastAPI backend for the Flights Chatbot.
Streams LLM responses via Server-Sent Events (SSE).
Supports configurable LLM provider: LM Studio (default) or Gemini.

Usage:
  cd backend
  uvicorn server:app --reload --port 8000

Environment variables (optional):
  LLM_PROVIDER   = "lmstudio" (default) | "gemini"
  LM_STUDIO_URL  = "http://127.0.0.1:1234/v1"
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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, AIMessage

# ── Add parent directory to path so we can import load_mcp ───────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from load_mcp import load_flight_tools

# ── LLM Provider Configuration ──────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "lmstudio").lower()


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
    "You are a helpful and professional travel assistant with access to flight search tools.\n\n"
    "GENERAL BEHAVIOR:\n"
    "- Be friendly, clear, and conversational.\n"
    "- Guide the user step-by-step when required information is missing.\n"
    "- Only call tools when all required parameters are confirmed.\n"
    "- Format your responses using Markdown for better readability.\n"
    "- Use bullet points, bold text, and headers to structure flight results.\n\n"
    "CRITICAL WORKFLOW RULES:\n"
    "1. ALWAYS call `get_current_date` FIRST before performing any flight search "
    "to ensure you are using the correct year and today's date context.\n\n"
    "2. Flight search tools require 3-letter IATA airport codes (e.g., 'SEA', 'HND').\n\n"
    "3. If the user provides a city or country instead of a specific airport:\n"
    "   - Call `get_airport` to find the correct IATA code(s).\n"
    "   - If multiple airports serve that area, present all matching options to the user.\n"
    "   - For cities with multiple airports, use `search_flights_multi_airport`.\n\n"
    "4. ALL flight search tools REQUIRE a `departure_date` in 'YYYY-MM-DD' format.\n"
    "   - If the user does not provide a specific departure date, ask for it.\n"
    "   - NEVER call flight tools without a confirmed departure date.\n\n"
    "5. For comparing prices across dates, use `search_flights_multi_date`.\n\n"
    "6. After receiving tool results, present them in a friendly, structured format.\n"
)


# ── Session Storage (in-memory) ──────────────────────────────────────────────
sessions: dict[str, list] = {}

# ── Global MCP context holder ────────────────────────────────────────────────
mcp_tools = None
agent_executor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start MCP connection and agent on server startup; clean up on shutdown."""
    global mcp_tools, agent_executor

    # We need to keep the MCP context alive for the lifetime of the server.
    # Use an async generator pattern to manage the context.
    mcp_cm = load_flight_tools()
    tools = await mcp_cm.__aenter__()
    mcp_tools = tools

    llm = create_llm()

    from langgraph.prebuilt import create_react_agent
    agent_executor = create_react_agent(model=llm, tools=tools, prompt=SYSTEM_PROMPT)

    print(f"✅ Server ready | LLM: {LLM_PROVIDER} | Tools: {len(tools)}")

    yield

    # Cleanup
    await mcp_cm.__aexit__(None, None, None)


# ── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(title="Flights Chatbot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
    session_id = request.session_id or str(uuid.uuid4())
    user_msg = request.message.strip()

    if not user_msg:
        return {"error": "Empty message", "session_id": session_id}

    # Get or create session history
    if session_id not in sessions:
        sessions[session_id] = []

    chat_history = sessions[session_id]
    chat_history.append(HumanMessage(content=user_msg))

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generate SSE events from the agent stream."""
        try:
            inputs = {"messages": chat_history}
            final_ai_content = ""
            tool_events = []

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
                            tool_data = json.dumps({
                                "type": "tool_call",
                                "tool_name": tc["name"],
                                "session_id": session_id,
                            })
                            yield f"data: {tool_data}\n\n"

                elif message.type == "tool":
                    tool_result = json.dumps({
                        "type": "tool_result",
                        "content": str(message.content)[:500],
                        "session_id": session_id,
                    })
                    yield f"data: {tool_result}\n\n"

            # Update session history with the final state
            sessions[session_id] = event["messages"]

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
    if session_id and session_id in sessions:
        del sessions[session_id]
    return {"status": "reset", "session_id": session_id}
