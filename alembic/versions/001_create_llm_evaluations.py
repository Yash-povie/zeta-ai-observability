"""create llm_evaluations table

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trace_id", sa.String(32), nullable=False),
        sa.Column("agent_node", sa.Text(), nullable=False),
        sa.Column("eval_model", sa.Text(), nullable=False),
        sa.Column("hallucination_score", sa.Float(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("eval_reasoning", sa.Text(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_llm_eval_created_at", "llm_evaluations", ["created_at"])
    op.create_index("idx_llm_eval_trace_id", "llm_evaluations", ["trace_id"])
    op.create_index("idx_llm_eval_agent_node", "llm_evaluations", ["agent_node"])


def downgrade() -> None:
    op.drop_table("llm_evaluations")