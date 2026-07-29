from datetime import datetime, timedelta

from models.aircraft import Aircraft
from models.airline import Airline
from models.airport import Airport
from models.enums import CabinClass, PaymentMethod
from models.passenger import Passenger
from models.seat import Seat
from services.catalog_service import CatalogService
from services.clock import Clock
from services.in_memory_payment_gateway import InMemoryPaymentGateway
from services.reservation_service import ReservationService
from strategies.standard_pricing_strategy import StandardPricingStrategy


class DemoClock(Clock):
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current


def build_demo() -> tuple[CatalogService, ReservationService, DemoClock]:
    clock = DemoClock(datetime.now())
    catalog = CatalogService()
    catalog.add_airport(Airport("BLR", "Kempegowda International", "Bengaluru", "Asia/Kolkata"))
    catalog.add_airport(Airport("DEL", "Indira Gandhi International", "Delhi", "Asia/Kolkata"))
    catalog.add_airline(Airline("airline-1", "Design Air", "DA"))

    aircraft = Aircraft("aircraft-1", "Airbus A320", "VT-LLD")
    aircraft.add_seat(Seat("1A", "1A", CabinClass.ECONOMY))
    aircraft.add_seat(Seat("1B", "1B", CabinClass.ECONOMY))
    aircraft.add_seat(Seat("2A", "2A", CabinClass.PREMIUM_ECONOMY))
    aircraft.add_seat(Seat("3A", "3A", CabinClass.BUSINESS))
    catalog.add_aircraft("airline-1", aircraft)
    catalog.add_passenger(Passenger("passenger-1", "Asha", "asha@example.com", "P1001"))

    departure = clock.now() + timedelta(days=2)
    catalog.create_flight(
        "flight-1",
        "DA101",
        "airline-1",
        "aircraft-1",
        "BLR",
        "DEL",
        departure,
        departure + timedelta(hours=3),
        {
            CabinClass.ECONOMY: "5200",
            CabinClass.PREMIUM_ECONOMY: "7600",
            CabinClass.BUSINESS: "12500",
        },
        gate="A1",
    )
    service = ReservationService(
        catalog,
        StandardPricingStrategy(),
        InMemoryPaymentGateway(clock),
        clock,
    )
    return catalog, service, clock


def main() -> None:
    catalog, service, clock = build_demo()
    flight = catalog.get_flight("flight-1")
    quotes = service.search_flights("BLR", "DEL", flight.departure_time.date())
    print(f"Found {flight.flight_number}: {flight.origin_code} -> {flight.destination_code}")
    for quote in quotes:
        print(f"  {quote.cabin_class.name}: Rs. {quote.total_price}")

    booking = service.create_booking("flight-1", {"passenger-1": "1A"})
    payment = service.confirm_booking(booking.booking_id, PaymentMethod.UPI)
    print(f"Booking {booking.status.name}; payment {payment.status.name}")

    clock.current = flight.departure_time - timedelta(hours=23)
    boarding_pass = service.check_in(booking.booking_id)[0]
    print(f"Boarding pass: seat {boarding_pass.seat_number}, gate {boarding_pass.gate}")
    clock.current = flight.departure_time - timedelta(minutes=30)
    service.start_boarding(flight.flight_id)
    service.board_booking(booking.booking_id)
    print(f"Flight {flight.status.name}; booking {booking.status.name}")
    clock.current = flight.departure_time
    service.depart_flight(flight.flight_id)
    clock.current = flight.arrival_time
    service.arrive_flight(flight.flight_id)
    print(f"Flight completed with status {flight.status.name}")


if __name__ == "__main__":
    main()
