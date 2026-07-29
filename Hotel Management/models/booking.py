from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from models.charge import Charge
from models.enums import BookingStatus
from models.money import to_money


@dataclass
class Booking:
    booking_id: str
    guest_id: str
    hotel_id: str
    room_ids: tuple[str, ...]
    check_in_date: date
    check_out_date: date
    guest_count: int
    room_amount: Decimal
    created_at: datetime
    hold_expires_at: datetime
    status: BookingStatus = BookingStatus.PENDING_PAYMENT
    charges: list[Charge] = field(default_factory=list)
    payment_ids: list[str] = field(default_factory=list)
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None

    @property
    def nights(self) -> int:
        return (self.check_out_date - self.check_in_date).days

    @property
    def total_amount(self) -> Decimal:
        return to_money(self.room_amount + sum((charge.amount for charge in self.charges), Decimal("0")))
