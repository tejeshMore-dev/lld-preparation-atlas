from decimal import Decimal, InvalidOperation

from models.money import MoneyInput, to_money
from models.show import Show
from strategies.pricing_strategy import PricingStrategy


class WeekendPricingDecorator(PricingStrategy):
    """Adds a configurable percentage surcharge on Saturday and Sunday."""

    def __init__(self, wrapped: PricingStrategy, surcharge_percent: MoneyInput) -> None:
        self._wrapped = wrapped
        try:
            self._surcharge_percent = Decimal(str(surcharge_percent))
        except (InvalidOperation, ValueError) as error:
            raise ValueError("Weekend surcharge must be numeric") from error
        if not self._surcharge_percent.is_finite() or self._surcharge_percent < 0:
            raise ValueError("Weekend surcharge must be a finite, non-negative number")

    def calculate(self, show: Show, seat_ids: tuple[str, ...]) -> Decimal:
        base_price = self._wrapped.calculate(show, seat_ids)
        if show.start_time.weekday() < 5:
            return base_price
        multiplier = Decimal("1") + self._surcharge_percent / Decimal("100")
        return to_money(base_price * multiplier)
