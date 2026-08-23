from dataclasses import dataclass
from datetime import datetime

from models.enums import Direction, RequestStatus


@dataclass
class HallRequest:
    request_id: str
    floor: int
    direction: Direction
    created_at: datetime
    status: RequestStatus = RequestStatus.PENDING
    assigned_elevator_id: str | None = None


@dataclass
class CarRequest:
    request_id: str
    elevator_id: str
    destination_floor: int
    created_at: datetime
    status: RequestStatus = RequestStatus.ASSIGNED
