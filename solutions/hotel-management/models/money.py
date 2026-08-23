from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import TypeAlias


MoneyInput: TypeAlias = Decimal | int | float | str
CENT = Decimal("0.01")


def to_money(value: MoneyInput) -> Decimal:
    try:
        amount = Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"Invalid monetary value: {value}") from error
    if not amount.is_finite():
        raise ValueError("Money must be finite")
    return amount
