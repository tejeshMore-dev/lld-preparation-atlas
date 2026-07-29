from abc import ABC, abstractmethod
from decimal import Decimal

from models.show import Show


class PricingStrategy(ABC):
    """Calculates the price of selected seats for a particular show."""

    @abstractmethod
    def calculate(self, show: Show, seat_ids: tuple[str, ...]) -> Decimal:
        raise NotImplementedError
