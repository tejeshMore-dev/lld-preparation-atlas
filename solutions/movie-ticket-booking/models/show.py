from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from models.enums import SeatType, ShowSeatStatus
from models.seat import Seat


@dataclass
class ShowSeat:
    seat: Seat
    status: ShowSeatStatus = ShowSeatStatus.AVAILABLE
    held_by_booking_id: str | None = None
    held_until: datetime | None = None


@dataclass
class Show:
    show_id: str
    movie_id: str
    theatre_id: str
    screen_id: str
    start_time: datetime
    end_time: datetime
    prices: dict[SeatType, Decimal]
    seats: dict[str, ShowSeat]
