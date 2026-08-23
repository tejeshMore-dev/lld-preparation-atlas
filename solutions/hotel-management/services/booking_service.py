from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from threading import RLock
from uuid import uuid4

from models.booking import Booking
from models.charge import Charge
from models.enums import (
    BookingStatus,
    ChargeType,
    PaymentMethod,
    PaymentStatus,
    RoomStatus,
    RoomType,
)
from models.money import MoneyInput, to_money
from models.payment import Payment
from models.room_quote import RoomQuote
from services.catalog_service import CatalogService
from services.clock import Clock, SystemClock
from services.payment_gateway import PaymentGateway
from strategies.pricing_strategy import PricingStrategy


class BookingService:
    """Coordinates availability, reservation, payment, and stay lifecycles."""

    BLOCKING_STATUSES = {
        BookingStatus.PENDING_PAYMENT,
        BookingStatus.CONFIRMED,
        BookingStatus.CHECKED_IN,
    }

    def __init__(
        self,
        catalog: CatalogService,
        pricing_strategy: PricingStrategy,
        payment_gateway: PaymentGateway,
        clock: Clock | None = None,
        hold_duration: timedelta = timedelta(minutes=10),
    ) -> None:
        if hold_duration <= timedelta(0):
            raise ValueError("Hold duration must be positive")
        self._catalog = catalog
        self._pricing_strategy = pricing_strategy
        self._payment_gateway = payment_gateway
        self._clock = clock or SystemClock()
        self._hold_duration = hold_duration
        self._hotel_locks: defaultdict[str, RLock] = defaultdict(RLock)
        self.bookings: dict[str, Booking] = {}
        self.payments: dict[str, Payment] = {}

    def search_available_rooms(
        self,
        city: str,
        check_in_date: date,
        check_out_date: date,
        room_type: RoomType | None = None,
        minimum_capacity: int | None = None,
    ) -> list[RoomQuote]:
        self._validate_stay_dates(check_in_date, check_out_date)
        if check_in_date < self._clock.now().date():
            raise ValueError("Check-in date cannot be in the past")
        if minimum_capacity is not None and minimum_capacity <= 0:
            raise ValueError("Minimum capacity must be positive")

        quotes = []
        for hotel in self._catalog.search_hotels(city):
            with self._hotel_locks[hotel.hotel_id]:
                self._expire_stale_for_hotel(hotel.hotel_id, self._clock.now())
                for room in hotel.rooms.values():
                    if room.status is not RoomStatus.IN_SERVICE:
                        continue
                    if room_type is not None and room.room_type is not room_type:
                        continue
                    if minimum_capacity is not None and room.capacity < minimum_capacity:
                        continue
                    if not self._is_room_available(
                        hotel.hotel_id,
                        room.room_id,
                        check_in_date,
                        check_out_date,
                    ):
                        continue
                    quotes.append(
                        RoomQuote(
                            hotel_id=hotel.hotel_id,
                            hotel_name=hotel.name,
                            room_id=room.room_id,
                            room_number=room.number,
                            room_type=room.room_type,
                            capacity=room.capacity,
                            check_in_date=check_in_date,
                            check_out_date=check_out_date,
                            total_price=self._pricing_strategy.calculate(
                                room,
                                check_in_date,
                                check_out_date,
                            ),
                        )
                    )
        return sorted(quotes, key=lambda quote: (quote.total_price, quote.hotel_name, quote.room_number))

    def create_booking(
        self,
        guest_id: str,
        hotel_id: str,
        room_ids: list[str] | tuple[str, ...],
        check_in_date: date,
        check_out_date: date,
        guest_count: int,
    ) -> Booking:
        self._catalog.get_guest(guest_id)
        hotel = self._catalog.get_hotel(hotel_id)
        self._validate_stay_dates(check_in_date, check_out_date)
        if check_in_date < self._clock.now().date():
            raise ValueError("Check-in date cannot be in the past")
        if guest_count <= 0:
            raise ValueError("Guest count must be positive")
        selected_rooms = tuple(room_ids)
        if not selected_rooms:
            raise ValueError("At least one room must be selected")
        if len(set(selected_rooms)) != len(selected_rooms):
            raise ValueError("The same room cannot be selected more than once")

        with self._hotel_locks[hotel_id]:
            now = self._clock.now()
            self._expire_stale_for_hotel(hotel_id, now)
            rooms = [self._catalog.get_room(hotel_id, room_id) for room_id in selected_rooms]
            if sum(room.capacity for room in rooms) < guest_count:
                raise ValueError("Selected rooms do not have enough guest capacity")
            for room in rooms:
                if room.status is not RoomStatus.IN_SERVICE:
                    raise ValueError(f"Room '{room.room_id}' is out of service")
                if not self._is_room_available(
                    hotel_id,
                    room.room_id,
                    check_in_date,
                    check_out_date,
                ):
                    raise ValueError(f"Room '{room.room_id}' is not available for those dates")

            room_amount = sum(
                (
                    self._pricing_strategy.calculate(room, check_in_date, check_out_date)
                    for room in rooms
                ),
                Decimal("0"),
            )
            booking = Booking(
                booking_id=str(uuid4()),
                guest_id=guest_id,
                hotel_id=hotel_id,
                room_ids=selected_rooms,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                guest_count=guest_count,
                room_amount=to_money(room_amount),
                created_at=now,
                hold_expires_at=now + self._hold_duration,
            )
            self.bookings[booking.booking_id] = booking
            return booking

    def confirm_booking(self, booking_id: str, method: PaymentMethod) -> Payment:
        booking = self.get_booking(booking_id)
        with self._hotel_locks[booking.hotel_id]:
            now = self._clock.now()
            self._expire_stale_for_hotel(booking.hotel_id, now)
            if booking.status is BookingStatus.CONFIRMED:
                return self._latest_completed_payment(booking)
            if booking.status is not BookingStatus.PENDING_PAYMENT:
                raise ValueError(f"Booking cannot be confirmed in {booking.status.name} state")
            if now.date() > booking.check_in_date:
                booking.status = BookingStatus.EXPIRED
                raise ValueError("Cannot confirm after the check-in date")

            payment = self._record_charge(booking, booking.room_amount, method)
            if payment.status is PaymentStatus.COMPLETED:
                booking.status = BookingStatus.CONFIRMED
            return payment

    def cancel_booking(self, booking_id: str) -> Booking:
        booking = self.get_booking(booking_id)
        with self._hotel_locks[booking.hotel_id]:
            now = self._clock.now()
            self._expire_stale_for_hotel(booking.hotel_id, now)
            if booking.status is BookingStatus.CANCELLED:
                return booking
            if booking.status is BookingStatus.EXPIRED:
                raise ValueError("An expired booking cannot be cancelled")
            if booking.status in {BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT}:
                raise ValueError(f"Booking cannot be cancelled in {booking.status.name} state")
            if booking.status is BookingStatus.CONFIRMED:
                if now.date() >= booking.check_in_date:
                    raise ValueError("Confirmed bookings must be cancelled before check-in date")
                for payment_id in booking.payment_ids:
                    payment = self.payments[payment_id]
                    if payment.status is PaymentStatus.COMPLETED:
                        self._payment_gateway.refund(payment)
            booking.status = BookingStatus.CANCELLED
            return booking

    def check_in(self, booking_id: str) -> Booking:
        booking = self.get_booking(booking_id)
        with self._hotel_locks[booking.hotel_id]:
            now = self._clock.now()
            if booking.status is BookingStatus.CHECKED_IN:
                return booking
            if booking.status is not BookingStatus.CONFIRMED:
                raise ValueError("Only a confirmed booking can check in")
            if now.date() < booking.check_in_date:
                raise ValueError("Cannot check in before the arrival date")
            if now.date() >= booking.check_out_date:
                raise ValueError("The reservation has passed its check-out date")
            for room_id in booking.room_ids:
                room = self._catalog.get_room(booking.hotel_id, room_id)
                if room.status is not RoomStatus.IN_SERVICE:
                    raise ValueError(f"Room '{room_id}' is out of service")
            booking.status = BookingStatus.CHECKED_IN
            booking.checked_in_at = now
            return booking

    def add_charge(
        self,
        booking_id: str,
        charge_type: ChargeType,
        description: str,
        amount: MoneyInput,
    ) -> Charge:
        booking = self.get_booking(booking_id)
        normalized_amount = to_money(amount)
        if normalized_amount <= 0:
            raise ValueError("Charge amount must be positive")
        if not description.strip():
            raise ValueError("Charge description is required")
        with self._hotel_locks[booking.hotel_id]:
            if booking.status is not BookingStatus.CHECKED_IN:
                raise ValueError("Charges can be added only during an active stay")
            charge = Charge(
                charge_id=str(uuid4()),
                charge_type=charge_type,
                description=description.strip(),
                amount=normalized_amount,
                created_at=self._clock.now(),
            )
            booking.charges.append(charge)
            return charge

    def check_out(self, booking_id: str, method: PaymentMethod) -> Payment | None:
        booking = self.get_booking(booking_id)
        with self._hotel_locks[booking.hotel_id]:
            if booking.status is BookingStatus.CHECKED_OUT:
                return None
            if booking.status is not BookingStatus.CHECKED_IN:
                raise ValueError("Only a checked-in booking can check out")
            outstanding = self.get_outstanding_amount(booking_id)
            payment = None
            if outstanding > 0:
                payment = self._record_charge(booking, outstanding, method)
                if payment.status is not PaymentStatus.COMPLETED:
                    return payment
            booking.status = BookingStatus.CHECKED_OUT
            booking.checked_out_at = self._clock.now()
            return payment

    def get_outstanding_amount(self, booking_id: str) -> Decimal:
        booking = self.get_booking(booking_id)
        paid = sum(
            (
                self.payments[payment_id].amount
                for payment_id in booking.payment_ids
                if self.payments[payment_id].status is PaymentStatus.COMPLETED
            ),
            Decimal("0"),
        )
        return to_money(max(booking.total_amount - paid, Decimal("0")))

    def expire_stale_bookings(self, hotel_id: str | None = None) -> list[Booking]:
        now = self._clock.now()
        if hotel_id is not None:
            self._catalog.get_hotel(hotel_id)
            with self._hotel_locks[hotel_id]:
                return self._expire_stale_for_hotel(hotel_id, now)
        expired = []
        for current_hotel_id in list(self._catalog.hotels):
            with self._hotel_locks[current_hotel_id]:
                expired.extend(self._expire_stale_for_hotel(current_hotel_id, now))
        return expired

    def get_booking(self, booking_id: str) -> Booking:
        try:
            return self.bookings[booking_id]
        except KeyError as error:
            raise ValueError(f"Booking '{booking_id}' does not exist") from error

    def get_guest_bookings(self, guest_id: str) -> list[Booking]:
        self._catalog.get_guest(guest_id)
        return sorted(
            (booking for booking in list(self.bookings.values()) if booking.guest_id == guest_id),
            key=lambda booking: booking.created_at,
            reverse=True,
        )

    def _record_charge(
        self,
        booking: Booking,
        amount: Decimal,
        method: PaymentMethod,
    ) -> Payment:
        payment = self._payment_gateway.charge(booking.booking_id, amount, method)
        self.payments[payment.payment_id] = payment
        booking.payment_ids.append(payment.payment_id)
        return payment

    def _is_room_available(
        self,
        hotel_id: str,
        room_id: str,
        check_in_date: date,
        check_out_date: date,
    ) -> bool:
        for booking in list(self.bookings.values()):
            if booking.hotel_id != hotel_id or room_id not in booking.room_ids:
                continue
            if booking.status not in self.BLOCKING_STATUSES:
                continue
            overlaps = (
                check_in_date < booking.check_out_date
                and booking.check_in_date < check_out_date
            )
            if overlaps:
                return False
        return True

    def _expire_stale_for_hotel(self, hotel_id: str, now) -> list[Booking]:
        expired = []
        for booking in list(self.bookings.values()):
            if (
                booking.hotel_id == hotel_id
                and booking.status is BookingStatus.PENDING_PAYMENT
                and booking.hold_expires_at <= now
            ):
                booking.status = BookingStatus.EXPIRED
                expired.append(booking)
        return expired

    def _latest_completed_payment(self, booking: Booking) -> Payment:
        for payment_id in reversed(booking.payment_ids):
            payment = self.payments[payment_id]
            if payment.status is PaymentStatus.COMPLETED:
                return payment
        raise RuntimeError("Confirmed booking has no completed payment")

    @staticmethod
    def _validate_stay_dates(check_in_date: date, check_out_date: date) -> None:
        if check_out_date <= check_in_date:
            raise ValueError("Check-out date must be after check-in date")
