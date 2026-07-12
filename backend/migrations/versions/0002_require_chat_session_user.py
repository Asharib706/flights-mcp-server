"""require chat_sessions.user_id (auth now exists)

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-13

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Pre-auth (Plan A) sessions have no owner and can't be attributed to a user;
    # this is pre-launch dev data only, so drop them rather than invent an owner.
    # ON DELETE CASCADE on chat_messages.session_id takes their messages with them.
    op.execute("DELETE FROM chat_sessions WHERE user_id IS NULL")
    op.alter_column("chat_sessions", "user_id", nullable=False)


def downgrade() -> None:
    op.alter_column("chat_sessions", "user_id", nullable=True)
