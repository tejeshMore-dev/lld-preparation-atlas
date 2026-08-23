from dataclasses import dataclass

from models.enums import SeatType


@dataclass(frozen=True)
class Seat:
    seat_id: str
    row: str
    number: int
    seat_type: SeatType
