from dataclasses import dataclass
from decimal import Decimal

from models.enums import VehicleType
from models.money import MoneyInput, to_money
from strategies.fare_strategy import FareStrategy


@dataclass(frozen=True)
class FareRule:
    base_fare: Decimal
    per_km: Decimal
    per_minute: Decimal
    minimum_fare: Decimal


class StandardFareStrategy(FareStrategy):
    DEFAULT_RULES = {
        VehicleType.MINI: ("40", "12", "1.5", "80"),
        VehicleType.SEDAN: ("60", "16", "2", "120"),
        VehicleType.SUV: ("90", "22", "2.5", "180"),
    }

    def __init__(
        self,
        rules: dict[VehicleType, tuple[MoneyInput, MoneyInput, MoneyInput, MoneyInput]] | None = None,
    ) -> None:
        source = rules or self.DEFAULT_RULES
        self._rules = {
            vehicle_type: FareRule(*(to_money(value) for value in values))
            for vehicle_type, values in source.items()
        }
        for rule in self._rules.values():
            if min(rule.base_fare, rule.per_km, rule.per_minute, rule.minimum_fare) < 0:
                raise ValueError("Fare rule values cannot be negative")

    def calculate(
        self,
        vehicle_type: VehicleType,
        distance_km: Decimal,
        duration_minutes: Decimal,
    ) -> Decimal:
        if distance_km < 0 or duration_minutes < 0:
            raise ValueError("Distance and duration cannot be negative")
        try:
            rule = self._rules[vehicle_type]
        except KeyError as error:
            raise ValueError(f"No fare rule configured for {vehicle_type.name}") from error
        calculated = (
            rule.base_fare
            + rule.per_km * distance_km
            + rule.per_minute * duration_minutes
        )
        return to_money(max(calculated, rule.minimum_fare))
