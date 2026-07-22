from abc import ABC, abstractmethod
from datetime import datetime
import uuid

from models.receipt import Receipt
from models.ticket import Ticket
from models.enums import PaymentStatus, PaymentMethod

class PaymentProcessor(ABC):

    @abstractmethod
    def pay(self, amount: float, payment_method: PaymentMethod) -> Receipt:
        pass


class UPIPaymentProcessor(PaymentProcessor):

    def pay(self, amount: float, payment_method: PaymentMethod) -> Receipt:
        # Implement UPI payment logic here
        # For demonstration, we'll just return a dummy receipt
        return Receipt(
            receipt_id=str(uuid.uuid4()),
            ticket_id="", 
            amount=amount, 
            payment_method=payment_method.name, 
            status= PaymentStatus.COMPLETED.name,
            date=datetime.now()
            )