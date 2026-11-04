from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from myeconomy.infrastructure.database import get_db
from myeconomy.infrastructure.models import Base
from myeconomy.main import app


@pytest.fixture
def test_environment(
    monkeypatch,
    tmp_path: Path,
) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
        )
        connection.exec_driver_sql(
            "INSERT INTO alembic_version (version_num) VALUES ('c1d4e7a9f204')"
        )
        connection.exec_driver_sql(
            "CREATE TRIGGER audit_events_no_update BEFORE UPDATE ON audit_events "
            "BEGIN SELECT RAISE(ABORT, 'audit_events are immutable'); END;"
        )
        connection.exec_driver_sql(
            "CREATE TRIGGER audit_events_no_delete BEFORE DELETE ON audit_events "
            "BEGIN SELECT RAISE(ABORT, 'audit_events are immutable'); END;"
        )
        connection.exec_driver_sql(
            "CREATE TRIGGER financial_transaction_update_guard "
            "BEFORE UPDATE ON financial_transactions "
            "WHEN OLD.id IS NOT NEW.id OR OLD.owner_user_id IS NOT NEW.owner_user_id OR "
            "OLD.account_id IS NOT NEW.account_id OR "
            "OLD.import_batch_id IS NOT NEW.import_batch_id OR "
            "OLD.occurred_on IS NOT NEW.occurred_on OR "
            "OLD.amount_minor IS NOT NEW.amount_minor OR "
            "OLD.currency IS NOT NEW.currency OR OLD.direction IS NOT NEW.direction OR "
            "OLD.cashflow_treatment IS NOT NEW.cashflow_treatment OR "
            "OLD.category IS NOT NEW.category OR "
            "OLD.description IS NOT NEW.description OR "
            "OLD.counterparty_label IS NOT NEW.counterparty_label OR "
            "OLD.external_reference IS NOT NEW.external_reference OR "
            "OLD.essential IS NOT NEW.essential OR "
            "OLD.fingerprint_sha256 IS NOT NEW.fingerprint_sha256 OR "
            "OLD.potential_duplicate_of_id IS NOT NEW.potential_duplicate_of_id OR "
            "OLD.source_row_number IS NOT NEW.source_row_number OR "
            "OLD.created_at IS NOT NEW.created_at OR "
            "(OLD.posted_at IS NOT NULL AND OLD.posted_at IS NOT NEW.posted_at) OR "
            "NOT (OLD.status = NEW.status OR "
            "(OLD.status = 'PENDING' AND NEW.status IN ('POSTED', 'REVERSED', 'VOID')) OR "
            "(OLD.status = 'POSTED' AND NEW.status IN ('REVERSED', 'VOID'))) "
            "BEGIN SELECT RAISE(ABORT, "
            "'financial transaction facts are immutable or status transition is invalid'); END;"
        )

    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    verification_tokens: dict[str, str] = {}
    app.state.verification_tokens = verification_tokens

    def capture_verification_email(*, recipient: str, token: str) -> None:
        verification_tokens[recipient] = token

    monkeypatch.setattr(
        "myeconomy.api.identity_routes.send_verification_email", capture_verification_email
    )
    app.dependency_overrides[get_db] = override_get_db
    from myeconomy.api import guardian_routes
    from myeconomy.infrastructure.document_storage import LocalPrivateDocumentStore

    monkeypatch.setattr(
        guardian_routes, "DOCUMENT_STORE", LocalPrivateDocumentStore(tmp_path / "private-documents")
    )
    try:
        with TestClient(app) as client:
            yield client, session_factory
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
