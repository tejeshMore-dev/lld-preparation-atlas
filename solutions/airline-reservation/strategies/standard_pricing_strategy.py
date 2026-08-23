from decimal import Decimal

from models.flight import Flight
from models.money import to_money
from strategies.pricing_strategy import PricingStrategy


class StandardPricingStrategy(PricingStrategy):
    """Adds the flight-specific fare for each assigned seat's cabin."""

    def calculate(self, flight: Flight, seat_ids: tuple[str, ...]) -> Decimal:
        total = Decimal("0")
        for seat_id in seat_ids:
            flight_seat = flight.seats.get(seat_id)
            if flight_seat is None:
                raise ValueError(f"Seat '{seat_id}' does not exist on this flight")
            cabin = flight_seat.seat.cabin_class
            if cabin not in flight.prices:
                raise ValueError(f"No fare configured for cabin {cabin.name}")
            total += flight.prices[cabin]
        return to_money(total)
