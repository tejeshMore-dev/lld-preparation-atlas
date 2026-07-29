from abc import ABC, abstractmethod
from decimal import Decimal

from models.enums import PaymentMethod
from models.payment import Payment


class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, ride_id: str, amount: Decimal, method: PaymentMethod) -> Payment:
        raise NotImplementedError
