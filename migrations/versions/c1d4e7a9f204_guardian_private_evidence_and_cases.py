"""Persist private evidence metadata and owner-scoped Guardian invoice cases.

Revision ID: c1d4e7a9f204
Revises: f2e9c7a4d821
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "c1d4e7a9f204"
down_revision = "f2e9c7a4d821"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guardian_evidence_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("original_filename", sa.String(160), nullable=False),
        sa.Column("media_type", sa.String(64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(sha256) = 64", name="ck_guardian_document_sha256"),
        sa.CheckConstraint("byte_size > 0 AND byte_size <= 5242880", name="ck_guardian_document_size"),
        sa.CheckConstraint("status IN ('STORED_UNSCANNED', 'CLEAN', 'REJECTED')", name="ck_guardian_document_status"),
        sa.CheckConstraint("media_type IN ('application/pdf', 'image/png', 'image/jpeg')", name="ck_guardian_document_media_type"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "owner_user_id", name="uq_guardian_document_id_owner"),
        sa.UniqueConstraint("owner_user_id", "idempotency_key", name="uq_guardian_document_idempotency"),
    )
    op.create_index("ix_guardian_documents_owner_created", "guardian_evidence_documents", ["owner_user_id", "created_at"])

    op.create_table(
        "guardian_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_document_id", sa.Uuid(), nullable=False),
        sa.Column("review_idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_sha256", sa.String(64), nullable=False),
        sa.Column("case_type", sa.String(32), nullable=False),
        sa.Column("invoice_id", sa.String(128), nullable=False),
        sa.Column("provider_key", sa.String(128), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("disposition", sa.String(24), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("invoice_snapshot", sa.JSON(), nullable=False),
        sa.Column("review_snapshot", sa.JSON(), nullable=False),
        sa.Column("action_draft", sa.String(12000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(request_sha256) = 64", name="ck_guardian_case_request_sha256"),
        sa.CheckConstraint("case_type = 'INVOICE_REVIEW'", name="ck_guardian_case_type"),
        sa.CheckConstraint("disposition IN ('CONSISTENT', 'REVIEW_REQUIRED', 'ABSTAIN')", name="ck_guardian_case_disposition"),
        sa.CheckConstraint("status IN ('REVIEWED', 'DRAFT_READY', 'APPROVED_FOR_USER_TO_SEND', 'REJECTED', 'CLOSED')", name="ck_guardian_case_status"),
        sa.CheckConstraint("length(currency) = 3", name="ck_guardian_case_currency"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["evidence_document_id", "owner_user_id"],
            ["guardian_evidence_documents.id", "guardian_evidence_documents.owner_user_id"],
            ondelete="RESTRICT", name="fk_guardian_case_evidence_owner",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "owner_user_id", name="uq_guardian_case_id_owner"),
        sa.UniqueConstraint("owner_user_id", "review_idempotency_key", name="uq_guardian_review_idempotency"),
    )
    op.create_index("ix_guardian_cases_owner_created", "guardian_cases", ["owner_user_id", "created_at"])
    op.create_index("ix_guardian_cases_owner_provider", "guardian_cases", ["owner_user_id", "provider_key", "issue_date"])


def downgrade() -> None:
    op.drop_index("ix_guardian_cases_owner_provider", table_name="guardian_cases")
    op.drop_index("ix_guardian_cases_owner_created", table_name="guardian_cases")
    op.drop_table("guardian_cases")
    op.drop_index("ix_guardian_documents_owner_created", table_name="guardian_evidence_documents")
    op.drop_table("guardian_evidence_documents")
