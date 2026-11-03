"""Currency precision and safe decimal arithmetic primitives."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

# ISO 4217 minor-unit exponents for the initial pilot and common international currencies.
# Add currencies only after checking the current ISO 4217 maintenance data.
CURRENCY_EXPONENTS: dict[str, int] = {
    "AED": 2,
    "AUD": 2,
    "BHD": 3,
    "CAD": 2,
    "CHF": 2,
    "EUR": 2,
    "GBP": 2,
    "INR": 2,
    "JPY": 0,
    "KWD": 3,
    "OMR": 3,
    "QAR": 2,
    "SAR": 2,
    "SGD": 2,
    "USD": 2,
}


class MoneyInputError(ValueError):
    """Raised when an amount cannot be represented in the currency's minor unit."""


def currency_exponent(currency: str) -> int:
    normalized = currency.upper()
    try:
        return CURRENCY_EXPONENTS[normalized]
    except KeyError as exc:
        raise MoneyInputError(f"Unsupported currency: {normalized}") from exc


def quantize_amount(amount: Decimal, currency: str) -> Decimal:
    """Validate and normalize an amount without silently losing precision."""
    if not amount.is_finite():
        raise MoneyInputError("Amount must be finite")
    exponent = currency_exponent(currency)
    quantum = Decimal(1).scaleb(-exponent)
    try:
        normalized = amount.quantize(quantum, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise MoneyInputError("Amount is outside the supported numeric range") from exc
    if normalized != amount:
        raise MoneyInputError(
            f"Amount has more than {exponent} decimal places for {currency.upper()}"
        )
    if normalized <= 0:
        raise MoneyInputError("Amount must be greater than zero")
    return normalized


def quantize_total(amount: Decimal, currency: str) -> Decimal:
    """Quantize a calculated total using the currency's minor-unit precision."""
    quantum = Decimal(1).scaleb(-currency_exponent(currency))
    return amount.quantize(quantum, rounding=ROUND_HALF_UP)
