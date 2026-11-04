#!/usr/bin/env python3
"""Load one synthetic persona into an existing verified local user account.

This script never creates a fake login identity. It is disabled in production and
requires an existing verified user selected by email.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select

from myeconomy.application.financial import (
    create_financial_account,
    create_recurring_obligation,
    import_transactions_csv,
)
from myeconomy.infrastructure.database import SessionLocal
from myeconomy.infrastructure.models import FinancialAccount, RecurringObligation, User

AS_OF = date(2026, 11, 3)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _next_due(first_due: date, frequency: str, due_day: int | None) -> date:
    current = first_due
    while current < AS_OF:
        if frequency == "WEEKLY":
            current += timedelta(days=7)
        elif frequency == "FORTNIGHTLY":
            current += timedelta(days=14)
        else:
            months = {"MONTHLY": 1, "QUARTERLY": 3, "YEARLY": 12}[frequency]
            month_index = current.year * 12 + current.month - 1 + months
            year, month0 = divmod(month_index, 12)
            month = month0 + 1
            day = min(due_day or current.day, monthrange(year, month)[1])
            current = date(year, month, day)
    return current


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-email", required=True, help="Existing verified MyEconomy account")
    parser.add_argument("--customer-id", default="CUS00001", help="Synthetic fixture persona ID")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "demo_data" / "synthetic_v1",
    )
    args = parser.parse_args()

    app_env = os.getenv("APP_ENV", "development").strip().lower()
    if app_env not in {"development", "test", "demo"}:
        raise SystemExit(
            "Refusing to seed synthetic data unless APP_ENV is development, test or demo."
        )

    dataset = args.dataset_dir.resolve()
    _, account_rows = _read_csv(dataset / "csv" / "accounts.csv")
    transaction_headers, transaction_rows = _read_csv(dataset / "csv" / "transactions.csv")
    _, obligation_rows = _read_csv(dataset / "csv" / "recurring_obligations.csv")

    customer_accounts = [r for r in account_rows if r["customer_id"] == args.customer_id]
    customer_transactions = [r for r in transaction_rows if r["customer_id"] == args.customer_id]
    customer_obligations = [r for r in obligation_rows if r["customer_id"] == args.customer_id]
    all_rows = customer_accounts + customer_transactions + customer_obligations
    if not all_rows or any(row.get("data_class") != "SYNTHETIC_FIXTURE" for row in all_rows):
        raise SystemExit(
            "Selected records are missing or not explicitly labeled SYNTHETIC_FIXTURE."
        )

    created_accounts = 0
    reused_accounts = 0
    imported_rows = 0
    replayed_batches = 0
    replayed_rows = 0
    updated_rows = 0
    rejected_batches = 0
    created_obligations = 0
    reused_obligations = 0

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == args.user_email.strip().casefold()))
        if user is None or not user.is_active or not user.email_verified:
            raise SystemExit("An existing active, email-verified MyEconomy user is required.")

        account_map: dict[str, FinancialAccount] = {}
        for fixture in customer_accounts:
            existing = db.scalar(
                select(FinancialAccount).where(
                    FinancialAccount.owner_user_id == user.id,
                    FinancialAccount.source_type == "SYNTHETIC_FIXTURE",
                    FinancialAccount.source_external_id == fixture["account_id"],
                )
            )
            if existing:
                account = existing
                reused_accounts += 1
            else:
                account = create_financial_account(
                    db,
                    owner=user,
                    account_name=f"Demo {fixture['account_type'].replace('_', ' ').title()}",
                    account_type=fixture["account_type"],
                    currency=fixture["currency"],
                    institution_label=fixture["institution_code"],
                    masked_reference=fixture["masked_reference"],
                    opening_balance=Decimal(fixture["opening_balance_inr"]),
                    source_type="SYNTHETIC_FIXTURE",
                    source_external_id=fixture["account_id"],
                )
                created_accounts += 1
            account_map[fixture["account_id"]] = account

        for fixture_account_id, account in account_map.items():
            selected = [r for r in customer_transactions if r["account_id"] == fixture_account_id]
            if not selected:
                continue
            output = io.StringIO(newline="")
            writer = csv.DictWriter(output, fieldnames=transaction_headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(selected)
            content = output.getvalue().encode("utf-8")
            import_key = f"synthetic-v1:{args.customer_id}:{fixture_account_id}"
            outcome = import_transactions_csv(
                db,
                owner=user,
                account_id=account.id,
                idempotency_key=import_key,
                filename=f"{fixture_account_id}_synthetic_statement.csv",
                content=content,
            )
            if outcome.batch.status == "REJECTED":
                rejected_batches += 1
            elif outcome.replayed:
                replayed_batches += 1
                replayed_rows += outcome.batch.inserted_count
            else:
                imported_rows += outcome.batch.inserted_count
                updated_rows += outcome.batch.updated_count

        default_account = next(iter(account_map.values()), None)
        for fixture in customer_obligations:
            existing = db.scalar(
                select(RecurringObligation).where(
                    RecurringObligation.owner_user_id == user.id,
                    RecurringObligation.source_type == "SYNTHETIC_FIXTURE",
                    RecurringObligation.source_external_id == fixture["obligation_id"],
                )
            )
            if existing:
                reused_obligations += 1
                continue
            first_due = date.fromisoformat(fixture["first_due_date"])
            frequency = fixture["frequency"]
            due_day = int(fixture["due_day"]) if fixture.get("due_day") else None
            if frequency in {"MONTHLY", "QUARTERLY", "YEARLY"} and due_day is not None:
                first_due = date(
                    first_due.year,
                    first_due.month,
                    min(due_day, monthrange(first_due.year, first_due.month)[1]),
                )
            create_recurring_obligation(
                db,
                owner=user,
                payee_label=fixture["payee_label"],
                category=fixture["category"],
                amount=Decimal(fixture["expected_amount_inr"]),
                currency="INR",
                frequency=frequency,
                first_due_date=first_due,
                next_due_date=_next_due(first_due, frequency, due_day),
                due_day=due_day,
                account_id=default_account.id if default_account else None,
                autopay_enabled=fixture["autopay_enabled"].lower() == "true",
                essential=fixture["essential"].lower() == "true",
                source_type="SYNTHETIC_FIXTURE",
                source_external_id=fixture["obligation_id"],
            )
            created_obligations += 1

    if rejected_batches:
        raise SystemExit(
            f"Seed finished with {rejected_batches} rejected CSV batches; "
            "inspect import batches before demo."
        )
    print(
        "Synthetic customer seed completed: "
        f"accounts_created={created_accounts}, accounts_reused={reused_accounts}, "
        f"transactions_inserted={imported_rows}, transactions_updated={updated_rows}, "
        f"import_batches_replayed={replayed_batches}, replayed_batch_rows={replayed_rows}, "
        f"obligations_created={created_obligations}, obligations_reused={reused_obligations}. "
        "No fake login identity was created."
    )


if __name__ == "__main__":
    main()
