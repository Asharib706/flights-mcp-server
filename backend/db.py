"""
Async SQLAlchemy engine and session factory backed by Supabase Postgres.
"""

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add the Supabase connection string "
        "(Project Settings -> Database -> Connection string -> Session pooler) "
        "to backend/.env."
    )

# Normalize to the asyncpg driver regardless of which scheme Supabase hands out.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    # Supabase's connection pooler (Supavisor) doesn't reliably support asyncpg's
    # server-side prepared statement cache across pooled connections; disabling it
    # trades a little per-query overhead for correctness.
    connect_args={"statement_cache_size": 0},
)

async_session = async_sessionmaker(engine, expire_on_commit=False)
