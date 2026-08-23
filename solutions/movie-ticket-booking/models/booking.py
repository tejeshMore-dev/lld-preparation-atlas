from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from models.enums import BookingStatus


@dataclass
class Booking:
    booking_id: str
    user_id: str
    show_id: str
    seat_ids: tuple[str, ...]
    total_amount: Decimal
    created_at: datetime
    hold_expires_at: datetime
    status: BookingStatus = BookingStatus.PENDING_PAYMENT
    payment_ids: list[str] = field(default_factory=list)
