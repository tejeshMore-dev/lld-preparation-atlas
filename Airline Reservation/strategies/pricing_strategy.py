from abc import ABC, abstractmethod
from decimal import Decimal

from models.flight import Flight


class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, flight: Flight, seat_ids: tuple[str, ...]) -> Decimal:
        raise NotImplementedError
