from abc import ABC, abstractmethod
from decimal import Decimal

from models.enums import VehicleType


class FareStrategy(ABC):
    @abstractmethod
    def calculate(
        self,
        vehicle_type: VehicleType,
        distance_km: Decimal,
        duration_minutes: Decimal,
    ) -> Decimal:
        raise NotImplementedError
