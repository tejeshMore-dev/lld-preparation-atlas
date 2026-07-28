from abc import ABC, abstractmethod
from datetime import datetime
import uuid

from models.receipt import Receipt
from models.enums import PaymentStatus, PaymentMethod


class PaymentProcessor(ABC):
    @abstractmethod
    def pay(self, amount: float, payment_method: PaymentMethod) -> Receipt:
        raise NotImplementedError


class UPIPaymentProcessor(PaymentProcessor):
    def pay(self, amount: float, payment_method: PaymentMethod) -> Receipt:
        if payment_method != PaymentMethod.UPI:
            raise ValueError("UPIPaymentProcessor only supports UPI payments")
        if amount < 0:
            raise ValueError("Payment amount cannot be negative")

        return Receipt(
            receipt_id=str(uuid.uuid4()),
            ticket_id="",
            amount=amount,
            payment_method=payment_method,
            status=PaymentStatus.COMPLETED,
            date=datetime.now(),
        )
