"""Money helpers for Decimal arithmetic with consistent rounding."""

from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Union

NumberLike = Union[str, float, int, Decimal]

MONEY = Decimal("0.01")

# Ensure enough precision for intermediate operations
getcontext().prec = 28


def to_decimal(value: NumberLike) -> Decimal:
    """Convert arbitrary input to Decimal without losing precision."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def q(value: NumberLike) -> Decimal:
    """Quantize a numeric value to two decimal places with ROUND_HALF_UP."""
    return to_decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)
