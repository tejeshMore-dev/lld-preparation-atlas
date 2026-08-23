from abc import ABC, abstractmethod
from decimal import Decimal


class DiscountStrategy(ABC):
    @abstractmethod
    def calculate_discount(self, order_amount: Decimal) -> Decimal:
        raise NotImplementedError
