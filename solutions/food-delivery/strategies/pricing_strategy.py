from abc import ABC, abstractmethod
from decimal import Decimal

from models.price_breakdown import PriceBreakdown


class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, subtotal: Decimal, delivery_distance_km: Decimal) -> PriceBreakdown:
        raise NotImplementedError
