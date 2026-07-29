import threading
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from models.enums import (
    BookingStatus,
    ChargeType,
    PaymentMethod,
    PaymentStatus,
    RoomStatus,
    RoomType,
)
from models.guest import Guest
from models.hotel import Hotel
from models.room import Room
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


class HotelManagementTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = MutableClock(datetime(2030, 1, 1, 10, 0))
        self.catalog = CatalogService()
        self.catalog.add_guest(Guest("g1", "Asha", "asha@example.com", "9000000001"))
        self.catalog.add_guest(Guest("g2", "Ravi", "ravi@example.com", "9000000002"))
        self.catalog.add_hotel(Hotel("h1", "Design Inn", "Bengaluru", "1 Pattern Road"))
        self.catalog.add_room("h1", Room("r101", "101", RoomType.STANDARD, 2, "1000"))
        self.catalog.add_room("h1", Room("r102", "102", RoomType.STANDARD, 2, "1000"))
        self.catalog.add_room("h1", Room("r201", "201", RoomType.DELUXE, 3, "1800"))
        self.catalog.add_room("h1", Room("r301", "301", RoomType.SUITE, 4, "3000"))
        self.gateway = InMemoryPaymentGateway(self.clock)
        self.service = BookingService(
            self.catalog,
            StandardPricingStrategy(),
            self.gateway,
            self.clock,
            timedelta(minutes=10),
        )
        self.arrival = date(2030, 1, 10)
        self.departure = date(2030, 1, 12)

    def create_booking(self, guest_id: str = "g1", room_id: str = "r101"):
        return self.service.create_booking(
            guest_id,
            "h1",
            [room_id],
            self.arrival,
            self.departure,
            2,
        )

    def test_catalog_search_and_room_quote(self) -> None:
        quotes = self.service.search_available_rooms(
            "bEnGaLuRu",
            self.arrival,
            self.departure,
            RoomType.STANDARD,
            2,
        )
        self.assertEqual(["r101", "r102"], [quote.room_id for quote in quotes])
        self.assertTrue(all(quote.total_price == Decimal("2000.00") for quote in quotes))

    def test_invalid_date_range_and_past_arrival_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "after check-in"):
            self.service.search_available_rooms("Bengaluru", self.arrival, self.arrival)
        with self.assertRaisesRegex(ValueError, "past"):
            self.service.search_available_rooms(
                "Bengaluru",
                date(2029, 12, 31),
                date(2030, 1, 2),
            )

    def test_booking_holds_room_and_calculates_nights(self) -> None:
        booking = self.create_booking()
        self.assertEqual(2, booking.nights)
        self.assertEqual(Decimal("2000.00"), booking.room_amount)
        self.assertIs(BookingStatus.PENDING_PAYMENT, booking.status)
        room_ids = [
            quote.room_id
            for quote in self.service.search_available_rooms(
                "Bengaluru", self.arrival, self.departure
            )
        ]
        self.assertNotIn("r101", room_ids)

    def test_selected_rooms_must_have_enough_capacity(self) -> None:
        with self.assertRaisesRegex(ValueError, "capacity"):
            self.service.create_booking(
                "g1", "h1", ["r101"], self.arrival, self.departure, 3
            )

    def test_out_of_service_room_is_not_searchable_or_bookable(self) -> None:
        self.catalog.set_room_status("h1", "r101", RoomStatus.OUT_OF_SERVICE)
        available = self.service.search_available_rooms(
            "Bengaluru", self.arrival, self.departure
        )
        self.assertNotIn("r101", [quote.room_id for quote in available])
        with self.assertRaisesRegex(ValueError, "out of service"):
            self.create_booking()

    def test_overlapping_stay_is_rejected_but_adjacent_stay_is_allowed(self) -> None:
        self.create_booking()
        with self.assertRaisesRegex(ValueError, "not available"):
            self.service.create_booking(
                "g2",
                "h1",
                ["r101"],
                date(2030, 1, 11),
                date(2030, 1, 13),
                1,
            )
        adjacent = self.service.create_booking(
            "g2",
            "h1",
            ["r101"],
            self.departure,
            date(2030, 1, 14),
            1,
        )
        self.assertIs(BookingStatus.PENDING_PAYMENT, adjacent.status)

    def test_expired_hold_releases_room(self) -> None:
        booking = self.create_booking()
        self.clock.advance(minutes=10)
        quotes = self.service.search_available_rooms(
            "Bengaluru", self.arrival, self.departure
        )
        self.assertIs(BookingStatus.EXPIRED, booking.status)
        self.assertIn("r101", [quote.room_id for quote in quotes])

    def test_payment_confirmation_is_idempotent(self) -> None:
        booking = self.create_booking()
        first = self.service.confirm_booking(booking.booking_id, PaymentMethod.UPI)
        second = self.service.confirm_booking(booking.booking_id, PaymentMethod.UPI)
        self.assertIs(PaymentStatus.COMPLETED, first.status)
        self.assertIs(first, second)
        self.assertIs(BookingStatus.CONFIRMED, booking.status)
        self.assertEqual(1, len(booking.payment_ids))

    def test_failed_payment_can_be_retried_during_hold(self) -> None:
        booking = self.create_booking()
        self.gateway.fail_next_charge = True
        failed = self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        self.assertIs(PaymentStatus.FAILED, failed.status)
        self.assertIs(BookingStatus.PENDING_PAYMENT, booking.status)
        completed = self.service.confirm_booking(booking.booking_id, PaymentMethod.UPI)
        self.assertIs(PaymentStatus.COMPLETED, completed.status)
        self.assertEqual(2, len(booking.payment_ids))

    def test_pending_cancellation_releases_without_payment(self) -> None:
        booking = self.create_booking()
        self.service.cancel_booking(booking.booking_id)
        self.assertIs(BookingStatus.CANCELLED, booking.status)
        self.assertEqual([], booking.payment_ids)
        quotes = self.service.search_available_rooms(
            "Bengaluru", self.arrival, self.departure
        )
        self.assertIn("r101", [quote.room_id for quote in quotes])

    def test_confirmed_cancellation_refunds_payment(self) -> None:
        booking = self.create_booking()
        payment = self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        self.service.cancel_booking(booking.booking_id)
        self.assertIs(BookingStatus.CANCELLED, booking.status)
        self.assertIs(PaymentStatus.REFUNDED, payment.status)

    def test_early_check_in_is_rejected_then_arrival_check_in_succeeds(self) -> None:
        booking = self.create_booking()
        self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        with self.assertRaisesRegex(ValueError, "before the arrival"):
            self.service.check_in(booking.booking_id)
        self.clock.current = datetime(2030, 1, 10, 14, 0)
        self.service.check_in(booking.booking_id)
        self.assertIs(BookingStatus.CHECKED_IN, booking.status)
        self.assertEqual(self.clock.now(), booking.checked_in_at)

    def test_confirmed_booking_cannot_cancel_on_arrival_date(self) -> None:
        booking = self.create_booking()
        self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        self.clock.current = datetime(2030, 1, 10, 9, 0)
        with self.assertRaisesRegex(ValueError, "before check-in"):
            self.service.cancel_booking(booking.booking_id)

    def test_stay_charges_and_checkout_payment_retry(self) -> None:
        booking = self.create_booking()
        self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        self.clock.current = datetime(2030, 1, 10, 14, 0)
        self.service.check_in(booking.booking_id)
        self.service.add_charge(
            booking.booking_id,
            ChargeType.ROOM_SERVICE,
            "Dinner",
            "350",
        )
        self.assertEqual(Decimal("2350.00"), booking.total_amount)
        self.assertEqual(Decimal("350.00"), self.service.get_outstanding_amount(booking.booking_id))

        self.gateway.fail_next_charge = True
        failed = self.service.check_out(booking.booking_id, PaymentMethod.CARD)
        self.assertIs(PaymentStatus.FAILED, failed.status)
        self.assertIs(BookingStatus.CHECKED_IN, booking.status)
        successful = self.service.check_out(booking.booking_id, PaymentMethod.UPI)
        self.assertIs(PaymentStatus.COMPLETED, successful.status)
        self.assertIs(BookingStatus.CHECKED_OUT, booking.status)
        self.assertEqual(Decimal("0.00"), self.service.get_outstanding_amount(booking.booking_id))

    def test_checkout_without_extra_charges_needs_no_second_payment(self) -> None:
        booking = self.create_booking()
        self.service.confirm_booking(booking.booking_id, PaymentMethod.CARD)
        self.clock.current = datetime(2030, 1, 10, 14, 0)
        self.service.check_in(booking.booking_id)
        payment = self.service.check_out(booking.booking_id, PaymentMethod.CASH)
        self.assertIsNone(payment)
        self.assertIs(BookingStatus.CHECKED_OUT, booking.status)
        self.assertEqual(1, len(booking.payment_ids))

    def test_weekend_surcharge_is_applied_per_night(self) -> None:
        weekend_service = BookingService(
            self.catalog,
            WeekendPricingDecorator(StandardPricingStrategy(), "25"),
            self.gateway,
            self.clock,
        )
        booking = weekend_service.create_booking(
            "g1",
            "h1",
            ["r101"],
            date(2030, 1, 4),
            date(2030, 1, 7),
            2,
        )
        self.assertEqual(Decimal("3500.00"), booking.room_amount)

    def test_guest_history_is_newest_first(self) -> None:
        first = self.create_booking(room_id="r101")
        self.clock.advance(seconds=1)
        second = self.create_booking(room_id="r102")
        self.assertEqual([second, first], self.service.get_guest_bookings("g1"))

    def test_concurrent_requests_for_same_room_have_one_winner(self) -> None:
        barrier = threading.Barrier(2)
        winners = []
        failures = []

        def attempt(guest_id: str) -> None:
            barrier.wait()
            try:
                winners.append(
                    self.service.create_booking(
                        guest_id,
                        "h1",
                        ["r101"],
                        self.arrival,
                        self.departure,
                        1,
                    )
                )
            except ValueError as error:
                failures.append(str(error))

        threads = [
            threading.Thread(target=attempt, args=("g1",)),
            threading.Thread(target=attempt, args=("g2",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(1, len(winners))
        self.assertEqual(1, len(failures))


if __name__ == "__main__":
    unittest.main()
