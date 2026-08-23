from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BoardingPass:
    boarding_pass_id: str
    booking_id: str
    passenger_id: str
    flight_id: str
    seat_number: str
    gate: str
    issued_at: datetime
