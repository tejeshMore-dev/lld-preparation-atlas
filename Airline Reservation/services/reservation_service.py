from collections import defaultdict
from datetime import date, timedelta
from threading import RLock
from uuid import uuid4

from models.boarding_pass import BoardingPass
from models.booking import Booking, SeatAssignment
from models.enums import (
    BookingStatus,
    CabinClass,
    FlightSeatStatus,
    FlightStatus,
    PaymentMethod,
    PaymentStatus,
)
from models.flight_quote import FlightQuote
from models.payment import Payment
from models.seat import Seat
from services.catalog_service import CatalogService
from services.clock import Clock, SystemClock
from services.payment_gateway import PaymentGateway
from strategies.pricing_strategy import PricingStrategy


class ReservationService:
    """Coordinates flight inventory, booking, payment, check-in, and boarding."""

    def __init__(
        self,
        catalog: CatalogService,
        pricing_strategy: PricingStrategy,
        payment_gateway: PaymentGateway,
        clock: Clock | None = None,
        hold_duration: timedelta = timedelta(minutes=10),
        check_in_opens_before: timedelta = timedelta(hours=24),
        check_in_closes_before: timedelta = timedelta(minutes=45),
        boarding_opens_before: timedelta = timedelta(minutes=45),
    ) -> None:
        if hold_duration <= timedelta(0):
            raise ValueError("Hold duration must be positive")
        if check_in_opens_before <= check_in_closes_before:
            raise ValueError("Check-in opening must be earlier than its closing deadline")
        if check_in_closes_before < timedelta(0) or boarding_opens_before <= timedelta(0):
            raise ValueError("Flight timing windows must be positive")
        self._catalog = catalog
        self._pricing_strategy = pricing_strategy
        self._payment_gateway = payment_gateway
        self._clock = clock or SystemClock()
        self._hold_duration = hold_duration
        self._check_in_opens_before = check_in_opens_before
        self._check_in_closes_before = check_in_closes_before
        self._boarding_opens_before = boarding_opens_before
        self._flight_locks: defaultdict[str, RLock] = defaultdict(RLock)
        self.bookings: dict[str, Booking] = {}
        self.payments: dict[str, Payment] = {}
        self.boarding_passes: dict[str, BoardingPass] = {}

    def search_flights(
        self,
        origin_code: str,
        destination_code: str,
        departure_date: date,
        passenger_count: int = 1,
        cabin_class: CabinClass | None = None,
    ) -> list[FlightQuote]:
        if passenger_count <= 0:
            raise ValueError("Passenger count must be positive")
        if departure_date < self._clock.now().date():
            raise ValueError("Departure date cannot be in the past")
        self._catalog.get_airport(origin_code)
        self._catalog.get_airport(destination_code)

        quotes = []
        for flight in self._catalog.find_flights(
            origin_code,
            destination_code,
            departure_date,
        ):
            with self._flight_locks[flight.flight_id]:
                now = self._clock.now()
                self._expire_stale_for_flight(flight.flight_id, now)
                if now >= flight.departure_time:
                    continue
                cabins = [cabin_class] if cabin_class is not None else list(CabinClass)
                for current_cabin in cabins:
                    available_ids = [
                        seat_id
                        for seat_id, flight_seat in flight.seats.items()
                        if flight_seat.status is FlightSeatStatus.AVAILABLE
                        and flight_seat.seat.cabin_class is current_cabin
                    ]
                    if len(available_ids) < passenger_count:
                        continue
                    quoted_ids = tuple(available_ids[:passenger_count])
                    airline = self._catalog.get_airline(flight.airline_id)
                    quotes.append(
                        FlightQuote(
                            flight_id=flight.flight_id,
                            flight_number=flight.flight_number,
                            airline_name=airline.name,
                            origin_code=flight.origin_code,
                            destination_code=flight.destination_code,
                            departure_time=flight.departure_time,
                            arrival_time=flight.arrival_time,
                            cabin_class=current_cabin,
                            passenger_count=passenger_count,
                            available_seats=len(available_ids),
                            total_price=self._pricing_strategy.calculate(
                                flight,
                                quoted_ids,
                            ),
                        )
                    )
        return sorted(quotes, key=lambda quote: (quote.total_price, quote.departure_time))

    def create_booking(
        self,
        flight_id: str,
        passenger_seats: dict[str, str],
    ) -> Booking:
        flight = self._catalog.get_flight(flight_id)
        if not passenger_seats:
            raise ValueError("At least one passenger and seat are required")
        if len(set(passenger_seats.values())) != len(passenger_seats):
            raise ValueError("The same seat cannot be assigned more than once")
        for passenger_id in passenger_seats:
            self._catalog.get_passenger(passenger_id)

        with self._flight_locks[flight_id]:
            now = self._clock.now()
            self._expire_stale_for_flight(flight_id, now)
            if flight.status is not FlightStatus.SCHEDULED:
                raise ValueError(f"Cannot book a flight in {flight.status.name} state")
            if now >= flight.departure_time:
                raise ValueError("Cannot book a flight that has departed")

            assignments = tuple(
                SeatAssignment(passenger_id, seat_id)
                for passenger_id, seat_id in passenger_seats.items()
            )
            for assignment in assignments:
                flight_seat = flight.seats.get(assignment.seat_id)
                if flight_seat is None:
                    raise ValueError(f"Seat '{assignment.seat_id}' does not exist on this flight")
                if flight_seat.status is not FlightSeatStatus.AVAILABLE:
                    raise ValueError(f"Seat '{assignment.seat_id}' is no longer available")

            booking = Booking(
                booking_id=str(uuid4()),
                flight_id=flight_id,
                assignments=assignments,
                total_amount=self._pricing_strategy.calculate(
                    flight,
                    tuple(assignment.seat_id for assignment in assignments),
                ),
                created_at=now,
                hold_expires_at=min(now + self._hold_duration, flight.departure_time),
            )
            for assignment in assignments:
                flight_seat = flight.seats[assignment.seat_id]
                flight_seat.status = FlightSeatStatus.HELD
                flight_seat.booking_id = booking.booking_id
                flight_seat.held_until = booking.hold_expires_at
            self.bookings[booking.booking_id] = booking
            return booking

    def confirm_booking(self, booking_id: str, method: PaymentMethod) -> Payment:
        booking = self.get_booking(booking_id)
        flight = self._catalog.get_flight(booking.flight_id)
        with self._flight_locks[booking.flight_id]:
            now = self._clock.now()
            self._expire_stale_for_flight(booking.flight_id, now)
            if booking.status is BookingStatus.CONFIRMED:
                return self._completed_payment_for(booking)
            if booking.status is not BookingStatus.PENDING_PAYMENT:
                raise ValueError(f"Booking cannot be paid in {booking.status.name} state")
            if now >= flight.departure_time or flight.status is not FlightStatus.SCHEDULED:
                self._release_seats(booking)
                booking.status = BookingStatus.EXPIRED
                raise ValueError("Flight is no longer open for payment")

            payment = self._payment_gateway.charge(
                booking.booking_id,
                booking.total_amount,
                method,
            )
            self.payments[payment.payment_id] = payment
            booking.payment_ids.append(payment.payment_id)
            if payment.status is PaymentStatus.COMPLETED:
                for seat_id in booking.seat_ids:
                    flight_seat = flight.seats[seat_id]
                    if flight_seat.booking_id != booking.booking_id:
                        raise RuntimeError("Booking no longer owns all selected seat holds")
                    flight_seat.status = FlightSeatStatus.BOOKED
                    flight_seat.held_until = None
                booking.status = BookingStatus.CONFIRMED
            return payment

    def cancel_booking(self, booking_id: str) -> Booking:
        booking = self.get_booking(booking_id)
        flight = self._catalog.get_flight(booking.flight_id)
        with self._flight_locks[booking.flight_id]:
            now = self._clock.now()
            self._expire_stale_for_flight(booking.flight_id, now)
            if booking.status is BookingStatus.CANCELLED:
                return booking
            if booking.status is BookingStatus.EXPIRED:
                raise ValueError("An expired booking cannot be cancelled")
            if booking.status in {BookingStatus.CHECKED_IN, BookingStatus.BOARDED}:
                raise ValueError(f"Booking cannot be cancelled in {booking.status.name} state")
            if now >= flight.departure_time:
                raise ValueError("Cannot cancel after departure")
            if booking.status is BookingStatus.CONFIRMED:
                payment = self._completed_payment_for(booking)
                self._payment_gateway.refund(payment)
            self._release_seats(booking)
            booking.status = BookingStatus.CANCELLED
            return booking

    def check_in(self, booking_id: str) -> list[BoardingPass]:
        booking = self.get_booking(booking_id)
        flight = self._catalog.get_flight(booking.flight_id)
        with self._flight_locks[booking.flight_id]:
            if booking.status in {BookingStatus.CHECKED_IN, BookingStatus.BOARDED}:
                return [self.boarding_passes[pass_id] for pass_id in booking.boarding_pass_ids]
            if booking.status is not BookingStatus.CONFIRMED:
                raise ValueError("Only a confirmed booking can check in")
            now = self._clock.now()
            opens_at = flight.departure_time - self._check_in_opens_before
            closes_at = flight.departure_time - self._check_in_closes_before
            if now < opens_at:
                raise ValueError("Online check-in has not opened")
            if now >= closes_at:
                raise ValueError("Online check-in has closed")
            if flight.status is not FlightStatus.SCHEDULED:
                raise ValueError(f"Cannot check in while flight is {flight.status.name}")
            if not flight.gate:
                raise ValueError("A gate must be assigned before check-in")

            passes = []
            for assignment in booking.assignments:
                flight_seat = flight.seats[assignment.seat_id]
                flight_seat.status = FlightSeatStatus.CHECKED_IN
                boarding_pass = BoardingPass(
                    boarding_pass_id=str(uuid4()),
                    booking_id=booking.booking_id,
                    passenger_id=assignment.passenger_id,
                    flight_id=flight.flight_id,
                    seat_number=flight_seat.seat.number,
                    gate=flight.gate,
                    issued_at=now,
                )
                self.boarding_passes[boarding_pass.boarding_pass_id] = boarding_pass
                booking.boarding_pass_ids.append(boarding_pass.boarding_pass_id)
                passes.append(boarding_pass)
            booking.status = BookingStatus.CHECKED_IN
            booking.checked_in_at = now
            return passes

    def start_boarding(self, flight_id: str) -> None:
        flight = self._catalog.get_flight(flight_id)
        with self._flight_locks[flight_id]:
            if flight.status is FlightStatus.BOARDING:
                return
            if flight.status is not FlightStatus.SCHEDULED:
                raise ValueError(f"Cannot start boarding while flight is {flight.status.name}")
            now = self._clock.now()
            if now < flight.departure_time - self._boarding_opens_before:
                raise ValueError("Boarding has not opened")
            if now >= flight.departure_time:
                raise ValueError("Cannot start boarding after departure time")
            if not flight.gate:
                raise ValueError("A gate must be assigned before boarding")
            flight.status = FlightStatus.BOARDING

    def board_booking(self, booking_id: str) -> Booking:
        booking = self.get_booking(booking_id)
        flight = self._catalog.get_flight(booking.flight_id)
        with self._flight_locks[booking.flight_id]:
            if booking.status is BookingStatus.BOARDED:
                return booking
            if booking.status is not BookingStatus.CHECKED_IN:
                raise ValueError("Only a checked-in booking can board")
            if flight.status is not FlightStatus.BOARDING:
                raise ValueError("Flight is not boarding")
            if self._clock.now() >= flight.departure_time:
                raise ValueError("Boarding has closed")
            for seat_id in booking.seat_ids:
                flight.seats[seat_id].status = FlightSeatStatus.BOARDED
            booking.status = BookingStatus.BOARDED
            booking.boarded_at = self._clock.now()
            return booking

    def depart_flight(self, flight_id: str) -> None:
        flight = self._catalog.get_flight(flight_id)
        with self._flight_locks[flight_id]:
            if flight.status is FlightStatus.DEPARTED:
                return
            if flight.status is not FlightStatus.BOARDING:
                raise ValueError("Only a boarding flight can depart")
            if self._clock.now() < flight.departure_time:
                raise ValueError("Cannot depart before scheduled departure time")
            flight.status = FlightStatus.DEPARTED

    def arrive_flight(self, flight_id: str) -> None:
        flight = self._catalog.get_flight(flight_id)
        with self._flight_locks[flight_id]:
            if flight.status is FlightStatus.ARRIVED:
                return
            if flight.status is not FlightStatus.DEPARTED:
                raise ValueError("Only a departed flight can arrive")
            if self._clock.now() < flight.arrival_time:
                raise ValueError("Cannot arrive before scheduled arrival time")
            flight.status = FlightStatus.ARRIVED

    def cancel_flight(self, flight_id: str) -> list[Booking]:
        flight = self._catalog.get_flight(flight_id)
        with self._flight_locks[flight_id]:
            if flight.status is FlightStatus.CANCELLED:
                return []
            if flight.status in {FlightStatus.DEPARTED, FlightStatus.ARRIVED}:
                raise ValueError(f"Cannot cancel a flight in {flight.status.name} state")
            affected = []
            for booking in list(self.bookings.values()):
                if booking.flight_id != flight_id or booking.status in {
                    BookingStatus.CANCELLED,
                    BookingStatus.EXPIRED,
                }:
                    continue
                for payment_id in booking.payment_ids:
                    payment = self.payments[payment_id]
                    if payment.status is PaymentStatus.COMPLETED:
                        self._payment_gateway.refund(payment)
                self._release_seats(booking)
                booking.status = BookingStatus.CANCELLED
                affected.append(booking)
            flight.status = FlightStatus.CANCELLED
            return affected

    def get_available_seats(
        self,
        flight_id: str,
        cabin_class: CabinClass | None = None,
    ) -> list[Seat]:
        flight = self._catalog.get_flight(flight_id)
        with self._flight_locks[flight_id]:
            self._expire_stale_for_flight(flight_id, self._clock.now())
            return sorted(
                (
                    flight_seat.seat
                    for flight_seat in flight.seats.values()
                    if flight_seat.status is FlightSeatStatus.AVAILABLE
                    and (
                        cabin_class is None
                        or flight_seat.seat.cabin_class is cabin_class
                    )
                ),
                key=lambda seat: seat.number,
            )

    def expire_stale_bookings(self, flight_id: str | None = None) -> list[Booking]:
        now = self._clock.now()
        if flight_id is not None:
            self._catalog.get_flight(flight_id)
            with self._flight_locks[flight_id]:
                return self._expire_stale_for_flight(flight_id, now)
        expired = []
        for current_flight_id in list(self._catalog.flights):
            with self._flight_locks[current_flight_id]:
                expired.extend(self._expire_stale_for_flight(current_flight_id, now))
        return expired

    def get_booking(self, booking_id: str) -> Booking:
        try:
            return self.bookings[booking_id]
        except KeyError as error:
            raise ValueError(f"Booking '{booking_id}' does not exist") from error

    def get_passenger_bookings(self, passenger_id: str) -> list[Booking]:
        self._catalog.get_passenger(passenger_id)
        return sorted(
            (
                booking
                for booking in list(self.bookings.values())
                if passenger_id in booking.passenger_ids
            ),
            key=lambda booking: booking.created_at,
            reverse=True,
        )

    def _expire_stale_for_flight(self, flight_id: str, now) -> list[Booking]:
        expired = []
        for booking in list(self.bookings.values()):
            if (
                booking.flight_id == flight_id
                and booking.status is BookingStatus.PENDING_PAYMENT
                and booking.hold_expires_at <= now
            ):
                self._release_seats(booking)
                booking.status = BookingStatus.EXPIRED
                expired.append(booking)
        return expired

    def _release_seats(self, booking: Booking) -> None:
        flight = self._catalog.get_flight(booking.flight_id)
        for seat_id in booking.seat_ids:
            flight_seat = flight.seats[seat_id]
            if flight_seat.booking_id == booking.booking_id:
                flight_seat.status = FlightSeatStatus.AVAILABLE
                flight_seat.booking_id = None
                flight_seat.held_until = None

    def _completed_payment_for(self, booking: Booking) -> Payment:
        for payment_id in reversed(booking.payment_ids):
            payment = self.payments[payment_id]
            if payment.status is PaymentStatus.COMPLETED:
                return payment
        raise RuntimeError("Confirmed booking has no completed payment")
