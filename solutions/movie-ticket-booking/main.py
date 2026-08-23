from datetime import datetime, timedelta

from models.enums import PaymentMethod, SeatType
from models.movie import Movie
from models.screen import Screen
from models.seat import Seat
from models.theatre import Theatre
from models.user import User
from services.booking_service import BookingService
from services.catalog_service import CatalogService
from services.in_memory_payment_gateway import InMemoryPaymentGateway
from strategies.standard_pricing_strategy import StandardPricingStrategy


def build_demo() -> tuple[CatalogService, BookingService]:
    catalog = CatalogService()
    catalog.add_user(User("user-1", "Asha", "asha@example.com"))
    catalog.add_movie(Movie("movie-1", "The Design", 150, "English", "Drama", "U/A"))

    screen = Screen("screen-1", "Audi 1")
    for number in range(1, 5):
        screen.add_seat(Seat(f"A{number}", "A", number, SeatType.REGULAR))
    for number in range(1, 4):
        screen.add_seat(Seat(f"B{number}", "B", number, SeatType.PREMIUM))
    screen.add_seat(Seat("C1", "C", 1, SeatType.RECLINER))

    theatre = Theatre("theatre-1", "Cine Design", "Bengaluru")
    theatre.add_screen(screen)
    catalog.add_theatre(theatre)
    catalog.create_show(
        "show-1",
        "movie-1",
        "theatre-1",
        "screen-1",
        datetime.now() + timedelta(days=1),
        {
            SeatType.REGULAR: "200",
            SeatType.PREMIUM: "320",
            SeatType.RECLINER: "550",
        },
    )

    service = BookingService(
        catalog,
        StandardPricingStrategy(),
        InMemoryPaymentGateway(),
    )
    return catalog, service


def main() -> None:
    catalog, service = build_demo()
    show = catalog.search_shows("Bengaluru", movie_id="movie-1")[0]
    print(f"Found: {catalog.get_movie(show.movie_id).title} at {show.start_time:%d %b, %I:%M %p}")
    print("Available seats:", [seat.seat_id for seat in service.get_available_seats(show.show_id)])

    booking = service.create_booking("user-1", show.show_id, ["A1", "B1"])
    print(f"Held {booking.seat_ids} for Rs. {booking.total_amount}")
    print(f"Hold expires at: {booking.hold_expires_at:%I:%M:%S %p}")

    payment = service.confirm_booking(booking.booking_id, PaymentMethod.UPI)
    print(f"Payment: {payment.status.name}; booking: {booking.status.name}")
    print("Still available:", [seat.seat_id for seat in service.get_available_seats(show.show_id)])


if __name__ == "__main__":
    main()
