from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from models.enums import RoomType


@dataclass(frozen=True)
class RoomQuote:
    hotel_id: str
    hotel_name: str
    room_id: str
    room_number: str
    room_type: RoomType
    capacity: int
    check_in_date: date
    check_out_date: date
    total_price: Decimal
