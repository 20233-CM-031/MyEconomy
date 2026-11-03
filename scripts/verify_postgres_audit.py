"""Verify PostgreSQL audit-event immutability after Alembic migrations."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url or not database_url.startswith("postgresql"):
        raise SystemExit("DATABASE_URL must target PostgreSQL")

    engine = create_engine(database_url, pool_pre_ping=True)
    event_id = uuid4()
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO audit_events "
                    "(id, action, subject_type, details, occurred_at) "
                    "VALUES (:id, :action, :subject_type, CAST(:details AS JSON), :occurred_at)"
                ),
                {
                    "id": event_id,
                    "action": "ci.immutability_probe",
                    "subject_type": "ci_probe",
                    "details": "{}",
                    "occurred_at": datetime.now(UTC),
                },
            )

        for mutation in ("UPDATE", "DELETE"):
            try:
                with engine.begin() as connection:
                    if mutation == "UPDATE":
                        connection.execute(
                            text("UPDATE audit_events SET action = 'tampered' WHERE id = :id"),
                            {"id": event_id},
                        )
                    else:
                        connection.execute(
                            text("DELETE FROM audit_events WHERE id = :id"),
                            {"id": event_id},
                        )
            except DBAPIError as exc:
                if "immutable" not in str(exc.orig).lower():
                    raise
            else:
                raise AssertionError(f"Audit-event {mutation} unexpectedly succeeded")

        with engine.begin() as connection:
            action = connection.execute(
                text("SELECT action FROM audit_events WHERE id = :id"),
                {"id": event_id},
            ).scalar_one()
        if action != "ci.immutability_probe":
            raise AssertionError("Audit event changed despite immutability trigger")
        print("PostgreSQL audit UPDATE and DELETE triggers passed.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
