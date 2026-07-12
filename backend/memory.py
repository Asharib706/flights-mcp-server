"""
Long-term per-user memory: extraction from conversation turns, and injection
into the system prompt. Separate from chat_messages (Plan A), which is the
literal per-chat history — this is durable facts that carry across sessions.
"""

import uuid
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from db import async_session
from models import UserMemory

EXTRACTION_PROMPT = """You maintain a long-term memory profile for a travel assistant's user.
Given what's already known about them and the latest exchange, decide what should change.

Rules:
- Only propose an operation for something durable about the traveler (a preference, a
  constraint, an interest, or a standing fact) — not one-off details specific to the trip
  being discussed right now, which are already saved in the chat itself.
- Use short, stable, snake_case keys (e.g. "home_airport", "cabin_class", "budget_band").
  Reuse an existing key if the new value should replace it (op="upsert"); use a new key for a
  genuinely new fact.
- Use op="delete" only if the user explicitly said something is no longer true.
- If nothing durable was said, return an empty operations list. Never invent facts.

Existing known facts about this user:
{existing_memory}

Latest exchange:
User: {user_message}
Assistant: {ai_message}
"""


class MemoryOp(BaseModel):
    op: Literal["upsert", "delete"]
    key: str
    value: str = ""
    category: Literal["preference", "constraint", "interest", "fact"] = "fact"
    confidence: float = 0.7


class MemoryOpsResult(BaseModel):
    operations: list[MemoryOp]


async def load_user_memory(db: AsyncSession, user_id: uuid.UUID) -> list[UserMemory]:
    result = await db.execute(select(UserMemory).where(UserMemory.user_id == user_id))
    return list(result.scalars().all())


def render_memory_for_prompt(rows: list[UserMemory]) -> str:
    """Compact, single-line form for injection into the agent's context."""
    if not rows:
        return ""
    facts = ", ".join(f"{r.key}={r.value}" for r in rows)
    return f"Known about this traveler: {facts}."


def _format_existing(rows: list[UserMemory]) -> str:
    if not rows:
        return "(none yet)"
    return "\n".join(f"- {r.key}={r.value} ({r.category})" for r in rows)


async def upsert_fact(
    db: AsyncSession,
    user_id: uuid.UUID,
    key: str,
    value: str,
    category: str,
    confidence: float,
    source: str,
) -> None:
    stmt = pg_insert(UserMemory).values(
        user_id=user_id,
        category=category,
        key=key,
        value=value,
        confidence=confidence,
        source=source,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[UserMemory.user_id, UserMemory.key],
        set_={
            "value": stmt.excluded.value,
            "category": stmt.excluded.category,
            "confidence": stmt.excluded.confidence,
            "source": stmt.excluded.source,
            "updated_at": func.now(),
        },
    )
    await db.execute(stmt)


async def delete_fact(db: AsyncSession, user_id: uuid.UUID, key: str) -> None:
    await db.execute(
        sa_delete(UserMemory).where(UserMemory.user_id == user_id, UserMemory.key == key)
    )


async def apply_memory_ops(db: AsyncSession, user_id: uuid.UUID, ops: list[MemoryOp]) -> None:
    for op in ops:
        if op.op == "delete":
            await delete_fact(db, user_id, op.key)
        else:
            await upsert_fact(db, user_id, op.key, op.value, op.category, op.confidence, "inferred")
    await db.commit()


async def run_memory_extraction(
    llm, user_id: uuid.UUID, user_message: str, ai_message: str
) -> None:
    """Background task: propose and apply memory updates from the latest exchange.

    Best-effort by design — a failure here must never surface as a user-facing
    chat error, since it runs after the response has already been sent.
    """
    try:
        async with async_session() as db:
            existing = await load_user_memory(db, user_id)

        prompt = EXTRACTION_PROMPT.format(
            existing_memory=_format_existing(existing),
            user_message=user_message,
            ai_message=ai_message,
        )
        structured_llm = llm.with_structured_output(MemoryOpsResult)
        result: MemoryOpsResult = await structured_llm.ainvoke(prompt)

        if result.operations:
            async with async_session() as db:
                await apply_memory_ops(db, user_id, result.operations)
    except Exception as e:
        print(f"⚠️ Memory extraction failed (non-fatal): {e}")
