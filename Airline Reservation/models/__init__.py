"""Domain models for the airline reservation solution."""

from .aircraft import Aircraft
from .airline import Airline
from .airport import Airport
from .boarding_pass import BoardingPass
from .booking import Booking, SeatAssignment
from .enums import (
    BookingStatus,
    CabinClass,
    FlightSeatStatus,
    FlightStatus,
    PaymentMethod,
    PaymentStatus,
)
from .flight import Flight, FlightSeat
from .flight_quote import FlightQuote
from .passenger import Passenger
from .payment import Payment
from .seat import Seat

__all__ = [
    "Aircraft",
    "Airline",
    "Airport",
    "BoardingPass",
    "Booking",
    "BookingStatus",
    "CabinClass",
    "Flight",
    "FlightQuote",
    "FlightSeat",
    "FlightSeatStatus",
    "FlightStatus",
    "Passenger",
    "Payment",
    "PaymentMethod",
    "PaymentStatus",
    "Seat",
    "SeatAssignment",
]
