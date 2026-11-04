"""Verify PostgreSQL audit-event immutability after Alembic migrations."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError


def verify_financial_status_transition_trigger(connection) -> None:
    """Verify the DB rejects a terminal transaction being reactivated."""
    user_id = uuid4()
    account_id = uuid4()
    transaction_id = uuid4()
    now = datetime.now(UTC)
    connection.execute(
        text(
            "INSERT INTO users "
            "(id, email, password_hash, display_name, email_verified, is_active, created_at) "
            "VALUES (:id, :email, :password_hash, :display_name, TRUE, TRUE, :created_at)"
        ),
        {
            "id": user_id,
            "email": f"ci-{user_id}@example.invalid",
            "password_hash": "ci-only-not-a-valid-login-hash",
            "display_name": "CI Status Probe",
            "created_at": now,
        },
    )
    connection.execute(
        text(
            "INSERT INTO financial_accounts "
            "(id, owner_user_id, account_name, account_type, currency, opening_balance_minor, "
            "status, source_type, created_at, updated_at) "
            "VALUES (:id, :owner, 'CI Probe', 'BANK_DEPOSIT', 'INR', 0, 'ACTIVE', 'MANUAL', "
            ":now, :now)"
        ),
        {"id": account_id, "owner": user_id, "now": now},
    )
    connection.execute(
        text(
            "INSERT INTO financial_transactions "
            "(id, owner_user_id, account_id, occurred_on, amount_minor, currency, direction, "
            "cashflow_treatment, category, description, status, essential, fingerprint_sha256, "
            "created_at) "
            "VALUES (:id, :owner, :account, CURRENT_DATE, 100, 'INR', 'DEBIT', 'EXPENSE', "
            "'ci', 'CI status transition probe', 'PENDING', FALSE, :fingerprint, :now)"
        ),
        {
            "id": transaction_id,
            "owner": user_id,
            "account": account_id,
            "fingerprint": "f" * 64,
            "now": now,
        },
    )
    connection.execute(
        text("UPDATE financial_transactions SET status = 'POSTED' WHERE id = :id"),
        {"id": transaction_id},
    )
    connection.execute(
        text("UPDATE financial_transactions SET status = 'REVERSED' WHERE id = :id"),
        {"id": transaction_id},
    )

    try:
        with connection.begin_nested():
            connection.execute(
                text("UPDATE financial_transactions SET amount_minor = 200 WHERE id = :id"),
                {"id": transaction_id},
            )
    except DBAPIError as exc:
        if "financial transaction facts are immutable" not in str(exc.orig).lower():
            raise
    else:
        raise AssertionError("PostgreSQL allowed an imported transaction amount to be edited")

    try:
        with connection.begin_nested():
            connection.execute(
                text("UPDATE financial_transactions SET status = 'POSTED' WHERE id = :id"),
                {"id": transaction_id},
            )
    except DBAPIError as exc:
        if "invalid financial transaction status transition" not in str(exc.orig).lower():
            raise
    else:
        raise AssertionError("PostgreSQL allowed a REVERSED transaction to become POSTED")

    amount, status = connection.execute(
        text("SELECT amount_minor, status FROM financial_transactions WHERE id = :id"),
        {"id": transaction_id},
    ).one()
    if amount != 100 or status != "REVERSED":
        raise AssertionError("PostgreSQL guard did not preserve immutable facts and terminal state")
    connection.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
    print("PostgreSQL financial transaction immutability and status-transition guards passed.")


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

        with engine.begin() as connection:
            verify_financial_status_transition_trigger(connection)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
