"""Persist personal economic cases and append-only lifecycle events.

Revision ID: e89a4c72b6d1
Revises: 7a05f3c2d9b1
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "e89a4c72b6d1"
down_revision = "7a05f3c2d9b1"
branch_labels = None
depends_on = None


_CASE_STATUSES = (
    "'OPEN', 'IN_REVIEW', 'ACTION_READY', 'WAITING_FOR_USER', "
    "'WAITING_EXTERNAL', 'RESOLVED', 'CLOSED'"
)


def upgrade() -> None:
    op.create_table(
        "personal_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("source_engine", sa.String(length=32), nullable=False),
        sa.Column("source_finding_id", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("source_snapshot", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("state_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("source_engine = 'PERSONAL'", name="ck_personal_case_source_engine"),
        sa.CheckConstraint(f"status IN ({_CASE_STATUSES})", name="ck_personal_case_status"),
        sa.CheckConstraint("length(currency) = 3", name="ck_personal_case_currency"),
        sa.CheckConstraint("length(request_sha256) = 64", name="ck_personal_case_request_hash"),
        sa.CheckConstraint("state_version >= 1", name="ck_personal_case_version"),
        sa.CheckConstraint(
            "period_end >= period_start AND as_of >= period_end",
            name="ck_personal_case_period",
        ),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "owner_user_id", name="uq_personal_case_id_owner"),
        sa.UniqueConstraint(
            "owner_user_id", "idempotency_key", name="uq_personal_case_owner_idempotency"
        ),
        sa.UniqueConstraint(
            "owner_user_id", "source_engine", "source_finding_id", "period_start",
            "period_end", "as_of", "currency", name="uq_personal_case_source_identity"
        ),
    )
    op.create_index(
        "ix_personal_cases_owner_updated", "personal_cases", ["owner_user_id", "updated_at"]
    )
    op.create_index(
        "ix_personal_cases_owner_status", "personal_cases", ["owner_user_id", "status"]
    )

    op.create_table(
        "personal_case_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("event_sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("from_status", sa.String(length=24), nullable=True),
        sa.Column("to_status", sa.String(length=24), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("event_sequence >= 1", name="ck_personal_case_event_sequence"),
        sa.CheckConstraint(
            "event_type IN ('CASE_OPENED', 'STATUS_CHANGED')",
            name="ck_personal_case_event_type",
        ),
        sa.CheckConstraint(
            f"to_status IN ({_CASE_STATUSES})", name="ck_personal_case_event_to_status"
        ),
        sa.CheckConstraint(
            f"from_status IS NULL OR from_status IN ({_CASE_STATUSES})",
            name="ck_personal_case_event_from_status",
        ),
        sa.CheckConstraint("length(request_sha256) = 64", name="ck_personal_case_event_hash"),
        sa.ForeignKeyConstraint(
            ["case_id", "actor_user_id"],
            ["personal_cases.id", "personal_cases.owner_user_id"],
            ondelete="CASCADE",
            name="fk_personal_case_event_actor_owner",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "event_sequence", name="uq_personal_case_event_sequence"),
        sa.UniqueConstraint(
            "case_id", "idempotency_key", name="uq_personal_case_event_idempotency"
        ),
    )
    op.create_index(
        "ix_personal_case_events_case_sequence",
        "personal_case_events",
        ["case_id", "event_sequence"],
    )

    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        op.execute(
            "CREATE TRIGGER personal_cases_update_guard BEFORE UPDATE ON personal_cases "
            "WHEN NEW.id IS NOT OLD.id OR NEW.owner_user_id IS NOT OLD.owner_user_id OR "
            "NEW.source_engine IS NOT OLD.source_engine OR "
            "NEW.source_finding_id IS NOT OLD.source_finding_id OR "
            "NEW.idempotency_key IS NOT OLD.idempotency_key OR "
            "NEW.request_sha256 IS NOT OLD.request_sha256 OR "
            "NEW.period_start IS NOT OLD.period_start OR NEW.period_end IS NOT OLD.period_end OR "
            "NEW.as_of IS NOT OLD.as_of OR NEW.currency IS NOT OLD.currency OR "
            "NEW.amount_minor IS NOT OLD.amount_minor OR NEW.title IS NOT OLD.title OR "
            "NEW.source_snapshot IS NOT OLD.source_snapshot OR "
            "NEW.created_at IS NOT OLD.created_at OR "
            "NEW.state_version != OLD.state_version + 1 OR NOT ("
            "(OLD.status = 'OPEN' AND NEW.status IN ('IN_REVIEW', 'CLOSED')) OR "
            "(OLD.status = 'IN_REVIEW' AND NEW.status IN "
            "('ACTION_READY', 'WAITING_FOR_USER', 'CLOSED')) OR "
            "(OLD.status = 'ACTION_READY' AND NEW.status IN "
            "('IN_REVIEW', 'WAITING_FOR_USER', 'WAITING_EXTERNAL', 'CLOSED')) OR "
            "(OLD.status = 'WAITING_FOR_USER' AND NEW.status IN "
            "('IN_REVIEW', 'ACTION_READY', 'CLOSED')) OR "
            "(OLD.status = 'WAITING_EXTERNAL' AND NEW.status IN "
            "('IN_REVIEW', 'RESOLVED', 'CLOSED')) OR "
            "(OLD.status = 'RESOLVED' AND NEW.status = 'CLOSED')) "
            "BEGIN SELECT RAISE(ABORT, 'personal case update violates immutable facts "
            "or transition policy'); END;"
        )
        op.execute(
            "CREATE TRIGGER personal_cases_no_delete BEFORE DELETE ON personal_cases "
            "BEGIN SELECT RAISE(ABORT, 'personal cases require an approved retention process'); END;"
        )
        op.execute(
            "CREATE TRIGGER personal_case_events_insert_guard "
            "BEFORE INSERT ON personal_case_events "
            "WHEN NOT EXISTS (SELECT 1 FROM personal_cases c WHERE c.id = NEW.case_id "
            "AND c.owner_user_id = NEW.actor_user_id AND c.state_version = NEW.event_sequence "
            "AND c.status = NEW.to_status AND ((NEW.event_sequence = 1 "
            "AND NEW.event_type = 'CASE_OPENED' AND NEW.from_status IS NULL "
            "AND NEW.to_status = 'OPEN') "
            "OR (NEW.event_sequence > 1 AND NEW.event_type = 'STATUS_CHANGED' "
            "AND NEW.from_status IS NOT NULL AND NEW.from_status != NEW.to_status "
            "AND EXISTS (SELECT 1 FROM personal_case_events prev "
            "WHERE prev.case_id = NEW.case_id "
            "AND prev.event_sequence = NEW.event_sequence - 1 "
            "AND prev.to_status = NEW.from_status)))) "
            "BEGIN SELECT RAISE(ABORT, 'personal case event does not match "
            "current case state'); END;"
        )
        op.execute(
            "CREATE TRIGGER personal_case_events_no_update BEFORE UPDATE ON personal_case_events "
            "BEGIN SELECT RAISE(ABORT, 'personal_case_events are immutable'); END;"
        )
        op.execute(
            "CREATE TRIGGER personal_case_events_no_delete BEFORE DELETE ON personal_case_events "
            "BEGIN SELECT RAISE(ABORT, 'personal_case_events are immutable'); END;"
        )
    elif dialect == "postgresql":
        op.execute(
            "CREATE FUNCTION guard_personal_case_update() RETURNS trigger AS $$ "
            "BEGIN "
            "IF ROW(NEW.id, NEW.owner_user_id, NEW.source_engine, NEW.source_finding_id, "
            "NEW.idempotency_key, NEW.request_sha256, NEW.period_start, NEW.period_end, "
            "NEW.as_of, NEW.currency, NEW.amount_minor, NEW.title, NEW.created_at) "
            "IS DISTINCT FROM ROW(OLD.id, OLD.owner_user_id, OLD.source_engine, "
            "OLD.source_finding_id, "
            "OLD.idempotency_key, OLD.request_sha256, OLD.period_start, OLD.period_end, "
            "OLD.as_of, OLD.currency, OLD.amount_minor, OLD.title, OLD.created_at) "
            "OR NEW.source_snapshot::text IS DISTINCT FROM OLD.source_snapshot::text "
            "OR NEW.state_version <> OLD.state_version + 1 THEN "
            "RAISE EXCEPTION 'personal case immutable facts or version guard failed'; END IF; "
            "IF NOT ((OLD.status = 'OPEN' AND NEW.status IN ('IN_REVIEW', 'CLOSED')) OR "
            "(OLD.status = 'IN_REVIEW' AND NEW.status IN "
            "('ACTION_READY', 'WAITING_FOR_USER', 'CLOSED')) OR "
            "(OLD.status = 'ACTION_READY' AND NEW.status IN "
            "('IN_REVIEW', 'WAITING_FOR_USER', 'WAITING_EXTERNAL', 'CLOSED')) OR "
            "(OLD.status = 'WAITING_FOR_USER' AND NEW.status IN "
            "('IN_REVIEW', 'ACTION_READY', 'CLOSED')) OR "
            "(OLD.status = 'WAITING_EXTERNAL' AND NEW.status IN "
            "('IN_REVIEW', 'RESOLVED', 'CLOSED')) OR "
            "(OLD.status = 'RESOLVED' AND NEW.status = 'CLOSED')) THEN "
            "RAISE EXCEPTION 'personal case transition is invalid'; END IF; RETURN NEW; "
            "END; $$ LANGUAGE plpgsql"
        )
        op.execute(
            "CREATE TRIGGER personal_cases_update_guard BEFORE UPDATE ON personal_cases "
            "FOR EACH ROW EXECUTE FUNCTION guard_personal_case_update()"
        )
        op.execute(
            "CREATE FUNCTION reject_personal_case_delete() RETURNS trigger AS $$ "
            "BEGIN RAISE EXCEPTION 'personal cases require an approved retention process'; "
            "END; $$ LANGUAGE plpgsql"
        )
        op.execute(
            "CREATE TRIGGER personal_cases_no_delete BEFORE DELETE ON personal_cases "
            "FOR EACH ROW EXECUTE FUNCTION reject_personal_case_delete()"
        )
        op.execute(
            "CREATE FUNCTION guard_personal_case_event_insert() RETURNS trigger AS $$ "
            "BEGIN "
            "IF NOT EXISTS (SELECT 1 FROM personal_cases c WHERE c.id = NEW.case_id "
            "AND c.owner_user_id = NEW.actor_user_id AND c.state_version = NEW.event_sequence "
            "AND c.status = NEW.to_status AND ((NEW.event_sequence = 1 "
            "AND NEW.event_type = 'CASE_OPENED' AND NEW.from_status IS NULL "
            "AND NEW.to_status = 'OPEN') "
            "OR (NEW.event_sequence > 1 AND NEW.event_type = 'STATUS_CHANGED' "
            "AND NEW.from_status IS NOT NULL AND NEW.from_status <> NEW.to_status "
            "AND EXISTS (SELECT 1 FROM personal_case_events prev "
            "WHERE prev.case_id = NEW.case_id "
            "AND prev.event_sequence = NEW.event_sequence - 1 "
            "AND prev.to_status = NEW.from_status)))) THEN "
            "RAISE EXCEPTION 'personal case event does not match current case state'; END IF; "
            "RETURN NEW; END; $$ LANGUAGE plpgsql"
        )
        op.execute(
            "CREATE TRIGGER personal_case_events_insert_guard "
            "BEFORE INSERT ON personal_case_events "
            "FOR EACH ROW EXECUTE FUNCTION guard_personal_case_event_insert()"
        )
        op.execute(
            "CREATE FUNCTION reject_personal_case_event_mutation() RETURNS trigger AS $$ "
            "BEGIN RAISE EXCEPTION 'personal_case_events are immutable'; END; $$ LANGUAGE plpgsql"
        )
        op.execute(
            "CREATE TRIGGER personal_case_events_immutable BEFORE UPDATE OR DELETE "
            "ON personal_case_events FOR EACH ROW "
            "EXECUTE FUNCTION reject_personal_case_event_mutation()"
        )


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS personal_cases_no_delete")
        op.execute("DROP TRIGGER IF EXISTS personal_cases_update_guard")
        op.execute("DROP TRIGGER IF EXISTS personal_case_events_insert_guard")
        op.execute("DROP TRIGGER IF EXISTS personal_case_events_no_update")
        op.execute("DROP TRIGGER IF EXISTS personal_case_events_no_delete")
    elif dialect == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS personal_case_events_insert_guard ON personal_case_events"
        )
        op.execute("DROP TRIGGER IF EXISTS personal_case_events_immutable ON personal_case_events")
        op.execute("DROP TRIGGER IF EXISTS personal_cases_no_delete ON personal_cases")
        op.execute("DROP TRIGGER IF EXISTS personal_cases_update_guard ON personal_cases")
        op.execute("DROP FUNCTION IF EXISTS reject_personal_case_delete() CASCADE")
        op.execute("DROP FUNCTION IF EXISTS guard_personal_case_update() CASCADE")
        op.execute("DROP FUNCTION IF EXISTS guard_personal_case_event_insert() CASCADE")
        op.execute("DROP FUNCTION IF EXISTS reject_personal_case_event_mutation() CASCADE")
    op.drop_index("ix_personal_case_events_case_sequence", table_name="personal_case_events")
    op.drop_table("personal_case_events")
    op.drop_index("ix_personal_cases_owner_status", table_name="personal_cases")
    op.drop_index("ix_personal_cases_owner_updated", table_name="personal_cases")
    op.drop_table("personal_cases")
