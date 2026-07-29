from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from models.enums import PaymentMethod, PaymentStatus


@dataclass
class Payment:
    payment_id: str
    ride_id: str
    amount: Decimal
    method: PaymentMethod
    status: PaymentStatus
    created_at: datetime
    failure_reason: str | None = None
