from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from models.enums import CabinClass


@dataclass(frozen=True)
class FlightQuote:
    flight_id: str
    flight_number: str
    airline_name: str
    origin_code: str
    destination_code: str
    departure_time: datetime
    arrival_time: datetime
    cabin_class: CabinClass
    passenger_count: int
    available_seats: int
    total_price: Decimal
