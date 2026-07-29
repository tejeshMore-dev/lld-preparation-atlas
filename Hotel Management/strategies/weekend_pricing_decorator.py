from datetime import date
from decimal import Decimal, InvalidOperation

from models.money import MoneyInput, to_money
from models.room import Room
from strategies.pricing_strategy import PricingStrategy


class WeekendPricingDecorator(PricingStrategy):
    """Adds a percentage surcharge to Saturday and Sunday nights."""

    def __init__(self, wrapped: PricingStrategy, surcharge_percent: MoneyInput) -> None:
        self._wrapped = wrapped
        try:
            self._surcharge_percent = Decimal(str(surcharge_percent))
        except (InvalidOperation, ValueError) as error:
            raise ValueError("Weekend surcharge must be numeric") from error
        if not self._surcharge_percent.is_finite() or self._surcharge_percent < 0:
            raise ValueError("Weekend surcharge must be finite and non-negative")

    def price_for_night(self, room: Room, stay_date: date) -> Decimal:
        base = self._wrapped.price_for_night(room, stay_date)
        if stay_date.weekday() < 5:
            return base
        multiplier = Decimal("1") + self._surcharge_percent / Decimal("100")
        return to_money(base * multiplier)
