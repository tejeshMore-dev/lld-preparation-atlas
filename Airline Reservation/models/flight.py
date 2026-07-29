from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from models.enums import CabinClass, FlightSeatStatus, FlightStatus
from models.seat import Seat


@dataclass
class FlightSeat:
    seat: Seat
    status: FlightSeatStatus = FlightSeatStatus.AVAILABLE
    booking_id: str | None = None
    held_until: datetime | None = None


@dataclass
class Flight:
    flight_id: str
    flight_number: str
    airline_id: str
    aircraft_id: str
    origin_code: str
    destination_code: str
    departure_time: datetime
    arrival_time: datetime
    prices: dict[CabinClass, Decimal]
    seats: dict[str, FlightSeat]
    gate: str | None = None
    status: FlightStatus = FlightStatus.SCHEDULED
