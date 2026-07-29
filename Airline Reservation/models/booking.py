from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from models.enums import BookingStatus


@dataclass(frozen=True)
class SeatAssignment:
    passenger_id: str
    seat_id: str


@dataclass
class Booking:
    booking_id: str
    flight_id: str
    assignments: tuple[SeatAssignment, ...]
    total_amount: Decimal
    created_at: datetime
    hold_expires_at: datetime
    status: BookingStatus = BookingStatus.PENDING_PAYMENT
    payment_ids: list[str] = field(default_factory=list)
    boarding_pass_ids: list[str] = field(default_factory=list)
    checked_in_at: datetime | None = None
    boarded_at: datetime | None = None

    @property
    def passenger_ids(self) -> tuple[str, ...]:
        return tuple(assignment.passenger_id for assignment in self.assignments)

    @property
    def seat_ids(self) -> tuple[str, ...]:
        return tuple(assignment.seat_id for assignment in self.assignments)
