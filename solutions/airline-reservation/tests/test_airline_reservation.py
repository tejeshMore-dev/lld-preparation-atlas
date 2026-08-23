import threading
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from models.aircraft import Aircraft
from models.airline import Airline
from models.airport import Airport
from models.enums import (
    BookingStatus,
    CabinClass,
    FlightSeatStatus,
    FlightStatus,
    PaymentMethod,
    PaymentStatus,
)
from models.passenger import Passenger
from models.seat import Seat
from services.catalog_service import CatalogService
from services.clock import Clock
from services.in_memory_payment_gateway import InMemoryPaymentGateway
from services.reservation_service import ReservationService
from strategies.standard_pricing_strategy import StandardPricingStrategy
from strategies.weekend_pricing_decorator import WeekendPricingDecorator


class MutableClock(Clock):
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current

    def advance(self, **kwargs) -> None:
        self.current += timedelta(**kwargs)


class AirlineReservationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = MutableClock(datetime(2030, 1, 1, 10, 0))
        self.catalog = CatalogService()
        self.catalog.add_airport(Airport("BLR", "Kempegowda International", "Bengaluru", "Asia/Kolkata"))
        self.catalog.add_airport(Airport("DEL", "Indira Gandhi International", "Delhi", "Asia/Kolkata"))
        self.catalog.add_airport(Airport("BOM", "Mumbai International", "Mumbai", "Asia/Kolkata"))
        self.catalog.add_airline(Airline("a1", "Design Air", "DA"))

        aircraft = Aircraft("ac1", "Airbus A320", "VT-LLD")
        aircraft.add_seat(Seat("e1", "1A", CabinClass.ECONOMY))
        aircraft.add_seat(Seat("e2", "1B", CabinClass.ECONOMY))
        aircraft.add_seat(Seat("p1", "2A", CabinClass.PREMIUM_ECONOMY))
        aircraft.add_seat(Seat("b1", "3A", CabinClass.BUSINESS))
        self.catalog.add_aircraft("a1", aircraft)

        self.catalog.add_passenger(Passenger("pax1", "Asha", "asha@example.com", "P1001"))
        self.catalog.add_passenger(Passenger("pax2", "Ravi", "ravi@example.com", "P1002"))
        self.flight = self.catalog.create_flight(
            "f1",
            "DA101",
            "a1",
            "ac1",
            "BLR",
            "DEL",
            datetime(2030, 1, 5, 18, 0),
            datetime(2030, 1, 5, 21, 0),
            {
                CabinClass.ECONOMY: "5000",
                CabinClass.PREMIUM_ECONOMY: "7500",
                CabinClass.BUSINESS: "12000",
            },
            gate="A1",
        )
        self.gateway = InMemoryPaymentGateway(self.clock)
        self.service = ReservationService(
            self.catalog,
            StandardPricingStrategy(),
            self.gateway,
            self.clock,
            hold_duration=timedelta(minutes=10),
        )

    def create_booking(self, passenger_id: str = "pax1", seat_id: str = "e1"):
        return self.service.create_booking("f1", {passenger_id: seat_id})

    def test_search_returns_cabin_quotes_sorted_by_price(self) -> None:
        quotes = self.service.search_flights(
            "blr",
            "del",
            self.flight.departure_time.date(),
        )
        self.assertEqual(
            [CabinClass.ECONOMY, CabinClass.PREMIUM_ECONOMY, CabinClass.BUSINESS],
            [quote.cabin_class for quote in quotes],
        )
        self.assertEqual(Decimal("5000.00"), quotes[0].total_price)
        self.assertEqual(2, quotes[0].available_seats)

    def test_search_requires_enough_seats_for_all_passengers(self) -> None:
        quotes = self.service.search_flights(
            "BLR",
            "DEL",
            self.flight.departure_time.date(),
            passenger_count=2,
        )
        self.assertEqual([CabinClass.ECONOMY], [quote.cabin_class for quote in quotes])
        self.assertEqual(Decimal("10000.00"), quotes[0].total_price)

    def test_aircraft_schedule_overlap_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "overlaps"):
            self.catalog.create_flight(
                "f2",
                "DA102",
                "a1",
                "ac1",
                "DEL",
                "BOM",
                datetime(2030, 1, 5, 20, 0),
                datetime(2030, 1, 5, 23, 0),
                {cabin: "6000" for cabin in (CabinClass.ECONOMY, CabinClass.PREMIUM_ECONOMY, CabinClass.BUSINESS)},
            )

    def test_each_flight_has_independent_seat_inventory(self) -> None:
        next_flight = self.catalog.create_flight(
            "f2",
            "DA102",
            "a1",
            "ac1",
            "DEL",
            "BOM",
            self.flight.arrival_time,
            datetime(2030, 1, 6, 0, 30),
            {cabin: "6000" for cabin in (CabinClass.ECONOMY, CabinClass.PREMIUM_ECONOMY, CabinClass.BUSINESS)},
        )
        self.create_booking()
        self.assertIs(FlightSeatStatus.HELD, self.flight.seats["e1"].status)
        self.assertIs(FlightSeatStatus.AVAILABLE, next_flight.seats["e1"].status)

    def test_booking_assigns_passengers_holds_seats_and_prices_cabins(self) -> None:
        booking = self.service.create_booking("f1", {"pax1": "e1", "pax2": "b1"})
        self.assertEqual(Decimal("17000.00"), booking.total_amount)
        self.assertEqual(("pax1", "pax2"), booking.passenger_ids)
        self.assertEqual(("e1", "b1"), booking.seat_ids)
        self.assertIs(FlightSeatStatus.HELD, self.flight.seats["b1"].status)

    def test_duplicate_or_held_seat_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "same seat"):
            self.service.create_booking("f1", {"pax1": "e1", "pax2": "e1"})
        self.create_booking()
        with self.assertRaisesRegex(ValueError, "no longer available"):
            self.create_booking("pax2", "e1")

    def test_expired_hold_releases_seat(self) -> None:
        booking = self.create_booking()
        self.clock.advance(minutes=10)
        seats = self.service.get_available_seats("f1")
        self.assertIs(BookingStatus.EXPIRED, booking.status)
        self.assertIn("e1", [seat.seat_id for seat in seats])

    def test_successful_confirmation_is_idempotent(self) -> None:
        booking = self.create_booking()
        first = self.service.confirm_booking(booking.booking_id, PaymentMethod.UPI)
        second = self.service.confirm_booking(booking.booking_id, PaymentMethod.UPI)
        self.assertIs(first, second)
        self.assertIs(BookingStatus.CONFIRMED, booking.status)
        self.assertIs(FlightSeatStatus.BOOKED, self.flight.seats["e1"].status)
        self.assertEqual(1, len(booking.payment_ids))

    def test_failed_payment_can_be_retried_before_expiry(self) -> None:
        booking = self.create_booking()
        self.gateway.fail_next_charge = True
        failed = self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        self.assertIs(PaymentStatus.FAILED, failed.status)
        self.assertIs(BookingStatus.PENDING_PAYMENT, booking.status)
        successful = self.service.confirm_booking(booking.booking_id, PaymentMethod.WALLET)
        self.assertIs(PaymentStatus.COMPLETED, successful.status)
        self.assertEqual(2, len(booking.payment_ids))

    def test_pending_and_confirmed_cancellation_release_seats(self) -> None:
        pending = self.create_booking(seat_id="e1")
        self.service.cancel_booking(pending.booking_id)
        self.assertIs(BookingStatus.CANCELLED, pending.status)
        confirmed = self.create_booking(seat_id="e2")
        payment = self.service.confirm_booking(confirmed.booking_id, PaymentMethod.CARD)
        self.service.cancel_booking(confirmed.booking_id)
        self.assertIs(PaymentStatus.REFUNDED, payment.status)
        self.assertIs(FlightSeatStatus.AVAILABLE, self.flight.seats["e2"].status)

    def test_check_in_window_and_boarding_pass_generation(self) -> None:
        booking = self.create_booking()
        self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        with self.assertRaisesRegex(ValueError, "not opened"):
            self.service.check_in(booking.booking_id)
        self.clock.current = self.flight.departure_time - timedelta(hours=23)
        passes = self.service.check_in(booking.booking_id)
        self.assertEqual(1, len(passes))
        self.assertEqual("1A", passes[0].seat_number)
        self.assertEqual("A1", passes[0].gate)
        self.assertIs(BookingStatus.CHECKED_IN, booking.status)
        self.assertIs(FlightSeatStatus.CHECKED_IN, self.flight.seats["e1"].status)

    def test_check_in_closes_at_deadline(self) -> None:
        booking = self.create_booking()
        self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        self.clock.current = self.flight.departure_time - timedelta(minutes=45)
        with self.assertRaisesRegex(ValueError, "closed"):
            self.service.check_in(booking.booking_id)

    def test_board_depart_and_arrive_state_sequence(self) -> None:
        booking = self.create_booking()
        self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        self.clock.current = self.flight.departure_time - timedelta(hours=1)
        self.service.check_in(booking.booking_id)
        self.clock.current = self.flight.departure_time - timedelta(minutes=30)
        self.service.start_boarding("f1")
        self.service.board_booking(booking.booking_id)
        self.assertIs(BookingStatus.BOARDED, booking.status)
        self.assertIs(FlightSeatStatus.BOARDED, self.flight.seats["e1"].status)
        self.clock.current = self.flight.departure_time
        self.service.depart_flight("f1")
        self.assertIs(FlightStatus.DEPARTED, self.flight.status)
        self.clock.current = self.flight.arrival_time
        self.service.arrive_flight("f1")
        self.assertIs(FlightStatus.ARRIVED, self.flight.status)

    def test_cannot_board_without_check_in(self) -> None:
        booking = self.create_booking()
        self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        self.clock.current = self.flight.departure_time - timedelta(minutes=30)
        self.service.start_boarding("f1")
        with self.assertRaisesRegex(ValueError, "checked-in"):
            self.service.board_booking(booking.booking_id)

    def test_airline_cancellation_refunds_and_cancels_active_bookings(self) -> None:
        confirmed = self.create_booking("pax1", "e1")
        payment = self.service.confirm_booking(confirmed.booking_id, PaymentMethod.CARD)
        pending = self.create_booking("pax2", "e2")
        affected = self.service.cancel_flight("f1")
        self.assertEqual({confirmed.booking_id, pending.booking_id}, {item.booking_id for item in affected})
        self.assertIs(FlightStatus.CANCELLED, self.flight.status)
        self.assertIs(PaymentStatus.REFUNDED, payment.status)
        self.assertTrue(all(item.status is BookingStatus.CANCELLED for item in affected))
        self.assertTrue(all(seat.status is FlightSeatStatus.AVAILABLE for seat in self.flight.seats.values()))

    def test_weekend_pricing_decorator(self) -> None:
        weekend_service = ReservationService(
            self.catalog,
            WeekendPricingDecorator(StandardPricingStrategy(), "25"),
            self.gateway,
            self.clock,
        )
        booking = weekend_service.create_booking("f1", {"pax1": "e1"})
        self.assertEqual(Decimal("6250.00"), booking.total_amount)

    def test_passenger_history_is_newest_first(self) -> None:
        first = self.create_booking("pax1", "e1")
        self.clock.advance(seconds=1)
        second = self.create_booking("pax1", "e2")
        self.assertEqual([second, first], self.service.get_passenger_bookings("pax1"))

    def test_concurrent_requests_for_same_seat_have_one_winner(self) -> None:
        barrier = threading.Barrier(2)
        winners = []
        failures = []

        def attempt(passenger_id: str) -> None:
            barrier.wait()
            try:
                winners.append(self.create_booking(passenger_id, "e1"))
            except ValueError as error:
                failures.append(str(error))

        threads = [
            threading.Thread(target=attempt, args=("pax1",)),
            threading.Thread(target=attempt, args=("pax2",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(1, len(winners))
        self.assertEqual(1, len(failures))


if __name__ == "__main__":
    unittest.main()
