from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, MetaData, Table, Uuid, create_engine, event, insert, text
from sqlalchemy.exc import IntegrityError

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "e89a4c72b6d1_personal_casebook.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location("personal_casebook_migration", MIGRATION_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sqlite_migration_guards_case_source_transitions_and_event_history():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    metadata = MetaData()
    users = Table("users", metadata, Column("id", Uuid(as_uuid=True), primary_key=True))
    with engine.begin() as connection:
        metadata.create_all(connection)
        migration = load_migration()
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()

        owner_id, outsider_id, case_id, event_id = uuid4(), uuid4(), uuid4(), uuid4()
        connection.execute(insert(users), [{"id": owner_id}, {"id": outsider_id}])
        now = datetime.now(UTC)
        snapshot = {"finding_id": "DATA-001", "amount": None}
        connection.execute(
            text(
                "INSERT INTO personal_cases (id, owner_user_id, source_engine, source_finding_id, "
                "idempotency_key, request_sha256, period_start, period_end, as_of, currency, "
                "amount_minor, title, source_snapshot, status, state_version, "
                "created_at, updated_at) "
                "VALUES (:id, :owner, 'PERSONAL', 'DATA-001', 'open-key', :hash, "
                "'2026-10-01', '2026-10-31', '2026-11-04', 'INR', NULL, "
                "'A data gap', :snapshot, 'OPEN', 1, :now, :now)"
            ),
            {
                "id": case_id.hex,
                "owner": owner_id.hex,
                "hash": "a" * 64,
                "snapshot": json.dumps(snapshot),
                "now": now.isoformat(),
            },
        )
        connection.execute(
            text(
                "INSERT INTO personal_case_events (id, case_id, actor_user_id, event_sequence, "
                "event_type, from_status, to_status, note, idempotency_key, "
                "request_sha256, created_at) "
                "VALUES (:id, :case_id, :actor, 1, 'CASE_OPENED', NULL, 'OPEN', "
                "'Opened', 'open-event', :hash, :now)"
            ),
            {
                "id": event_id.hex,
                "case_id": case_id.hex,
                "actor": owner_id.hex,
                "hash": "b" * 64,
                "now": now.isoformat(),
            },
        )

        # One legal transition increments the version exactly once.
        connection.execute(
            text("UPDATE personal_cases SET status='IN_REVIEW', state_version=2 WHERE id=:id"),
            {"id": case_id.hex},
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                text("UPDATE personal_cases SET status='RESOLVED', state_version=3 WHERE id=:id"),
                {"id": case_id.hex},
            )
        with pytest.raises(IntegrityError):
            connection.execute(
                text("UPDATE personal_cases SET source_snapshot=:snap WHERE id=:id"),
                {"id": case_id.hex, "snap": json.dumps({"finding_id": "forged"})},
            )
        with pytest.raises(IntegrityError):
            connection.execute(
                text("UPDATE personal_case_events SET note='edited' WHERE id=:id"),
                {"id": event_id.hex},
            )
        invalid_event_values = {
            "id": uuid4().hex,
            "case_id": case_id.hex,
            "actor": owner_id.hex,
            "hash": "c" * 64,
            "now": now.isoformat(),
        }
        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO personal_case_events (id, case_id, actor_user_id, event_sequence, "
                    "event_type, from_status, to_status, note, idempotency_key, "
                    "request_sha256, created_at) "
                    "VALUES (:id, :case_id, :actor, 2, 'STATUS_CHANGED', 'OPEN', "
                    "'CLOSED', 'wrong state', 'bad-state', :hash, :now)"
                ),
                invalid_event_values,
            )

        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO personal_case_events (id, case_id, actor_user_id, event_sequence, "
                    "event_type, from_status, to_status, note, idempotency_key, "
                    "request_sha256, created_at) "
                    "VALUES (:id, :case_id, :actor, 2, 'STATUS_CHANGED', 'OPEN', "
                    "'IN_REVIEW', 'bad owner', 'bad-owner', :hash, :now)"
                ),
                {**invalid_event_values, "id": uuid4().hex, "actor": outsider_id.hex},
            )

        # The case itself cannot be deleted to cascade away its append-only timeline.
        with pytest.raises(IntegrityError):
            connection.execute(text("DELETE FROM personal_cases WHERE id=:id"), {"id": case_id.hex})

        valid_event_id = uuid4().hex
        connection.execute(
            text(
                "INSERT INTO personal_case_events (id, case_id, actor_user_id, event_sequence, "
                "event_type, from_status, to_status, note, idempotency_key, "
                "request_sha256, created_at) "
                "VALUES (:id, :case_id, :actor, 2, 'STATUS_CHANGED', 'OPEN', "
                "'IN_REVIEW', 'Valid transition', 'valid-transition', :hash, :now)"
            ),
            {**invalid_event_values, "id": valid_event_id},
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                text("DELETE FROM personal_case_events WHERE id=:id"), {"id": valid_event_id}
            )
    engine.dispose()


def test_sqlite_migration_downgrade_removes_casebook_tables_and_triggers():
    from sqlalchemy import inspect

    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata = MetaData()
    Table("users", metadata, Column("id", Uuid(as_uuid=True), primary_key=True))
    with engine.begin() as connection:
        metadata.create_all(connection)
        migration = load_migration()
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            migration.downgrade()
        inspector = inspect(connection)
        assert "personal_cases" not in inspector.get_table_names()
        assert "personal_case_events" not in inspector.get_table_names()
        triggers = (
            connection.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='trigger' "
                    "AND name LIKE 'personal_case%'"
                )
            )
            .scalars()
            .all()
        )
        assert triggers == []
    engine.dispose()
