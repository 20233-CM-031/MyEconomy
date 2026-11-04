"""Deterministic Personal Mode report construction for AwnNORA.

This module intentionally has no database, HTTP, model SDK, or provider dependency.
The output is an evidence-indexed review aid, not a financial recommendation or
proof of a recovered/saved amount.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, DecimalException

from myeconomy.domain.money import currency_exponent, quantize_total


class PersonalPowerRuleError(ValueError):
    """A report input violates a deterministic financial invariant."""


@dataclass(frozen=True, slots=True)
class DuplicateCandidate:
    transaction_id: str
    amount: Decimal
    currency: str
    occurred_on: date
    possible_duplicate_of_id: str
    description: str

    def __post_init__(self) -> None:
        if not self.transaction_id or not self.possible_duplicate_of_id:
            raise PersonalPowerRuleError(
                "Duplicate candidates require both transaction references."
            )
        _validate_money(self.amount, self.currency, allow_zero=False)
        if not self.description.strip():
            raise PersonalPowerRuleError("Duplicate candidate description is required.")


@dataclass(frozen=True, slots=True)
class UpcomingObligation:
    obligation_id: str
    payee_label: str
    amount: Decimal
    currency: str
    next_due_date: date
    frequency: str
    essential: bool

    def __post_init__(self) -> None:
        if not self.obligation_id or not self.payee_label.strip():
            raise PersonalPowerRuleError("Obligation reference and payee label are required.")
        _validate_money(self.amount, self.currency, allow_zero=False)
        if self.frequency not in {"WEEKLY", "FORTNIGHTLY", "MONTHLY", "QUARTERLY", "YEARLY"}:
            raise PersonalPowerRuleError("Unsupported recurring-obligation frequency.")


def _validate_money(
    value: Decimal, currency: str, *, allow_zero: bool = True, allow_negative: bool = False
) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise PersonalPowerRuleError("Money must be a finite Decimal value.")
    if (value < 0 and not allow_negative) or (not allow_zero and value <= 0):
        raise PersonalPowerRuleError("Money sign is outside the permitted range.")
    if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
        raise PersonalPowerRuleError("Currency must be a three-letter code.")
    try:
        currency_exponent(currency.upper())
        if quantize_total(value, currency.upper()) != value:
            raise PersonalPowerRuleError("Money exceeds the currency's minor-unit precision.")
    except (ValueError, DecimalException) as exc:
        raise PersonalPowerRuleError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class PersonalPowerInput:
    owner_reference: str
    currency: str
    period_start: date
    period_end: date
    as_of: date
    account_count: int
    posted_transaction_count: int
    income_total: Decimal
    gross_expenses: Decimal
    refunds: Decimal
    essential_expenses: Decimal
    discretionary_expenses: Decimal
    net_cashflow: Decimal
    duplicate_candidates: tuple[DuplicateCandidate, ...] = ()
    upcoming_obligations: tuple[UpcomingObligation, ...] = ()
    obligation_horizon_days: int = 30

    def __post_init__(self) -> None:
        if not self.owner_reference:
            raise PersonalPowerRuleError("Owner reference is required for a private report.")
        _validate_money(self.income_total, self.currency)
        _validate_money(self.gross_expenses, self.currency)
        _validate_money(self.refunds, self.currency)
        _validate_money(self.essential_expenses, self.currency)
        _validate_money(self.discretionary_expenses, self.currency)
        _validate_money(self.net_cashflow, self.currency, allow_negative=True)
        if self.period_end < self.period_start:
            raise PersonalPowerRuleError("Report period end cannot precede its start.")
        if self.period_end > self.as_of:
            raise PersonalPowerRuleError("Report period end cannot be after the as-of date.")
        if self.account_count < 0 or self.posted_transaction_count < 0:
            raise PersonalPowerRuleError("Record counts cannot be negative.")
        if not 1 <= self.obligation_horizon_days <= 90:
            raise PersonalPowerRuleError("Obligation horizon must be between 1 and 90 days.")
        if self.essential_expenses + self.discretionary_expenses != self.gross_expenses:
            raise PersonalPowerRuleError("Essential and discretionary expenses must reconcile.")
        if self.net_cashflow != self.income_total - self.gross_expenses + self.refunds:
            raise PersonalPowerRuleError(
                "Net cashflow does not reconcile to income, expenses and refunds."
            )
        normalized = self.currency.upper()
        if any(x.currency.upper() != normalized for x in self.duplicate_candidates):
            raise PersonalPowerRuleError("Duplicate candidates cannot mix currencies.")
        if any(x.currency.upper() != normalized for x in self.upcoming_obligations):
            raise PersonalPowerRuleError("Upcoming obligations cannot mix currencies.")


@dataclass(frozen=True, slots=True)
class PowerFinding:
    finding_id: str
    code: str
    priority: str
    title: str
    explanation: str
    recommended_next_step: str
    amount: Decimal | None
    currency: str | None
    source_references: tuple[str, ...]
    value_status: str = "NOT_A_VALUE_OUTCOME"


@dataclass(frozen=True, slots=True)
class PersonalPowerReport:
    report_version: str
    currency: str
    period_start: date
    period_end: date
    as_of: date
    account_count: int
    posted_transaction_count: int
    income_total: Decimal
    gross_expenses: Decimal
    refunds: Decimal
    net_expenses_after_refunds: Decimal
    essential_expenses: Decimal
    discretionary_expenses: Decimal
    net_cashflow: Decimal
    upcoming_essential_obligations: Decimal
    upcoming_obligation_count: int
    potential_duplicate_count: int
    verified_value_created: Decimal
    findings: tuple[PowerFinding, ...]
    read_only: bool = True
    external_actions_taken: bool = False
    commons_required: bool = False
    limitations: tuple[str, ...] = (
        "This report uses only records already imported into this AwnNORA account.",
        (
            "It is not a verified bank balance, credit assessment, legal opinion "
            "or official eligibility decision."
        ),
        (
            "Potential duplicates and upcoming obligations require user review; "
            "no recovery or saving is assumed."
        ),
        (
            "No external provider, bank, employer, insurer, government "
            "or payment system was contacted."
        ),
    )


def build_personal_power_report(data: PersonalPowerInput) -> PersonalPowerReport:
    """Create prioritized, owner-private action signals from persisted financial facts."""
    currency = data.currency.upper()
    findings: list[PowerFinding] = []

    if data.posted_transaction_count == 0:
        findings.append(
            PowerFinding(
                "DATA-001",
                "NO_POSTED_DATA",
                "INFO",
                "Add a financial record to unlock analysis",
                (
                    "No posted transactions were found for the selected period and currency. "
                    "AwnNORA will not infer income or expenses from incomplete data."
                ),
                (
                    "Import a statement or add a record manually; "
                    "verify classifications before relying on the result."
                ),
                None,
                None,
                (),
            )
        )
    elif data.income_total == 0:
        findings.append(
            PowerFinding(
                "DATA-002",
                "NO_CLASSIFIED_INCOME",
                "INFO",
                "Income is not classified in this period",
                (
                    "The imported records contain no posted entries classified as income. "
                    "This may be incomplete data, not proof that income is zero."
                ),
                (
                    "Review unclassified/ignored credits and classify them only "
                    "when the source supports the treatment."
                ),
                None,
                None,
                (),
            )
        )

    if data.net_cashflow < 0:
        findings.append(
            PowerFinding(
                "CASH-001",
                "NEGATIVE_NET_CASHFLOW",
                "HIGH",
                "Outflow exceeded classified inflow",
                (
                    "Posted classified expenses exceeded classified income "
                    "after refunds in the selected period."
                ),
                (
                    "Review essential commitments, due dates and reversible discretionary costs. "
                    "Do not assume a new loan is the right response."
                ),
                abs(data.net_cashflow),
                currency,
                (),
            )
        )

    if data.income_total > 0 and data.essential_expenses >= data.income_total:
        findings.append(
            PowerFinding(
                "CASH-002",
                "ESSENTIAL_COST_PRESSURE",
                "HIGH",
                "Essential costs meet or exceed classified income",
                (
                    "Essential outflow in the selected period is at least as large as "
                    "classified income. The signal is limited to imported records and "
                    "the selected period."
                ),
                (
                    "Check missing income records, essential bill accuracy, "
                    "available relief/entitlements and safe payment arrangements."
                ),
                data.essential_expenses,
                currency,
                (),
            )
        )

    for index, candidate in enumerate(
        sorted(data.duplicate_candidates, key=lambda x: (x.occurred_on, x.transaction_id)), start=1
    ):
        findings.append(
            PowerFinding(
                f"DUP-{index:03d}",
                "POSSIBLE_DUPLICATE_TRANSACTION",
                "MEDIUM",
                "A transaction needs duplicate review",
                (
                    "The import process linked this transaction to a potential "
                    "duplicate fingerprint. This is a review signal, not proof of double charging."
                ),
                (
                    "Compare the original statement and account posting. "
                    "Contact the provider only after you confirm the duplicate."
                ),
                candidate.amount,
                currency,
                (candidate.transaction_id, candidate.possible_duplicate_of_id),
            )
        )

    horizon_end = data.as_of + timedelta(days=data.obligation_horizon_days)
    relevant = [o for o in data.upcoming_obligations if o.next_due_date <= horizon_end]
    essential = [o for o in relevant if o.essential]
    essential_total = sum((o.amount for o in essential), Decimal("0"))
    for index, obligation in enumerate(
        sorted(relevant, key=lambda x: (x.next_due_date, x.obligation_id)), start=1
    ):
        days = (obligation.next_due_date - data.as_of).days
        priority = (
            "HIGH"
            if obligation.essential and days <= 7
            else "MEDIUM"
            if obligation.essential
            else "INFO"
        )
        timing = "overdue" if days < 0 else "due today" if days == 0 else f"due in {days} days"
        findings.append(
            PowerFinding(
                f"OBL-{index:03d}",
                "UPCOMING_RECURRING_OBLIGATION",
                priority,
                f"{obligation.payee_label} is {timing}",
                (
                    "This is the next recorded recurring due date, not a payment mandate "
                    "or a confirmation that the amount is still owed."
                ),
                (
                    "Confirm the bill and due date with the original provider; "
                    "review essential items before discretionary spending."
                ),
                obligation.amount,
                currency,
                (obligation.obligation_id,),
            )
        )

    if not findings:
        findings.append(
            PowerFinding(
                "BASE-001",
                "NO_HIGH_PRIORITY_SIGNAL",
                "INFO",
                "No high-priority signal found in this slice",
                (
                    "The selected records did not trigger the current deterministic review rules. "
                    "This is not a guarantee that no financial issue exists."
                ),
                (
                    "Keep records current and add relevant bills, "
                    "obligations, income or goals when useful."
                ),
                None,
                None,
                (),
            )
        )

    priority_order = {"HIGH": 0, "MEDIUM": 1, "INFO": 2}
    findings.sort(key=lambda x: (priority_order[x.priority], x.finding_id))
    return PersonalPowerReport(
        report_version="1.0.0",
        currency=currency,
        period_start=data.period_start,
        period_end=data.period_end,
        as_of=data.as_of,
        account_count=data.account_count,
        posted_transaction_count=data.posted_transaction_count,
        income_total=data.income_total,
        gross_expenses=data.gross_expenses,
        refunds=data.refunds,
        net_expenses_after_refunds=data.gross_expenses - data.refunds,
        essential_expenses=data.essential_expenses,
        discretionary_expenses=data.discretionary_expenses,
        net_cashflow=data.net_cashflow,
        upcoming_essential_obligations=essential_total,
        upcoming_obligation_count=len(relevant),
        potential_duplicate_count=len(data.duplicate_candidates),
        verified_value_created=Decimal("0"),
        findings=tuple(findings),
    )
