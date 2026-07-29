import threading
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from models.enums import (
    BookingStatus,
    PaymentMethod,
    PaymentStatus,
    SeatType,
    ShowSeatStatus,
)
from models.movie import Movie
from models.screen import Screen
from models.seat import Seat
from models.theatre import Theatre
from models.user import User
from services.booking_service import BookingService
from services.catalog_service import CatalogService
from services.clock import Clock
from services.in_memory_payment_gateway import InMemoryPaymentGateway
from strategies.standard_pricing_strategy import StandardPricingStrategy
from strategies.weekend_pricing_decorator import WeekendPricingDecorator


class MutableClock(Clock):
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current

    def advance(self, **kwargs) -> None:
        self.current += timedelta(**kwargs)


class MovieTicketBookingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = MutableClock(datetime(2030, 1, 1, 10, 0))
        self.catalog = CatalogService()
        self.catalog.add_user(User("u1", "Asha", "asha@example.com"))
        self.catalog.add_user(User("u2", "Ravi", "ravi@example.com"))
        self.catalog.add_movie(Movie("m1", "Design Patterns", 120, "English", "Drama", "U"))

        screen = Screen("s1", "Audi 1")
        screen.add_seat(Seat("A1", "A", 1, SeatType.REGULAR))
        screen.add_seat(Seat("A2", "A", 2, SeatType.REGULAR))
        screen.add_seat(Seat("B1", "B", 1, SeatType.PREMIUM))
        screen.add_seat(Seat("C1", "C", 1, SeatType.RECLINER))
        theatre = Theatre("t1", "Cine Design", "Bengaluru")
        theatre.add_screen(screen)
        self.catalog.add_theatre(theatre)

        self.show = self.catalog.create_show(
            "show1",
            "m1",
            "t1",
            "s1",
            datetime(2030, 1, 2, 18, 0),
            {
                SeatType.REGULAR: "200",
                SeatType.PREMIUM: "300",
                SeatType.RECLINER: "500",
            },
        )
        self.gateway = InMemoryPaymentGateway(self.clock)
        self.service = BookingService(
            self.catalog,
            StandardPricingStrategy(),
            self.gateway,
            self.clock,
            timedelta(minutes=5),
        )

    def test_search_filters_by_city_movie_and_date(self) -> None:
        result = self.catalog.search_shows("bEnGaLuRu", "m1", self.show.start_time.date())
        self.assertEqual([self.show], result)
        self.assertEqual([], self.catalog.search_shows("Mumbai"))

    def test_overlapping_show_on_same_screen_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "overlaps"):
            self.catalog.create_show(
                "show2",
                "m1",
                "t1",
                "s1",
                datetime(2030, 1, 2, 19, 0),
                {seat_type: "250" for seat_type in SeatType},
            )

    def test_touching_show_times_are_allowed(self) -> None:
        next_show = self.catalog.create_show(
            "show2",
            "m1",
            "t1",
            "s1",
            self.show.end_time,
            {seat_type: "250" for seat_type in SeatType},
        )
        self.assertEqual(self.show.end_time, next_show.start_time)

    def test_each_show_has_independent_seat_inventory(self) -> None:
        next_show = self.catalog.create_show(
            "show2",
            "m1",
            "t1",
            "s1",
            self.show.end_time,
            {seat_type: "250" for seat_type in SeatType},
        )
        self.service.create_booking("u1", "show1", ["A1"])
        self.assertIs(ShowSeatStatus.HELD, self.show.seats["A1"].status)
        self.assertIs(ShowSeatStatus.AVAILABLE, next_show.seats["A1"].status)

    def test_booking_holds_seats_and_calculates_exact_total(self) -> None:
        booking = self.service.create_booking("u1", "show1", ["A1", "B1"])
        self.assertEqual(Decimal("500.00"), booking.total_amount)
        self.assertEqual(self.clock.now() + timedelta(minutes=5), booking.hold_expires_at)
        self.assertIs(ShowSeatStatus.HELD, self.show.seats["A1"].status)

    def test_duplicate_or_already_held_seat_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "same seat"):
            self.service.create_booking("u1", "show1", ["A1", "A1"])
        self.service.create_booking("u1", "show1", ["A1"])
        with self.assertRaisesRegex(ValueError, "no longer available"):
            self.service.create_booking("u2", "show1", ["A1"])

    def test_expired_hold_releases_seat(self) -> None:
        booking = self.service.create_booking("u1", "show1", ["A1"])
        self.clock.advance(minutes=5)
        available = self.service.get_available_seats("show1")
        self.assertIs(BookingStatus.EXPIRED, booking.status)
        self.assertIn("A1", [seat.seat_id for seat in available])

    def test_hold_never_extends_beyond_show_start(self) -> None:
        self.clock.current = self.show.start_time - timedelta(minutes=2)
        booking = self.service.create_booking("u1", "show1", ["A1"])
        self.assertEqual(self.show.start_time, booking.hold_expires_at)
        self.clock.current = self.show.start_time
        self.service.expire_stale_bookings("show1")
        self.assertIs(BookingStatus.EXPIRED, booking.status)

    def test_successful_payment_confirms_booking(self) -> None:
        booking = self.service.create_booking("u1", "show1", ["C1"])
        payment = self.service.confirm_booking(booking.booking_id, PaymentMethod.UPI)
        self.assertIs(PaymentStatus.COMPLETED, payment.status)
        self.assertIs(BookingStatus.CONFIRMED, booking.status)
        self.assertIs(ShowSeatStatus.BOOKED, self.show.seats["C1"].status)

    def test_confirmation_is_idempotent(self) -> None:
        booking = self.service.create_booking("u1", "show1", ["A1"])
        first = self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        second = self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        self.assertIs(first, second)
        self.assertEqual(1, len(booking.payment_ids))

    def test_failed_payment_can_be_retried_before_hold_expires(self) -> None:
        booking = self.service.create_booking("u1", "show1", ["A1"])
        self.gateway.fail_next_charge = True
        failed = self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        self.assertIs(PaymentStatus.FAILED, failed.status)
        self.assertIs(BookingStatus.PENDING_PAYMENT, booking.status)
        successful = self.service.confirm_booking(booking.booking_id, PaymentMethod.UPI)
        self.assertIs(PaymentStatus.COMPLETED, successful.status)
        self.assertIs(BookingStatus.CONFIRMED, booking.status)
        self.assertEqual(2, len(booking.payment_ids))

    def test_pending_booking_can_be_cancelled_without_refund(self) -> None:
        booking = self.service.create_booking("u1", "show1", ["A1"])
        self.service.cancel_booking(booking.booking_id)
        self.assertIs(BookingStatus.CANCELLED, booking.status)
        self.assertIs(ShowSeatStatus.AVAILABLE, self.show.seats["A1"].status)

    def test_confirmed_booking_cancellation_refunds_and_releases(self) -> None:
        booking = self.service.create_booking("u1", "show1", ["B1"])
        payment = self.service.confirm_booking(booking.booking_id, PaymentMethod.WALLET)
        self.service.cancel_booking(booking.booking_id)
        self.assertIs(BookingStatus.CANCELLED, booking.status)
        self.assertIs(PaymentStatus.REFUNDED, payment.status)
        self.assertIs(ShowSeatStatus.AVAILABLE, self.show.seats["B1"].status)

    def test_booking_and_cancellation_are_blocked_after_show_starts(self) -> None:
        booking = self.service.create_booking("u1", "show1", ["A1"])
        self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        self.clock.current = self.show.start_time
        with self.assertRaisesRegex(ValueError, "Cannot cancel"):
            self.service.cancel_booking(booking.booking_id)
        with self.assertRaisesRegex(ValueError, "already started"):
            self.service.create_booking("u2", "show1", ["A2"])

    def test_weekend_pricing_decorator(self) -> None:
        saturday_show = self.catalog.create_show(
            "weekend",
            "m1",
            "t1",
            "s1",
            datetime(2030, 1, 5, 18, 0),
            {seat_type: "200" for seat_type in SeatType},
        )
        weekend_service = BookingService(
            self.catalog,
            WeekendPricingDecorator(StandardPricingStrategy(), "25"),
            self.gateway,
            self.clock,
        )
        booking = weekend_service.create_booking("u1", saturday_show.show_id, ["A1"])
        self.assertEqual(Decimal("250.00"), booking.total_amount)

    def test_user_booking_history_is_newest_first(self) -> None:
        first = self.service.create_booking("u1", "show1", ["A1"])
        self.clock.advance(seconds=1)
        second = self.service.create_booking("u1", "show1", ["A2"])
        self.assertEqual([second, first], self.service.get_user_bookings("u1"))

    def test_concurrent_requests_allow_only_one_winner(self) -> None:
        barrier = threading.Barrier(2)
        winners = []
        failures = []

        def attempt(user_id: str) -> None:
            barrier.wait()
            try:
                winners.append(self.service.create_booking(user_id, "show1", ["A1"]))
            except ValueError as error:
                failures.append(str(error))

        threads = [
            threading.Thread(target=attempt, args=("u1",)),
            threading.Thread(target=attempt, args=("u2",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(1, len(winners))
        self.assertEqual(1, len(failures))
        self.assertIs(ShowSeatStatus.HELD, self.show.seats["A1"].status)


if __name__ == "__main__":
    unittest.main()
