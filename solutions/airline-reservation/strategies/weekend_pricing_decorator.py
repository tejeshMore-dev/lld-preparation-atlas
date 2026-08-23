from decimal import Decimal, InvalidOperation

from models.flight import Flight
from models.money import MoneyInput, to_money
from strategies.pricing_strategy import PricingStrategy


class WeekendPricingDecorator(PricingStrategy):
    """Adds a percentage to flights departing on Saturday or Sunday."""

    def __init__(self, wrapped: PricingStrategy, surcharge_percent: MoneyInput) -> None:
        self._wrapped = wrapped
        try:
            self._surcharge_percent = Decimal(str(surcharge_percent))
        except (InvalidOperation, ValueError) as error:
            raise ValueError("Weekend surcharge must be numeric") from error
        if not self._surcharge_percent.is_finite() or self._surcharge_percent < 0:
            raise ValueError("Weekend surcharge must be finite and non-negative")

    def calculate(self, flight: Flight, seat_ids: tuple[str, ...]) -> Decimal:
        base = self._wrapped.calculate(flight, seat_ids)
        if flight.departure_time.weekday() < 5:
            return base
        multiplier = Decimal("1") + self._surcharge_percent / Decimal("100")
        return to_money(base * multiplier)
