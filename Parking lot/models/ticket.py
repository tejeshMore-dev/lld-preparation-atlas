from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from models.vehicle import Vehicle
from models.enums import TicketStatus
from models.parking_spots import ParkingSpot


@dataclass
class Ticket:
    ticket_id: str
    vehicle: Vehicle
    spot: ParkingSpot
    entry_time: datetime
    status: TicketStatus = TicketStatus.ACTIVE
    exit_time: Optional[datetime] = None