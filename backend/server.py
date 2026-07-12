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
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# uvicorn only configures its own loggers (uvicorn/uvicorn.access/uvicorn.error), not
# the root logger, so a bare getLogger(...).info(...) here would be silently dropped —
# give this logger its own handler/level rather than assume one exists.
guardrail_logger = logging.getLogger("skymind.guardrail")
guardrail_logger.setLevel(logging.INFO)
if not guardrail_logger.handlers:
    _guardrail_handler = logging.StreamHandler()
    _guardrail_handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
    guardrail_logger.addHandler(_guardrail_handler)

from dotenv import load_dotenv
load_dotenv()

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

# ── Add parent directory to path so we can import load_mcp ───────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from load_mcp import load_all_tools
from db import async_session
from models import ChatSession, ChatMessage, User, UserMemory
from auth import (
    COOKIE_NAME,
    COOKIE_SECURE,
    JWT_EXPIRES,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from memory import (
    delete_fact,
    load_user_memory,
    render_memory_for_prompt,
    run_memory_extraction,
    upsert_fact,
)

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


# ── Guardrail: keep the assistant on travel topics ───────────────────────────
# Prompt-only for now (see backend plan) — a determined user can talk around this,
# but it's the right first tier: free, zero latency. GUARDRAIL_MARKER lets us
# detect (heuristically, best-effort) when it actually fires, so refusals can be
# logged as data for a future classifier tier rather than just disappearing.
GUARDRAIL_REFUSAL = (
    "I'm SkyMind, focused on flights, hotels, and trip planning — happy to help you find "
    "or book travel instead. What trip can I help with?"
)
GUARDRAIL_MARKER = "focused on flights, hotels, and trip planning"

# ── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are SkyMind, a helpful and professional AI travel assistant with access to "
    "both flight search tools AND hotel search tools.\n\n"

    "SCOPE — READ FIRST:\n"
    "You only help with travel: flights, hotels, trip planning, itineraries, destinations,\n"
    "visas/travel documents (general info only, not legal advice), packing, travel budgeting,\n"
    "and currency/weather as it relates to a trip.\n"
    "If the user asks about anything outside this scope (coding help, general trivia, math,\n"
    "unrelated advice, etc.), politely decline in one sentence and redirect. Do not answer\n"
    "the off-topic question first and then redirect — decline before answering. Use exactly\n"
    f"this redirect, verbatim: \"{GUARDRAIL_REFUSAL}\"\n\n"

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


async def get_or_create_chat_session(
    db: AsyncSession, session_id: str | None, user_id: uuid.UUID
) -> ChatSession:
    """Look up a session by id *owned by this user*, or create a new one.

    Requiring the user_id match (not just the id) is what stops one user from
    reading another user's history by guessing/reusing a session_id.
    """
    if session_id:
        try:
            sid = uuid.UUID(session_id)
        except ValueError:
            sid = None
        if sid is not None:
            result = await db.execute(
                select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == user_id)
            )
            existing = result.scalar_one_or_none()
            if existing is not None:
                return existing

    new_session = ChatSession(user_id=user_id)
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


def stringify_ai_content(content) -> str:
    """Flatten an AI message's content to plain text.

    Gemini sometimes returns a list of content blocks (e.g. carrying a
    thought-signature) instead of a plain string; chat_messages.content is a
    text column, so this normalizes either shape before it's stored or sent.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        return "".join(parts)
    return str(content) if content else ""


# ── Global MCP context holder ────────────────────────────────────────────────
mcp_tools = None
agent_executor = None
llm = None  # kept separately from agent_executor for the memory-extraction background task


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start MCP connection and agent on server startup; clean up on shutdown."""
    global mcp_tools, agent_executor, llm

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


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class OnboardingRequest(BaseModel):
    home_airport: str | None = None
    trip_type: str | None = None
    budget_band: str | None = None
    cabin_class: str | None = None
    interests: list[str] = []
    travel_frequency: str | None = None
    constraints: str | None = None


def user_out(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "onboarding_done": user.onboarding_done,
    }


def set_session_cookie(response: Response, user_id: uuid.UUID) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=create_access_token(user_id),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=int(JWT_EXPIRES.total_seconds()),
        path="/",
    )


# ── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "llm_provider": LLM_PROVIDER,
        "tools_loaded": len(mcp_tools) if mcp_tools else 0,
    }


@app.post("/api/auth/register")
async def register(payload: RegisterRequest, response: Response):
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    async with async_session() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="An account with this email already exists")

        user = User(
            email=email,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    set_session_cookie(response, user.id)
    return user_out(user)


@app.post("/api/auth/login")
async def login(payload: LoginRequest, response: Response):
    email = payload.email.strip().lower()

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    set_session_cookie(response, user.id)
    return user_out(user)


@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "logged_out"}


@app.get("/api/auth/me")
async def me(current_user: User = Depends(get_current_user)):
    return user_out(current_user)


@app.post("/api/onboarding")
async def submit_onboarding(
    payload: OnboardingRequest, current_user: User = Depends(get_current_user)
):
    """One-time onboarding questionnaire; seeds the user's memory profile."""
    facts: dict[str, tuple[str, str]] = {}  # key -> (value, category)
    if payload.home_airport:
        facts["home_airport"] = (payload.home_airport.strip().upper(), "fact")
    if payload.trip_type:
        facts["trip_type"] = (payload.trip_type, "preference")
    if payload.budget_band:
        facts["budget_band"] = (payload.budget_band, "preference")
    if payload.cabin_class:
        facts["cabin_class"] = (payload.cabin_class, "preference")
    if payload.interests:
        facts["interests"] = (", ".join(payload.interests), "interest")
    if payload.travel_frequency:
        facts["travel_frequency"] = (payload.travel_frequency, "fact")
    if payload.constraints:
        facts["constraints"] = (payload.constraints, "constraint")

    async with async_session() as db:
        for key, (value, category) in facts.items():
            await upsert_fact(db, current_user.id, key, value, category, 1.0, "onboarding")
        await db.execute(
            update(User).where(User.id == current_user.id).values(onboarding_done=True)
        )
        await db.commit()

    return {"status": "onboarding_complete"}


@app.get("/api/memory")
async def get_memory(current_user: User = Depends(get_current_user)):
    """What SkyMind currently knows about this traveler."""
    async with async_session() as db:
        rows = await load_user_memory(db, current_user.id)
    return [
        {
            "key": r.key,
            "value": r.value,
            "category": r.category,
            "source": r.source,
            "confidence": r.confidence,
            "updated_at": r.updated_at.isoformat(),
        }
        for r in rows
    ]


@app.delete("/api/memory/{key}")
async def forget_memory(key: str, current_user: User = Depends(get_current_user)):
    """Let a user remove a single remembered fact."""
    async with async_session() as db:
        await delete_fact(db, current_user.id, key)
        await db.commit()
    return {"status": "deleted", "key": key}


@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Stream agent responses via Server-Sent Events (SSE)."""
    user_msg = request.message.strip()

    if not user_msg:
        return {"error": "Empty message", "session_id": request.session_id}

    # Resolve (or create) the chat session and load its recent history from Postgres.
    async with async_session() as db:
        chat_session = await get_or_create_chat_session(db, request.session_id, current_user.id)
        session_id = str(chat_session.id)

        memory_rows = await load_user_memory(db, current_user.id)
        history_rows = await load_recent_messages(db, chat_session.id)
        chat_history = history_to_lc_messages(history_rows)
        chat_history.append(HumanMessage(content=user_msg))

        memory_line = render_memory_for_prompt(memory_rows)
        if memory_line:
            chat_history = [SystemMessage(content=memory_line)] + chat_history

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
                        final_ai_content = stringify_ai_content(message.content)
                        data = json.dumps({
                            "type": "ai_message",
                            "content": final_ai_content,
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
                # Without this, chat_sessions.updated_at never changes after creation
                # (inserting a child chat_messages row doesn't touch the parent), which
                # would break the sidebar's "most recently active" ordering.
                await db.execute(
                    update(ChatSession).where(ChatSession.id == chat_session.id).values(updated_at=func.now())
                )
                await db.commit()

            # Best-effort: let memory catch up on anything durable from this
            # turn *after* the response is sent, so it never adds latency.
            if final_ai_content:
                background_tasks.add_task(
                    run_memory_extraction, llm, current_user.id, user_msg, final_ai_content
                )

            if GUARDRAIL_MARKER in final_ai_content:
                guardrail_logger.info(
                    "guardrail_block user_id=%s session_id=%s message=%r",
                    current_user.id,
                    session_id,
                    user_msg[:200],
                )

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
        background=background_tasks,
    )


@app.post("/api/reset")
async def reset_session(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Reset a chat session to clear history."""
    session_id = request.session_id
    if session_id:
        try:
            sid = uuid.UUID(session_id)
        except ValueError:
            sid = None
        if sid is not None:
            async with async_session() as db:
                await db.execute(
                    delete(ChatSession).where(
                        ChatSession.id == sid, ChatSession.user_id == current_user.id
                    )
                )
                await db.commit()
    return {"status": "reset", "session_id": session_id}


@app.get("/api/sessions")
async def list_sessions(current_user: User = Depends(get_current_user)):
    """The authenticated user's chat sessions, most recently active first."""
    async with async_session() as db:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == current_user.id, ChatSession.archived.is_(False))
            .order_by(ChatSession.updated_at.desc())
            .limit(50)
        )
        sessions = list(result.scalars().all())

        out = []
        for s in sessions:
            preview_result = await db.execute(
                select(ChatMessage.content)
                .where(ChatMessage.session_id == s.id, ChatMessage.role == "user")
                .order_by(ChatMessage.created_at.asc())
                .limit(1)
            )
            first_user_msg = preview_result.scalar_one_or_none()
            out.append({
                "id": str(s.id),
                "title": s.title or (first_user_msg[:60] if first_user_msg else "New conversation"),
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            })
    return out


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, current_user: User = Depends(get_current_user)):
    """Full message history for one session (for loading it back into the UI)."""
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")

    async with async_session() as db:
        session_result = await db.execute(
            select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == current_user.id)
        )
        # 404 either way (not found vs. not yours) so this can't be used to probe
        # for the existence of another user's session id.
        if session_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Session not found")

        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == sid)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = list(result.scalars().all())

    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "tool_events": m.tool_events,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
