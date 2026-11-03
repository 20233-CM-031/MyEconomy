"""add one-time email verification challenges

Revision ID: 3b2e7f4a9c10
Revises: 8ec10b31a771
Create Date: 2026-11-03 18:30:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "3b2e7f4a9c10"
down_revision = "8ec10b31a771"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_verification_challenges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_email_verification_challenges_user_id",
        "email_verification_challenges",
        ["user_id"],
    )
    op.create_index(
        "uq_pending_email_verification",
        "email_verification_challenges",
        ["user_id"],
        unique=True,
        sqlite_where=sa.text("consumed_at IS NULL AND revoked_at IS NULL"),
        postgresql_where=sa.text("consumed_at IS NULL AND revoked_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_pending_email_verification", table_name="email_verification_challenges")
    op.drop_index("ix_email_verification_challenges_user_id", table_name="email_verification_challenges")
    op.drop_table("email_verification_challenges")
