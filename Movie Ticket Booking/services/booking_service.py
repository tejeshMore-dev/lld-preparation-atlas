from collections import defaultdict
from datetime import timedelta
from threading import RLock
from uuid import uuid4

from models.booking import Booking
from models.enums import BookingStatus, PaymentMethod, PaymentStatus, ShowSeatStatus
from models.payment import Payment
from models.seat import Seat
from services.catalog_service import CatalogService
from services.clock import Clock, SystemClock
from services.payment_gateway import PaymentGateway
from strategies.pricing_strategy import PricingStrategy


class BookingService:
    """Coordinates seat holds, payments, confirmation, expiry, and cancellation."""

    def __init__(
        self,
        catalog: CatalogService,
        pricing_strategy: PricingStrategy,
        payment_gateway: PaymentGateway,
        clock: Clock | None = None,
        hold_duration: timedelta = timedelta(minutes=5),
    ) -> None:
        if hold_duration <= timedelta(0):
            raise ValueError("Hold duration must be positive")
        self._catalog = catalog
        self._pricing_strategy = pricing_strategy
        self._payment_gateway = payment_gateway
        self._clock = clock or SystemClock()
        self._hold_duration = hold_duration
        self._show_locks: defaultdict[str, RLock] = defaultdict(RLock)
        self.bookings: dict[str, Booking] = {}
        self.payments: dict[str, Payment] = {}

    def create_booking(
        self,
        user_id: str,
        show_id: str,
        seat_ids: list[str] | tuple[str, ...],
    ) -> Booking:
        self._catalog.get_user(user_id)
        show = self._catalog.get_show(show_id)
        requested_seats = tuple(seat_ids)
        if not requested_seats:
            raise ValueError("At least one seat must be selected")
        if len(set(requested_seats)) != len(requested_seats):
            raise ValueError("The same seat cannot be selected more than once")

        with self._show_locks[show_id]:
            now = self._clock.now()
            self._expire_stale_for_show(show_id, now)
            if now >= show.start_time:
                raise ValueError("Cannot book a show that has already started")

            for seat_id in requested_seats:
                show_seat = show.seats.get(seat_id)
                if show_seat is None:
                    raise ValueError(f"Seat '{seat_id}' does not exist in this show")
                if show_seat.status is not ShowSeatStatus.AVAILABLE:
                    raise ValueError(f"Seat '{seat_id}' is no longer available")

            booking = Booking(
                booking_id=str(uuid4()),
                user_id=user_id,
                show_id=show_id,
                seat_ids=requested_seats,
                total_amount=self._pricing_strategy.calculate(show, requested_seats),
                created_at=now,
                hold_expires_at=min(now + self._hold_duration, show.start_time),
            )
            for seat_id in requested_seats:
                show_seat = show.seats[seat_id]
                show_seat.status = ShowSeatStatus.HELD
                show_seat.held_by_booking_id = booking.booking_id
                show_seat.held_until = booking.hold_expires_at
            self.bookings[booking.booking_id] = booking
            return booking

    def confirm_booking(
        self,
        booking_id: str,
        method: PaymentMethod,
    ) -> Payment:
        booking = self.get_booking(booking_id)
        show = self._catalog.get_show(booking.show_id)
        with self._show_locks[booking.show_id]:
            now = self._clock.now()
            self._expire_stale_for_show(booking.show_id, now)

            if booking.status is BookingStatus.CONFIRMED:
                return self._completed_payment_for(booking)
            if booking.status is not BookingStatus.PENDING_PAYMENT:
                raise ValueError(f"Booking cannot be paid in {booking.status.name} state")
            if now >= show.start_time:
                self._release_seats(booking)
                booking.status = BookingStatus.EXPIRED
                raise ValueError("Cannot pay after the show has started")

            payment = self._payment_gateway.charge(
                booking.booking_id,
                booking.total_amount,
                method,
            )
            self.payments[payment.payment_id] = payment
            booking.payment_ids.append(payment.payment_id)

            if payment.status is PaymentStatus.COMPLETED:
                for seat_id in booking.seat_ids:
                    show_seat = show.seats[seat_id]
                    if show_seat.held_by_booking_id != booking.booking_id:
                        raise RuntimeError("Booking no longer owns all selected seat holds")
                    show_seat.status = ShowSeatStatus.BOOKED
                    show_seat.held_until = None
                booking.status = BookingStatus.CONFIRMED
            return payment

    def cancel_booking(self, booking_id: str) -> Booking:
        booking = self.get_booking(booking_id)
        show = self._catalog.get_show(booking.show_id)
        with self._show_locks[booking.show_id]:
            now = self._clock.now()
            self._expire_stale_for_show(booking.show_id, now)

            if booking.status is BookingStatus.CANCELLED:
                return booking
            if booking.status is BookingStatus.EXPIRED:
                raise ValueError("An expired booking cannot be cancelled")
            if now >= show.start_time:
                raise ValueError("Cannot cancel after the show has started")

            if booking.status is BookingStatus.CONFIRMED:
                payment = self._completed_payment_for(booking)
                self._payment_gateway.refund(payment)

            self._release_seats(booking)
            booking.status = BookingStatus.CANCELLED
            return booking

    def expire_stale_bookings(self, show_id: str | None = None) -> list[Booking]:
        """Expires unpaid holds. A scheduler could call this periodically in production."""
        now = self._clock.now()
        if show_id is not None:
            self._catalog.get_show(show_id)
            with self._show_locks[show_id]:
                return self._expire_stale_for_show(show_id, now)

        expired = []
        for current_show_id in list(self._catalog.shows):
            with self._show_locks[current_show_id]:
                expired.extend(self._expire_stale_for_show(current_show_id, now))
        return expired

    def get_available_seats(self, show_id: str) -> list[Seat]:
        show = self._catalog.get_show(show_id)
        with self._show_locks[show_id]:
            self._expire_stale_for_show(show_id, self._clock.now())
            seats = [
                show_seat.seat
                for show_seat in show.seats.values()
                if show_seat.status is ShowSeatStatus.AVAILABLE
            ]
            return sorted(seats, key=lambda seat: (seat.row, seat.number))

    def get_booking(self, booking_id: str) -> Booking:
        try:
            return self.bookings[booking_id]
        except KeyError as error:
            raise ValueError(f"Booking '{booking_id}' does not exist") from error

    def get_user_bookings(self, user_id: str) -> list[Booking]:
        self._catalog.get_user(user_id)
        return sorted(
            (booking for booking in self.bookings.values() if booking.user_id == user_id),
            key=lambda booking: booking.created_at,
            reverse=True,
        )

    def _expire_stale_for_show(self, show_id: str, now) -> list[Booking]:
        expired = []
        # Snapshot the values because another show has a different lock and may
        # add a booking concurrently.
        for booking in list(self.bookings.values()):
            if (
                booking.show_id == show_id
                and booking.status is BookingStatus.PENDING_PAYMENT
                and booking.hold_expires_at <= now
            ):
                self._release_seats(booking)
                booking.status = BookingStatus.EXPIRED
                expired.append(booking)
        return expired

    def _release_seats(self, booking: Booking) -> None:
        show = self._catalog.get_show(booking.show_id)
        for seat_id in booking.seat_ids:
            show_seat = show.seats[seat_id]
            if show_seat.held_by_booking_id == booking.booking_id:
                show_seat.status = ShowSeatStatus.AVAILABLE
                show_seat.held_by_booking_id = None
                show_seat.held_until = None

    def _completed_payment_for(self, booking: Booking) -> Payment:
        for payment_id in reversed(booking.payment_ids):
            payment = self.payments[payment_id]
            if payment.status is PaymentStatus.COMPLETED:
                return payment
        raise RuntimeError("Confirmed booking has no completed payment")
