"""Persistence models. Public behavior is defined by application/domain services."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    event,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (Index("ix_auth_sessions_user_id", "user_id"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EmailVerificationChallenge(Base):
    __tablename__ = "email_verification_challenges"
    __table_args__ = (
        Index("ix_email_verification_challenges_user_id", "user_id"),
        Index(
            "uq_pending_email_verification",
            "user_id",
            unique=True,
            sqlite_where=text("consumed_at IS NULL AND revoked_at IS NULL"),
            postgresql_where=text("consumed_at IS NULL AND revoked_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Household(Base):
    __tablename__ = "households"
    __table_args__ = (Index("ix_households_created_by_user_id", "created_by_user_id"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class HouseholdMembership(Base):
    __tablename__ = "household_memberships"
    __table_args__ = (
        UniqueConstraint("household_id", "user_id", name="uq_household_membership"),
        CheckConstraint("role IN ('owner', 'admin', 'member')", name="ck_household_role"),
        Index("ix_household_memberships_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    household_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class HouseholdInvitation(Base):
    __tablename__ = "household_invitations"
    __table_args__ = (
        Index("ix_household_invitations_household_id", "household_id"),
        Index("ix_household_invitations_invited_email", "invited_email"),
        Index("ix_household_invitations_token_hash", "token_hash", unique=True),
        Index(
            "uq_pending_household_invitation",
            "household_id",
            "invited_email",
            unique=True,
            sqlite_where=text("accepted_at IS NULL AND revoked_at IS NULL"),
            postgresql_where=text("accepted_at IS NULL AND revoked_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    household_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False
    )
    invited_email: Mapped[str] = mapped_column(String(320), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    invited_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsentGrant(Base):
    __tablename__ = "consent_grants"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'revoked')", name="ck_consent_status"),
        CheckConstraint(
            "recipient_type IN ('service', 'household', 'partner', 'research')",
            name="ck_consent_recipient_type",
        ),
        CheckConstraint(
            "purpose IN ('household_sharing', 'commons_aggregation', 'opportunity_matching', "
            "'benefits_discovery', 'partner_offer_personalization', 'research_participation', "
            "'support_case_processing', 'economic_defence', 'enterprise_assistance', "
            "'ai_assistance')",
            name="ck_consent_purpose",
        ),
        Index("ix_consent_grants_subject_user_id", "subject_user_id"),
        Index(
            "ix_consent_grants_lookup",
            "subject_user_id",
            "purpose",
            "recipient_type",
            "recipient_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    subject_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    data_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    recipient_type: Mapped[str] = mapped_column(String(16), nullable=False)
    recipient_id: Mapped[str] = mapped_column(String(128), nullable=False)
    terms_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_actor_user_id", "actor_user_id"),
        Index("ix_audit_events_subject", "subject_type", "subject_id"),
        Index("ix_audit_events_occurred_at", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    # UUID references are intentionally non-FK pseudonymous references. This
    # permits future account/household erasure without mutating immutable audit rows.
    actor_user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    household_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(96), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


def _audit_events_are_immutable(_mapper: object, _connection: object, _target: object) -> None:
    raise RuntimeError("Audit events are append-only and cannot be modified or deleted.")


event.listen(AuditEvent, "before_update", _audit_events_are_immutable)
event.listen(AuditEvent, "before_delete", _audit_events_are_immutable)


class FinancialAccount(Base):
    """User-owned account metadata; never a credential or live bank connection."""

    __tablename__ = "financial_accounts"
    __table_args__ = (
        UniqueConstraint("id", "owner_user_id", name="uq_financial_accounts_id_owner"),
        UniqueConstraint(
            "id", "owner_user_id", "currency", name="uq_financial_accounts_scope_currency"
        ),
        UniqueConstraint(
            "owner_user_id", "source_type", "source_external_id", name="uq_financial_account_source"
        ),
        CheckConstraint("length(currency) = 3", name="ck_financial_account_currency"),
        CheckConstraint(
            "account_type IN ("
            "'BANK_DEPOSIT', 'CREDIT_CARD', 'UPI_WALLET', 'CASH', 'INVESTMENT', 'OTHER'"
            ")",
            name="ck_financial_account_type",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'CLOSED')", name="ck_financial_account_status"
        ),
        CheckConstraint(
            "source_type IN ('MANUAL', 'CSV_IMPORT', 'AUTHORIZED_PROVIDER', 'SYNTHETIC_FIXTURE')",
            name="ck_financial_account_source_type",
        ),
        Index("ix_financial_accounts_owner_created", "owner_user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    institution_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    masked_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    opening_balance_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    opening_balance_as_of: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="MANUAL")
    source_external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class TransactionImportBatch(Base):
    """Immutable provenance and idempotency envelope for one submitted statement."""

    __tablename__ = "transaction_import_batches"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "idempotency_key", name="uq_import_owner_idempotency"),
        UniqueConstraint("id", "account_id", "owner_user_id", name="uq_import_batch_composite"),
        ForeignKeyConstraint(
            ["account_id", "owner_user_id"],
            ["financial_accounts.id", "financial_accounts.owner_user_id"],
            ondelete="CASCADE",
            name="fk_import_account_owner",
        ),
        CheckConstraint("status IN ('COMPLETED', 'PARTIAL', 'REJECTED')", name="ck_import_status"),
        CheckConstraint("length(source_sha256) = 64", name="ck_import_sha256_length"),
        CheckConstraint(
            "row_count >= 0 AND inserted_count >= 0 AND duplicate_count >= 0",
            name="ck_import_counts_nonnegative",
        ),
        Index("ix_import_batches_owner_created", "owner_user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_filename: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="CSV_IMPORT")
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inserted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    potential_duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validation_errors: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FinancialTransaction(Base):
    """Normalized immutable-posting record; corrections use reversal/new records."""

    __tablename__ = "financial_transactions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "owner_user_id", "currency"],
            [
                "financial_accounts.id",
                "financial_accounts.owner_user_id",
                "financial_accounts.currency",
            ],
            ondelete="CASCADE",
            name="fk_transaction_account_owner_currency",
        ),
        ForeignKeyConstraint(
            ["import_batch_id", "account_id", "owner_user_id"],
            [
                "transaction_import_batches.id",
                "transaction_import_batches.account_id",
                "transaction_import_batches.owner_user_id",
            ],
            ondelete="RESTRICT",
            name="fk_transaction_import_batch_scope",
        ),
        ForeignKeyConstraint(
            ["potential_duplicate_of_id", "owner_user_id", "account_id", "currency"],
            [
                "financial_transactions.id",
                "financial_transactions.owner_user_id",
                "financial_transactions.account_id",
                "financial_transactions.currency",
            ],
            ondelete="RESTRICT",
            name="fk_transaction_potential_duplicate_owner",
        ),
        UniqueConstraint("id", "owner_user_id", name="uq_financial_transactions_id_owner"),
        UniqueConstraint(
            "id", "owner_user_id", "account_id", name="uq_financial_transactions_scope"
        ),
        UniqueConstraint(
            "id",
            "owner_user_id",
            "account_id",
            "currency",
            name="uq_financial_transactions_scope_currency",
        ),
        CheckConstraint("amount_minor > 0", name="ck_transaction_amount_positive"),
        CheckConstraint("length(currency) = 3", name="ck_transaction_currency"),
        CheckConstraint("direction IN ('CREDIT', 'DEBIT')", name="ck_transaction_direction"),
        CheckConstraint(
            "cashflow_treatment IN ('INCOME', 'EXPENSE', 'REFUND', 'TRANSFER', 'IGNORE')",
            name="ck_transaction_treatment",
        ),
        CheckConstraint(
            "status IN ('POSTED', 'PENDING', 'REVERSED', 'VOID')", name="ck_transaction_status"
        ),
        CheckConstraint(
            "(cashflow_treatment != 'INCOME' OR direction = 'CREDIT') AND "
            "(cashflow_treatment != 'EXPENSE' OR direction = 'DEBIT') AND "
            "(cashflow_treatment != 'REFUND' OR direction = 'CREDIT')",
            name="ck_transaction_direction_treatment",
        ),
        Index("ix_financial_transactions_owner_date", "owner_user_id", "occurred_on"),
        Index("ix_financial_transactions_account_date", "account_id", "occurred_on"),
        Index(
            "ix_financial_transactions_fingerprint",
            "owner_user_id",
            "account_id",
            "fingerprint_sha256",
        ),
        Index(
            "uq_transaction_external_reference",
            "owner_user_id",
            "account_id",
            "external_reference",
            unique=True,
            sqlite_where=text("external_reference IS NOT NULL"),
            postgresql_where=text("external_reference IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    import_batch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    cashflow_treatment: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    counterparty_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="POSTED")
    essential: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fingerprint_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    potential_duplicate_of_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    source_row_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RecurringObligation(Base):
    """Expected obligation schedule; not itself a posted payment or transaction."""

    __tablename__ = "recurring_obligations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "owner_user_id", "currency"],
            [
                "financial_accounts.id",
                "financial_accounts.owner_user_id",
                "financial_accounts.currency",
            ],
            ondelete="RESTRICT",
            name="fk_obligation_account_owner_currency",
        ),
        UniqueConstraint(
            "owner_user_id", "source_type", "source_external_id", name="uq_obligation_owner_source"
        ),
        CheckConstraint("amount_minor > 0", name="ck_obligation_amount_positive"),
        CheckConstraint("length(currency) = 3", name="ck_obligation_currency"),
        CheckConstraint(
            "frequency IN ('WEEKLY', 'FORTNIGHTLY', 'MONTHLY', 'QUARTERLY', 'YEARLY')",
            name="ck_obligation_frequency",
        ),
        CheckConstraint(
            "due_day IS NULL OR (due_day BETWEEN 1 AND 31)", name="ck_obligation_due_day"
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'PAUSED', 'CANCELLED', 'COMPLETED')", name="ck_obligation_status"
        ),
        CheckConstraint("next_due_date >= first_due_date", name="ck_obligation_due_date_order"),
        CheckConstraint(
            "source_type IN ('MANUAL', 'CSV_IMPORT', 'AUTHORIZED_PROVIDER', 'SYNTHETIC_FIXTURE')",
            name="ck_obligation_source_type",
        ),
        Index("ix_obligations_owner_due", "owner_user_id", "next_due_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    payee_label: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False)
    due_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    autopay_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    essential: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="MANUAL")
    source_external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class GuardianEvidenceDocument(Base):
    """Owner-scoped evidence metadata; bytes live in a private storage adapter."""

    __tablename__ = "guardian_evidence_documents"
    __table_args__ = (
        UniqueConstraint("id", "owner_user_id", name="uq_guardian_document_id_owner"),
        UniqueConstraint(
            "owner_user_id", "idempotency_key", name="uq_guardian_document_idempotency"
        ),
        CheckConstraint("length(sha256) = 64", name="ck_guardian_document_sha256"),
        CheckConstraint("byte_size > 0 AND byte_size <= 5242880", name="ck_guardian_document_size"),
        CheckConstraint(
            "status IN ('STORED_UNSCANNED', 'CLEAN', 'REJECTED')",
            name="ck_guardian_document_status",
        ),
        CheckConstraint(
            "media_type IN ('application/pdf', 'image/png', 'image/jpeg')",
            name="ck_guardian_document_media_type",
        ),
        Index("ix_guardian_documents_owner_created", "owner_user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(160), nullable=False)
    media_type: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="STORED_UNSCANNED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class GuardianCase(Base):
    """Persisted invoice-review case and its human-readable, evidence-linked result."""

    __tablename__ = "guardian_cases"
    __table_args__ = (
        UniqueConstraint("id", "owner_user_id", name="uq_guardian_case_id_owner"),
        UniqueConstraint(
            "owner_user_id", "review_idempotency_key", name="uq_guardian_review_idempotency"
        ),
        ForeignKeyConstraint(
            ["evidence_document_id", "owner_user_id"],
            ["guardian_evidence_documents.id", "guardian_evidence_documents.owner_user_id"],
            ondelete="RESTRICT",
            name="fk_guardian_case_evidence_owner",
        ),
        CheckConstraint("case_type = 'INVOICE_REVIEW'", name="ck_guardian_case_type"),
        CheckConstraint(
            "disposition IN ('CONSISTENT', 'REVIEW_REQUIRED', 'ABSTAIN')",
            name="ck_guardian_case_disposition",
        ),
        CheckConstraint(
            "status IN ("
            "'REVIEWED', 'DRAFT_READY', 'APPROVED_FOR_USER_TO_SEND', 'REJECTED', 'CLOSED'"
            ")",
            name="ck_guardian_case_status",
        ),
        CheckConstraint("length(currency) = 3", name="ck_guardian_case_currency"),
        Index("ix_guardian_cases_owner_created", "owner_user_id", "created_at"),
        Index("ix_guardian_cases_owner_provider", "owner_user_id", "provider_key", "issue_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    evidence_document_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    review_idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    case_type: Mapped[str] = mapped_column(String(32), nullable=False, default="INVOICE_REVIEW")
    invoice_id: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_key: Mapped[str] = mapped_column(String(128), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    disposition: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="REVIEWED")
    invoice_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    review_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    action_draft: Mapped[str | None] = mapped_column(String(12000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
