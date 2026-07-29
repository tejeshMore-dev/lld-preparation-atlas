from decimal import Decimal, InvalidOperation

from models.enums import VehicleType
from models.money import MoneyInput, to_money
from strategies.fare_strategy import FareStrategy


class SurgePricingDecorator(FareStrategy):
    def __init__(self, wrapped: FareStrategy, multiplier: MoneyInput) -> None:
        self._wrapped = wrapped
        try:
            self._multiplier = Decimal(str(multiplier))
        except (InvalidOperation, ValueError) as error:
            raise ValueError("Surge multiplier must be numeric") from error
        if not self._multiplier.is_finite() or self._multiplier < 1:
            raise ValueError("Surge multiplier must be finite and at least 1")

    def calculate(
        self,
        vehicle_type: VehicleType,
        distance_km: Decimal,
        duration_minutes: Decimal,
    ) -> Decimal:
        return to_money(
            self._wrapped.calculate(vehicle_type, distance_km, duration_minutes)
            * self._multiplier
        )
