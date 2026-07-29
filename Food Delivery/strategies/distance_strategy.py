from abc import ABC, abstractmethod
from decimal import Decimal

from models.location import Location


class DistanceStrategy(ABC):
    @abstractmethod
    def calculate_km(self, start: Location, end: Location) -> Decimal:
        raise NotImplementedError
