from dataclasses import dataclass
from datetime import datetime

from models.enums import PaymentStatus, PaymentMethod

@dataclass
class Receipt:
    receipt_id: str
    ticket_id: str
    status: PaymentStatus
    payment_method: PaymentMethod
    amount: float
    date: datetime

    def __str__(self):
        return (
            f"\n"
            f"========== RECEIPT ==========\n"
            f"Receipt ID     : {self.receipt_id}\n"
            f"Ticket ID      : {self.ticket_id}\n"
            f"Amount Paid    : ₹{self.amount:.2f}\n"
            f"Payment Method : {self.payment_method.name}\n"
            f"Status         : {self.status.name}\n"
            f"Paid At        : {self.date:%d-%m-%Y %H:%M:%S}\n"
            f"============================="
        )