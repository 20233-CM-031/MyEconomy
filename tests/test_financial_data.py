from __future__ import annotations

from datetime import date
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from myeconomy.domain.financial import MAX_CSV_BYTES
from myeconomy.infrastructure.models import (
    FinancialAccount,
    FinancialTransaction,
    RecurringObligation,
    User,
)


def register_verified(client, email: str, display_name: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "A-Long-Unique-Passphrase-2026!",
            "display_name": display_name,
        },
    )
    assert response.status_code == 201, response.text
    token = client.app.state.verification_tokens[email]
    verified = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verified.status_code == 200, verified.text
    return response.json()


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_account(client, token: str, account_name: str = "Primary account") -> dict:
    response = client.post(
        "/api/v1/financial/accounts",
        headers=auth(token),
        json={
            "account_name": account_name,
            "account_type": "BANK_DEPOSIT",
            "currency": "INR",
            "opening_balance": "0.00",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def sample_statement() -> bytes:
    return (
        b"transaction_date,amount_inr,currency,direction,cashflow_treatment,category,"
        b"counterparty_label,reference,status,essential,posted_at\n"
        b"2026-11-01,100000.00,INR,CREDIT,INCOME,salary,DEMO-EMPLOYER,TX-1,POSTED,true,2026-11-01T10:00:00+00:00\n"
        b"2026-11-02,25000.00,INR,DEBIT,EXPENSE,rent,DEMO-LESSOR,TX-2,POSTED,true,2026-11-02T10:00:00+00:00\n"
        b"2026-11-05,5000.00,INR,CREDIT,REFUND,rent,DEMO-LESSOR,TX-3,POSTED,true,2026-11-05T10:00:00+00:00\n"
        b"2026-11-06,2000.00,INR,DEBIT,EXPENSE,shopping,DEMO-STORE,TX-4,PENDING,false,2026-11-06T10:00:00+00:00\n"
        b"2026-11-07,8000.00,INR,CREDIT,TRANSFER,internal transfer,SELF,TX-5,POSTED,false,"
        b"2026-11-07T10:00:00+00:00\n"
    )


def upload(client, account_id: str, token: str, content: bytes, key: str):
    return client.post(
        f"/api/v1/financial/accounts/{account_id}/imports/csv",
        headers={
            **auth(token),
            "Content-Type": "text/csv",
            "Idempotency-Key": key,
            "X-Filename": "synthetic-statement.csv",
        },
        content=content,
    )


def test_financial_import_and_cashflow_semantics(test_environment) -> None:
    client, _ = test_environment
    user = register_verified(client, "finance-owner@example.com", "Finance Owner")
    account = create_account(client, user["access_token"])

    imported = upload(
        client, account["id"], user["access_token"], sample_statement(), "statement-001"
    )
    assert imported.status_code == 200, imported.text
    body = imported.json()
    assert body["status"] == "COMPLETED"
    assert body["row_count"] == 5
    assert body["inserted_count"] == 5
    assert body["updated_count"] == 0
    assert body["duplicate_count"] == 0
    batch_view = client.get(
        f"/api/v1/financial/imports/{body['batch_id']}", headers=auth(user["access_token"])
    )
    assert batch_view.status_code == 200
    assert batch_view.json()["source_sha256"] == body["source_sha256"]

    tx = client.get(
        f"/api/v1/financial/accounts/{account['id']}/transactions",
        headers=auth(user["access_token"]),
    )
    assert tx.status_code == 200
    assert len(tx.json()) == 5

    cashflow = client.get(
        "/api/v1/financial/cashflow",
        params={
            "period_start": "2026-11-01",
            "period_end": "2026-11-30",
            "currency": "INR",
        },
        headers=auth(user["access_token"]),
    )
    assert cashflow.status_code == 200, cashflow.text
    result = cashflow.json()
    assert result["posted_transaction_count"] == 4
    assert result["income_total"] == "100000.00"
    assert result["gross_expenses"] == "25000.00"
    assert result["refunds"] == "5000.00"
    assert result["net_expenses_after_refunds"] == "20000.00"
    assert result["net_cashflow"] == "80000.00"
    assert result["net_cashflow_to_income_percent"] == "80.00"
    assert result["pending_transactions_excluded"] is True


def test_import_idempotency_and_external_reference_duplicate_detection(test_environment) -> None:
    client, session_factory = test_environment
    user = register_verified(client, "idempotent-owner@example.com", "Idempotent Owner")
    account = create_account(client, user["access_token"])
    content = sample_statement()

    first = upload(client, account["id"], user["access_token"], content, "same-key")
    replay = upload(client, account["id"], user["access_token"], content, "same-key")
    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json()["replayed"] is True
    assert replay.json()["batch_id"] == first.json()["batch_id"]
    assert replay.json()["updated_count"] == 0

    changed = content.replace(b"100000.00", b"100001.00")
    conflict = upload(client, account["id"], user["access_token"], changed, "same-key")
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency_conflict"

    duplicate_batch = upload(client, account["id"], user["access_token"], content, "different-key")
    assert duplicate_batch.status_code == 200
    assert duplicate_batch.json()["inserted_count"] == 0
    assert duplicate_batch.json()["duplicate_count"] == 5
    with session_factory() as db:
        assert len(list(db.scalars(select(FinancialTransaction)))) == 5


def test_invalid_csv_is_rejected_atomically(test_environment) -> None:
    client, session_factory = test_environment
    user = register_verified(client, "invalid-owner@example.com", "Invalid Owner")
    account = create_account(client, user["access_token"])
    invalid = sample_statement().replace(b"2026-11-02", b"not-a-date")
    response = upload(client, account["id"], user["access_token"], invalid, "bad-file")
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["inserted_count"] == 0
    assert body["validation_errors"]
    with session_factory() as db:
        assert len(list(db.scalars(select(FinancialTransaction)))) == 0


def test_conflicting_external_reference_rejects_whole_batch(test_environment) -> None:
    client, session_factory = test_environment
    user = register_verified(client, "conflict-owner@example.com", "Conflict Owner")
    account = create_account(client, user["access_token"])
    original = sample_statement()
    first = upload(client, account["id"], user["access_token"], original, "original")
    assert first.status_code == 200
    changed = original.replace(b"100000.00", b"90000.00")
    rejected = upload(client, account["id"], user["access_token"], changed, "altered-reference")
    assert rejected.status_code == 422
    assert rejected.json()["status"] == "REJECTED"
    with session_factory() as db:
        assert len(list(db.scalars(select(FinancialTransaction)))) == 5


def test_possible_duplicate_without_provider_reference_is_flagged_not_dropped(
    test_environment,
) -> None:
    client, session_factory = test_environment
    user = register_verified(client, "potential-duplicate@example.com", "Potential Duplicate")
    account = create_account(client, user["access_token"])
    content = (
        b"transaction_date,amount,currency,direction,cashflow_treatment,category,counterparty\n"
        b"2026-11-01,499.00,INR,DEBIT,EXPENSE,groceries,DEMO-MARKET\n"
        b"2026-11-01,499.00,INR,DEBIT,EXPENSE,groceries,DEMO-MARKET\n"
    )
    response = upload(
        client, account["id"], user["access_token"], content, "same-looking-purchases"
    )
    assert response.status_code == 200
    assert response.json()["inserted_count"] == 2
    assert response.json()["potential_duplicate_count"] == 1
    with session_factory() as db:
        rows = list(
            db.scalars(select(FinancialTransaction).order_by(FinancialTransaction.created_at))
        )
        assert len(rows) == 2
        assert rows[0].potential_duplicate_of_id is None
        assert rows[1].potential_duplicate_of_id == rows[0].id


def test_financial_records_are_owner_scoped(test_environment) -> None:
    client, _ = test_environment
    alice = register_verified(client, "financial-alice@example.com", "Alice")
    bob = register_verified(client, "financial-bob@example.com", "Bob")
    account = create_account(client, alice["access_token"], "Alice private account")
    denied = client.get(
        f"/api/v1/financial/accounts/{account['id']}/transactions",
        headers=auth(bob["access_token"]),
    )
    assert denied.status_code == 404
    denied_import = upload(
        client, account["id"], bob["access_token"], sample_statement(), "bob-key"
    )
    assert denied_import.status_code == 404


def test_recurring_obligation_is_persisted_and_currency_checked(test_environment) -> None:
    client, session_factory = test_environment
    user = register_verified(client, "obligation-owner@example.com", "Obligation Owner")
    account = create_account(client, user["access_token"])
    payload = {
        "payee_label": "DEMO-EDUCATION-PROVIDER",
        "category": "education",
        "amount": "8500.00",
        "currency": "INR",
        "frequency": "MONTHLY",
        "first_due_date": "2026-11-05",
        "next_due_date": "2026-11-05",
        "due_day": 5,
        "account_id": account["id"],
        "autopay_enabled": False,
        "essential": True,
    }
    created = client.post(
        "/api/v1/financial/obligations", json=payload, headers=auth(user["access_token"])
    )
    assert created.status_code == 201, created.text
    assert created.json()["amount"] == "8500.00"
    listing = client.get("/api/v1/financial/obligations", headers=auth(user["access_token"]))
    assert len(listing.json()) == 1
    with session_factory() as db:
        item = db.scalar(select(RecurringObligation))
        assert item is not None
        assert item.amount_minor == 850000

    payload["currency"] = "USD"
    mismatch = client.post(
        "/api/v1/financial/obligations", json=payload, headers=auth(user["access_token"])
    )
    assert mismatch.status_code == 422


def test_csv_upload_enforces_body_limit_and_media_type(test_environment) -> None:
    client, _ = test_environment
    user = register_verified(client, "upload-limits@example.com", "Upload Limits")
    account = create_account(client, user["access_token"])
    too_large = upload(
        client, account["id"], user["access_token"], b"x" * (MAX_CSV_BYTES + 1), "too-large"
    )
    assert too_large.status_code == 413
    wrong_type = client.post(
        f"/api/v1/financial/accounts/{account['id']}/imports/csv",
        headers={
            **auth(user["access_token"]),
            "Content-Type": "application/json",
            "Idempotency-Key": "wrong-type",
        },
        content=b"{}",
    )
    assert wrong_type.status_code == 415


def test_account_currency_mismatch_rejects_import(test_environment) -> None:
    client, session_factory = test_environment
    user = register_verified(client, "currency-owner@example.com", "Currency Owner")
    account = create_account(client, user["access_token"])
    content = sample_statement().replace(b",INR,", b",USD,")
    rejected = upload(client, account["id"], user["access_token"], content, "wrong-currency")
    assert rejected.status_code == 422
    assert rejected.json()["status"] == "REJECTED"
    with session_factory() as db:
        assert len(list(db.scalars(select(FinancialTransaction)))) == 0


def test_database_composite_keys_reject_wrong_owner_and_currency(test_environment) -> None:
    client, session_factory = test_environment
    alice = register_verified(client, "composite-alice@example.com", "Alice")
    register_verified(client, "composite-bob@example.com", "Bob")
    account = create_account(client, alice["access_token"], "Alice INR account")
    with session_factory() as db:
        owner = db.scalar(select(User).where(User.email == "composite-bob@example.com"))
        alice_account = db.scalar(
            select(FinancialAccount).where(FinancialAccount.id == UUID(account["id"]))
        )
        assert owner is not None and alice_account is not None

        wrong_owner = FinancialTransaction(
            owner_user_id=owner.id,
            account_id=alice_account.id,
            occurred_on=date(2026, 11, 1),
            amount_minor=100,
            currency="INR",
            direction="DEBIT",
            cashflow_treatment="EXPENSE",
            category="test",
            description="Wrong owner constraint probe",
            status="POSTED",
            essential=False,
            fingerprint_sha256="a" * 64,
        )
        db.add(wrong_owner)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        wrong_currency = FinancialTransaction(
            owner_user_id=alice_account.owner_user_id,
            account_id=alice_account.id,
            occurred_on=date(2026, 11, 1),
            amount_minor=100,
            currency="USD",
            direction="DEBIT",
            cashflow_treatment="EXPENSE",
            category="test",
            description="Wrong currency constraint probe",
            status="POSTED",
            essential=False,
            fingerprint_sha256="b" * 64,
        )
        db.add(wrong_currency)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def _single_reference_statement(*, status: str, posted_at: str = "") -> bytes:
    return (
        "transaction_date,amount,currency,direction,cashflow_treatment,category,"
        "counterparty,reference,status,posted_at\n"
        f"2026-11-08,2500.00,INR,DEBIT,EXPENSE,utilities,DEMO-POWER,TX-LIFECYCLE,{status},{posted_at}\n"
    ).encode()


def test_pending_transaction_reconciles_to_posted_with_audited_update(test_environment) -> None:
    client, session_factory = test_environment
    user = register_verified(client, "lifecycle-owner@example.com", "Lifecycle Owner")
    account = create_account(client, user["access_token"])

    pending = upload(
        client,
        account["id"],
        user["access_token"],
        _single_reference_statement(status="PENDING"),
        "lifecycle-pending",
    )
    assert pending.status_code == 200, pending.text
    assert pending.json()["inserted_count"] == 1
    assert pending.json()["updated_count"] == 0

    posted = upload(
        client,
        account["id"],
        user["access_token"],
        _single_reference_statement(status="POSTED", posted_at="2026-11-08T11:30:00+05:30"),
        "lifecycle-posted",
    )
    assert posted.status_code == 200, posted.text
    assert posted.json()["inserted_count"] == 0
    assert posted.json()["updated_count"] == 1
    assert posted.json()["duplicate_count"] == 0

    details = client.get(
        f"/api/v1/financial/imports/{posted.json()['batch_id']}",
        headers=auth(user["access_token"]),
    )
    assert details.status_code == 200
    assert details.json()["updated_count"] == 1

    with session_factory() as db:
        transaction = db.scalar(select(FinancialTransaction))
        assert transaction is not None
        assert transaction.status == "POSTED"
        assert transaction.posted_at is not None
        assert transaction.posted_at.isoformat().startswith("2026-11-08T06:00:00")

    cashflow = client.get(
        "/api/v1/financial/cashflow",
        params={
            "period_start": "2026-11-01",
            "period_end": "2026-11-30",
            "currency": "INR",
        },
        headers=auth(user["access_token"]),
    )
    assert cashflow.status_code == 200
    assert cashflow.json()["gross_expenses"] == "2500.00"
    transactions = client.get(
        f"/api/v1/financial/accounts/{account['id']}/transactions",
        headers=auth(user["access_token"]),
    )
    assert transactions.status_code == 200
    assert transactions.json()[0]["posted_at"].endswith(("Z", "+00:00"))


def test_reversed_transaction_cannot_be_reactivated(test_environment) -> None:
    client, session_factory = test_environment
    user = register_verified(client, "terminal-owner@example.com", "Terminal Owner")
    account = create_account(client, user["access_token"])

    posted = upload(
        client,
        account["id"],
        user["access_token"],
        _single_reference_statement(status="POSTED", posted_at="2026-11-08T10:00:00+00:00"),
        "terminal-posted",
    )
    assert posted.status_code == 200, posted.text

    reversed_response = upload(
        client,
        account["id"],
        user["access_token"],
        _single_reference_statement(status="REVERSED"),
        "terminal-reversed",
    )
    assert reversed_response.status_code == 200, reversed_response.text
    assert reversed_response.json()["updated_count"] == 1

    reactivated = upload(
        client,
        account["id"],
        user["access_token"],
        _single_reference_statement(status="POSTED", posted_at="2026-11-08T10:00:00+00:00"),
        "terminal-reactivation-attempt",
    )
    assert reactivated.status_code == 422
    assert reactivated.json()["status"] == "REJECTED"
    assert any(
        error["code"] == "invalid_status_transition"
        for error in reactivated.json()["validation_errors"]
    )
    with session_factory() as db:
        transaction = db.scalar(select(FinancialTransaction))
        assert transaction is not None
        assert transaction.status == "REVERSED"
        transaction.amount_minor = 200
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        transaction = db.scalar(select(FinancialTransaction))
        assert transaction is not None and transaction.amount_minor == 250000
        transaction.status = "POSTED"
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        assert transaction.status == "REVERSED"


def test_missing_cashflow_treatment_is_excluded_until_classified(test_environment) -> None:
    client, _ = test_environment
    user = register_verified(client, "unclassified-owner@example.com", "Unclassified Owner")
    account = create_account(client, user["access_token"])
    statement = (
        b"transaction_date,amount,currency,direction,category,counterparty,reference,status\n"
        b"2026-11-09,75000.00,INR,CREDIT,transfer,DEMO-SELF,UNCLASSIFIED-1,POSTED\n"
    )
    imported = upload(client, account["id"], user["access_token"], statement, "unclassified-credit")
    assert imported.status_code == 200, imported.text
    transactions = client.get(
        f"/api/v1/financial/accounts/{account['id']}/transactions",
        headers=auth(user["access_token"]),
    )
    assert transactions.status_code == 200
    assert transactions.json()[0]["cashflow_treatment"] == "IGNORE"

    cashflow = client.get(
        "/api/v1/financial/cashflow",
        params={"period_start": "2026-11-01", "period_end": "2026-11-30", "currency": "INR"},
        headers=auth(user["access_token"]),
    )
    assert cashflow.status_code == 200
    assert cashflow.json()["income_total"] == "0.00"


def test_amount_inr_header_rejects_non_inr_account(test_environment) -> None:
    client, _ = test_environment
    user = register_verified(client, "amount-inr-owner@example.com", "Amount INR Owner")
    account_response = client.post(
        "/api/v1/financial/accounts",
        headers=auth(user["access_token"]),
        json={"account_name": "USD account", "account_type": "BANK_DEPOSIT", "currency": "USD"},
    )
    assert account_response.status_code == 201, account_response.text
    statement = b"transaction_date,amount_inr,direction\n2026-11-09,500.00,CREDIT\n"
    rejected = upload(
        client, account_response.json()["id"], user["access_token"], statement, "amount-inr-usd"
    )
    assert rejected.status_code == 422
    assert rejected.json()["status"] == "REJECTED"


def test_same_provider_reference_with_conflicting_states_in_one_batch_is_rejected(
    test_environment,
) -> None:
    client, session_factory = test_environment
    user = register_verified(client, "infile-state-owner@example.com", "In File State Owner")
    account = create_account(client, user["access_token"])
    statement = (
        b"transaction_date,amount,currency,direction,cashflow_treatment,category,"
        b"counterparty,reference,status\n"
        b"2026-11-10,1200.00,INR,DEBIT,EXPENSE,transport,DEMO-CAB,TX-DUP-STATE,PENDING\n"
        b"2026-11-10,1200.00,INR,DEBIT,EXPENSE,transport,DEMO-CAB,TX-DUP-STATE,POSTED\n"
    )
    response = upload(
        client, account["id"], user["access_token"], statement, "same-file-conflicting-status"
    )
    assert response.status_code == 422
    assert response.json()["status"] == "REJECTED"
    assert any(
        error["code"] == "external_reference_conflict"
        for error in response.json()["validation_errors"]
    )
    with session_factory() as db:
        assert db.scalar(select(FinancialTransaction)) is None
