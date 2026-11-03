from datetime import date
from decimal import Decimal

import pytest

from myeconomy.domain.cashflow import CashflowEntry, analyze_cashflow

PERIOD_START = date(2026, 11, 1)
PERIOD_END = date(2026, 11, 30)


def test_cashflow_totals_and_expense_categories() -> None:
    result = analyze_cashflow(
        currency="INR",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        incomes=[
            CashflowEntry(date(2026, 11, 1), Decimal("50000.00"), "salary"),
        ],
        expenses=[
            CashflowEntry(date(2026, 11, 3), Decimal("18000.00"), "rent", True),
            CashflowEntry(date(2026, 11, 4), Decimal("6000.00"), "groceries", True),
            CashflowEntry(date(2026, 11, 5), Decimal("4000.00"), "transport", False),
        ],
    )

    assert result.income_total == Decimal("50000.00")
    assert result.expense_total == Decimal("28000.00")
    assert result.net_cashflow == Decimal("22000.00")
    assert result.essential_expenses == Decimal("24000.00")
    assert result.discretionary_expenses == Decimal("4000.00")
    assert result.savings_rate_percent == Decimal("44.00")
    assert [item.category for item in result.expense_by_category] == [
        "rent",
        "groceries",
        "transport",
    ]


def test_zero_income_has_no_savings_rate_and_can_show_deficit() -> None:
    result = analyze_cashflow(
        currency="INR",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        incomes=[],
        expenses=[
            CashflowEntry(date(2026, 11, 8), Decimal("100.00"), "medicine", True),
        ],
    )
    assert result.net_cashflow == Decimal("-100.00")
    assert result.savings_rate_percent is None


def test_entry_outside_period_is_rejected() -> None:
    with pytest.raises(ValueError, match="outside the requested period"):
        analyze_cashflow(
            currency="INR",
            period_start=PERIOD_START,
            period_end=PERIOD_END,
            incomes=[
                CashflowEntry(date(2026, 12, 1), Decimal("100.00"), "salary"),
            ],
            expenses=[],
        )


def test_currency_minor_units_are_respected() -> None:
    result = analyze_cashflow(
        currency="JPY",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        incomes=[CashflowEntry(date(2026, 11, 1), Decimal("1000"), "salary")],
        expenses=[CashflowEntry(date(2026, 11, 2), Decimal("200"), "food", True)],
    )
    assert result.net_cashflow == Decimal("800")


def test_amount_with_excess_currency_precision_is_rejected() -> None:
    with pytest.raises(ValueError, match="decimal places"):
        analyze_cashflow(
            currency="INR",
            period_start=PERIOD_START,
            period_end=PERIOD_END,
            incomes=[CashflowEntry(date(2026, 11, 1), Decimal("10.001"), "salary")],
            expenses=[],
        )


def test_three_decimal_currency_is_supported() -> None:
    result = analyze_cashflow(
        currency="KWD",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        incomes=[CashflowEntry(date(2026, 11, 1), Decimal("10.125"), "salary")],
        expenses=[CashflowEntry(date(2026, 11, 2), Decimal("1.125"), "food", True)],
    )
    assert result.net_cashflow == Decimal("9.000")
