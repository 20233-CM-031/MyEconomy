"""Add owner-scoped financial accounts, imports, transactions and obligations.

Revision ID: f2e9c7a4d821
Revises: 3b2e7f4a9c10
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "f2e9c7a4d821"
down_revision = "3b2e7f4a9c10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "financial_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("account_name", sa.String(100), nullable=False),
        sa.Column("account_type", sa.String(32), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("institution_label", sa.String(120), nullable=True),
        sa.Column("masked_reference", sa.String(64), nullable=True),
        sa.Column("opening_balance_minor", sa.BigInteger(), nullable=False),
        sa.Column("opening_balance_as_of", sa.Date(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_external_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(currency) = 3", name="ck_financial_account_currency"),
        sa.CheckConstraint("account_type IN ('BANK_DEPOSIT', 'CREDIT_CARD', 'UPI_WALLET', 'CASH', 'INVESTMENT', 'OTHER')", name="ck_financial_account_type"),
        sa.CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'CLOSED')", name="ck_financial_account_status"),
        sa.CheckConstraint("source_type IN ('MANUAL', 'CSV_IMPORT', 'AUTHORIZED_PROVIDER', 'SYNTHETIC_FIXTURE')", name="ck_financial_account_source_type"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "owner_user_id", name="uq_financial_accounts_id_owner"),
        sa.UniqueConstraint("id", "owner_user_id", "currency", name="uq_financial_accounts_scope_currency"),
        sa.UniqueConstraint("owner_user_id", "source_type", "source_external_id", name="uq_financial_account_source"),
    )
    op.create_index("ix_financial_accounts_owner_created", "financial_accounts", ["owner_user_id", "created_at"])

    op.create_table(
        "transaction_import_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("source_filename", sa.String(160), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("inserted_count", sa.Integer(), nullable=False),
        sa.Column("updated_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("potential_duplicate_count", sa.Integer(), nullable=False),
        sa.Column("validation_errors", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('COMPLETED', 'PARTIAL', 'REJECTED')", name="ck_import_status"),
        sa.CheckConstraint("length(source_sha256) = 64", name="ck_import_sha256_length"),
        sa.CheckConstraint("row_count >= 0 AND inserted_count >= 0 AND updated_count >= 0 AND duplicate_count >= 0", name="ck_import_counts_nonnegative"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id", "owner_user_id"], ["financial_accounts.id", "financial_accounts.owner_user_id"], ondelete="CASCADE", name="fk_import_account_owner"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_user_id", "idempotency_key", name="uq_import_owner_idempotency"),
        sa.UniqueConstraint("id", "account_id", "owner_user_id", name="uq_import_batch_composite"),
    )
    op.create_index("ix_import_batches_owner_created", "transaction_import_batches", ["owner_user_id", "created_at"])

    op.create_table(
        "financial_transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("import_batch_id", sa.Uuid(), nullable=True),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
        sa.Column("cashflow_treatment", sa.String(16), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("description", sa.String(256), nullable=False),
        sa.Column("counterparty_label", sa.String(128), nullable=True),
        sa.Column("external_reference", sa.String(128), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("essential", sa.Boolean(), nullable=False),
        sa.Column("fingerprint_sha256", sa.String(64), nullable=False),
        sa.Column("potential_duplicate_of_id", sa.Uuid(), nullable=True),
        sa.Column("source_row_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_minor > 0", name="ck_transaction_amount_positive"),
        sa.CheckConstraint("length(currency) = 3", name="ck_transaction_currency"),
        sa.CheckConstraint("direction IN ('CREDIT', 'DEBIT')", name="ck_transaction_direction"),
        sa.CheckConstraint("cashflow_treatment IN ('INCOME', 'EXPENSE', 'REFUND', 'TRANSFER', 'IGNORE')", name="ck_transaction_treatment"),
        sa.CheckConstraint("status IN ('POSTED', 'PENDING', 'REVERSED', 'VOID')", name="ck_transaction_status"),
        sa.CheckConstraint("(cashflow_treatment != 'INCOME' OR direction = 'CREDIT') AND (cashflow_treatment != 'EXPENSE' OR direction = 'DEBIT') AND (cashflow_treatment != 'REFUND' OR direction = 'CREDIT')", name="ck_transaction_direction_treatment"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id", "owner_user_id", "currency"], ["financial_accounts.id", "financial_accounts.owner_user_id", "financial_accounts.currency"], ondelete="CASCADE", name="fk_transaction_account_owner_currency"),
        sa.ForeignKeyConstraint(["import_batch_id", "account_id", "owner_user_id"], ["transaction_import_batches.id", "transaction_import_batches.account_id", "transaction_import_batches.owner_user_id"], ondelete="RESTRICT", name="fk_transaction_import_batch_scope"),
        sa.ForeignKeyConstraint(["potential_duplicate_of_id", "owner_user_id", "account_id", "currency"], ["financial_transactions.id", "financial_transactions.owner_user_id", "financial_transactions.account_id", "financial_transactions.currency"], ondelete="RESTRICT", name="fk_transaction_potential_duplicate_owner"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "owner_user_id", name="uq_financial_transactions_id_owner"),
        sa.UniqueConstraint("id", "owner_user_id", "account_id", name="uq_financial_transactions_scope"),
        sa.UniqueConstraint("id", "owner_user_id", "account_id", "currency", name="uq_financial_transactions_scope_currency"),
    )
    op.create_index("ix_financial_transactions_owner_date", "financial_transactions", ["owner_user_id", "occurred_on"])
    op.create_index("ix_financial_transactions_account_date", "financial_transactions", ["account_id", "occurred_on"])
    op.create_index("ix_financial_transactions_fingerprint", "financial_transactions", ["owner_user_id", "account_id", "fingerprint_sha256"])
    op.create_index("uq_transaction_external_reference", "financial_transactions", ["owner_user_id", "account_id", "external_reference"], unique=True, sqlite_where=sa.text("external_reference IS NOT NULL"), postgresql_where=sa.text("external_reference IS NOT NULL"))

    # Defense in depth: financial facts cannot be edited after import. Only a
    # previously absent posted_at may be enriched and provider lifecycle status
    # may follow the monotonic transition graph.
    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        op.execute(
            "CREATE TRIGGER financial_transaction_update_guard "
            "BEFORE UPDATE ON financial_transactions "
            "WHEN OLD.id IS NOT NEW.id OR OLD.owner_user_id IS NOT NEW.owner_user_id OR "
            "OLD.account_id IS NOT NEW.account_id OR OLD.import_batch_id IS NOT NEW.import_batch_id OR "
            "OLD.occurred_on IS NOT NEW.occurred_on OR OLD.amount_minor IS NOT NEW.amount_minor OR "
            "OLD.currency IS NOT NEW.currency OR OLD.direction IS NOT NEW.direction OR "
            "OLD.cashflow_treatment IS NOT NEW.cashflow_treatment OR OLD.category IS NOT NEW.category OR "
            "OLD.description IS NOT NEW.description OR OLD.counterparty_label IS NOT NEW.counterparty_label OR "
            "OLD.external_reference IS NOT NEW.external_reference OR OLD.essential IS NOT NEW.essential OR "
            "OLD.fingerprint_sha256 IS NOT NEW.fingerprint_sha256 OR "
            "OLD.potential_duplicate_of_id IS NOT NEW.potential_duplicate_of_id OR "
            "OLD.source_row_number IS NOT NEW.source_row_number OR OLD.created_at IS NOT NEW.created_at OR "
            "(OLD.posted_at IS NOT NULL AND OLD.posted_at IS NOT NEW.posted_at) OR "
            "NOT (OLD.status = NEW.status OR "
            "(OLD.status = 'PENDING' AND NEW.status IN ('POSTED', 'REVERSED', 'VOID')) OR "
            "(OLD.status = 'POSTED' AND NEW.status IN ('REVERSED', 'VOID'))) "
            "BEGIN SELECT RAISE(ABORT, 'financial transaction facts are immutable or status transition is invalid'); END;"
        )
    elif dialect == "postgresql":
        op.execute(
            "CREATE FUNCTION enforce_financial_transaction_update() RETURNS trigger "
            "LANGUAGE plpgsql AS $$ BEGIN "
            "IF OLD.id IS DISTINCT FROM NEW.id OR OLD.owner_user_id IS DISTINCT FROM NEW.owner_user_id OR "
            "OLD.account_id IS DISTINCT FROM NEW.account_id OR OLD.import_batch_id IS DISTINCT FROM NEW.import_batch_id OR "
            "OLD.occurred_on IS DISTINCT FROM NEW.occurred_on OR OLD.amount_minor IS DISTINCT FROM NEW.amount_minor OR "
            "OLD.currency IS DISTINCT FROM NEW.currency OR OLD.direction IS DISTINCT FROM NEW.direction OR "
            "OLD.cashflow_treatment IS DISTINCT FROM NEW.cashflow_treatment OR OLD.category IS DISTINCT FROM NEW.category OR "
            "OLD.description IS DISTINCT FROM NEW.description OR OLD.counterparty_label IS DISTINCT FROM NEW.counterparty_label OR "
            "OLD.external_reference IS DISTINCT FROM NEW.external_reference OR OLD.essential IS DISTINCT FROM NEW.essential OR "
            "OLD.fingerprint_sha256 IS DISTINCT FROM NEW.fingerprint_sha256 OR "
            "OLD.potential_duplicate_of_id IS DISTINCT FROM NEW.potential_duplicate_of_id OR "
            "OLD.source_row_number IS DISTINCT FROM NEW.source_row_number OR OLD.created_at IS DISTINCT FROM NEW.created_at OR "
            "(OLD.posted_at IS NOT NULL AND OLD.posted_at IS DISTINCT FROM NEW.posted_at) THEN "
            "RAISE EXCEPTION 'financial transaction facts are immutable'; END IF; "
            "IF OLD.status = NEW.status OR "
            "(OLD.status = 'PENDING' AND NEW.status IN ('POSTED', 'REVERSED', 'VOID')) OR "
            "(OLD.status = 'POSTED' AND NEW.status IN ('REVERSED', 'VOID')) THEN RETURN NEW; END IF; "
            "RAISE EXCEPTION 'invalid financial transaction status transition: % -> %', OLD.status, NEW.status; "
            "END; $$"
        )
        op.execute(
            "CREATE TRIGGER financial_transaction_update_guard BEFORE UPDATE ON financial_transactions "
            "FOR EACH ROW EXECUTE FUNCTION enforce_financial_transaction_update()"
        )

    op.create_table(
        "recurring_obligations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=True),
        sa.Column("payee_label", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("frequency", sa.String(16), nullable=False),
        sa.Column("due_day", sa.Integer(), nullable=True),
        sa.Column("first_due_date", sa.Date(), nullable=False),
        sa.Column("next_due_date", sa.Date(), nullable=False),
        sa.Column("autopay_enabled", sa.Boolean(), nullable=False),
        sa.Column("essential", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_external_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_minor > 0", name="ck_obligation_amount_positive"),
        sa.CheckConstraint("length(currency) = 3", name="ck_obligation_currency"),
        sa.CheckConstraint("frequency IN ('WEEKLY', 'FORTNIGHTLY', 'MONTHLY', 'QUARTERLY', 'YEARLY')", name="ck_obligation_frequency"),
        sa.CheckConstraint("due_day IS NULL OR (due_day BETWEEN 1 AND 31)", name="ck_obligation_due_day"),
        sa.CheckConstraint("status IN ('ACTIVE', 'PAUSED', 'CANCELLED', 'COMPLETED')", name="ck_obligation_status"),
        sa.CheckConstraint("next_due_date >= first_due_date", name="ck_obligation_due_date_order"),
        sa.CheckConstraint("source_type IN ('MANUAL', 'CSV_IMPORT', 'AUTHORIZED_PROVIDER', 'SYNTHETIC_FIXTURE')", name="ck_obligation_source_type"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id", "owner_user_id", "currency"], ["financial_accounts.id", "financial_accounts.owner_user_id", "financial_accounts.currency"], ondelete="RESTRICT", name="fk_obligation_account_owner_currency"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_user_id", "source_type", "source_external_id", name="uq_obligation_owner_source"),
    )
    op.create_index("ix_obligations_owner_due", "recurring_obligations", ["owner_user_id", "next_due_date"])


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS financial_transaction_update_guard")
    elif dialect == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS financial_transaction_update_guard ON financial_transactions")
        op.execute("DROP FUNCTION IF EXISTS enforce_financial_transaction_update()")
    op.drop_index("ix_obligations_owner_due", table_name="recurring_obligations")
    op.drop_table("recurring_obligations")
    op.drop_index("uq_transaction_external_reference", table_name="financial_transactions")
    op.drop_index("ix_financial_transactions_fingerprint", table_name="financial_transactions")
    op.drop_index("ix_financial_transactions_account_date", table_name="financial_transactions")
    op.drop_index("ix_financial_transactions_owner_date", table_name="financial_transactions")
    op.drop_table("financial_transactions")
    op.drop_index("ix_import_batches_owner_created", table_name="transaction_import_batches")
    op.drop_table("transaction_import_batches")
    op.drop_index("ix_financial_accounts_owner_created", table_name="financial_accounts")
    op.drop_table("financial_accounts")
