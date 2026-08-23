from dataclasses import dataclass
from decimal import Decimal

from models.enums import RoomStatus, RoomType


@dataclass
class Room:
    room_id: str
    number: str
    room_type: RoomType
    capacity: int
    nightly_rate: Decimal
    status: RoomStatus = RoomStatus.IN_SERVICE
