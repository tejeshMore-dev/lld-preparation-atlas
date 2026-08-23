from decimal import Decimal

from models.money import MoneyInput, to_money
from strategies.discount_strategy import DiscountStrategy


class FixedAmountDiscount(DiscountStrategy):
    def __init__(self, amount: MoneyInput) -> None:
        self._amount = to_money(amount)
        if self._amount <= 0:
            raise ValueError("Fixed discount must be positive")

    def calculate_discount(self, order_amount: Decimal) -> Decimal:
        if order_amount < 0:
            raise ValueError("Order amount cannot be negative")
        return to_money(min(self._amount, order_amount))
