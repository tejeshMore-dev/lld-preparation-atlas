from datetime import date, timedelta

from models.enums import PaymentMethod, RoomType
from models.guest import Guest
from models.hotel import Hotel
from models.room import Room
from services.booking_service import BookingService
from services.catalog_service import CatalogService
from services.in_memory_payment_gateway import InMemoryPaymentGateway
from strategies.standard_pricing_strategy import StandardPricingStrategy


def build_demo() -> tuple[CatalogService, BookingService]:
    catalog = CatalogService()
    catalog.add_guest(Guest("guest-1", "Asha", "asha@example.com", "9000000001"))
    catalog.add_hotel(Hotel("hotel-1", "Design Inn", "Bengaluru", "1 Pattern Road"))
    catalog.add_room("hotel-1", Room("room-101", "101", RoomType.STANDARD, 2, "2200"))
    catalog.add_room("hotel-1", Room("room-201", "201", RoomType.DELUXE, 3, "3400"))
    catalog.add_room("hotel-1", Room("room-301", "301", RoomType.SUITE, 4, "5200"))
    service = BookingService(
        catalog,
        StandardPricingStrategy(),
        InMemoryPaymentGateway(),
    )
    return catalog, service


def main() -> None:
    _, service = build_demo()
    arrival = date.today() + timedelta(days=1)
    departure = arrival + timedelta(days=2)
    quotes = service.search_available_rooms("Bengaluru", arrival, departure)
    print(f"Available rooms for {arrival} to {departure}:")
    for quote in quotes:
        print(f"  {quote.room_number} ({quote.room_type.name}): Rs. {quote.total_price}")

    booking = service.create_booking(
        "guest-1", "hotel-1", [quotes[0].room_id], arrival, departure, 2
    )
    payment = service.confirm_booking(booking.booking_id, PaymentMethod.UPI)
    print(f"Booking {booking.status.name}; payment {payment.status.name}")

    # Move the educational demo's service clock conceptually by setting dates in
    # real applications. Here we show the later stay operations as API examples.
    print(f"Reservation total: Rs. {booking.total_amount} for {booking.nights} nights")
    print("At arrival: service.check_in(booking.booking_id)")
    print("During stay: service.add_charge(..., ChargeType.ROOM_SERVICE, 'Dinner', 450)")
    print("At departure: service.check_out(booking.booking_id, PaymentMethod.UPI)")


if __name__ == "__main__":
    main()
