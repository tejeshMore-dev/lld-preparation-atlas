from decimal import Decimal, InvalidOperation

from models.money import MoneyInput, to_money
from strategies.discount_strategy import DiscountStrategy


class PercentageDiscount(DiscountStrategy):
    def __init__(
        self,
        percentage: MoneyInput,
        maximum_discount: MoneyInput | None = None,
    ) -> None:
        try:
            self._percentage = Decimal(str(percentage))
        except (InvalidOperation, ValueError) as error:
            raise ValueError("Discount percentage must be numeric") from error
        if not self._percentage.is_finite() or self._percentage <= 0 or self._percentage > 100:
            raise ValueError("Discount percentage must be greater than 0 and at most 100")
        self._maximum_discount = (
            None if maximum_discount is None else to_money(maximum_discount)
        )
        if self._maximum_discount is not None and self._maximum_discount <= 0:
            raise ValueError("Maximum discount must be positive")

    def calculate_discount(self, order_amount: Decimal) -> Decimal:
        if order_amount < 0:
            raise ValueError("Order amount cannot be negative")
        discount = to_money(order_amount * self._percentage / Decimal("100"))
        if self._maximum_discount is not None:
            discount = min(discount, self._maximum_discount)
        return to_money(discount)
