from decimal import Decimal

from models.money import to_money
from models.show import Show
from strategies.pricing_strategy import PricingStrategy


class StandardPricingStrategy(PricingStrategy):
    """Adds the show-specific price configured for every selected seat type."""

    def calculate(self, show: Show, seat_ids: tuple[str, ...]) -> Decimal:
        total = Decimal("0")
        for seat_id in seat_ids:
            show_seat = show.seats.get(seat_id)
            if show_seat is None:
                raise ValueError(f"Seat '{seat_id}' does not exist in this show")
            seat_type = show_seat.seat.seat_type
            if seat_type not in show.prices:
                raise ValueError(f"No price configured for seat type {seat_type.name}")
            total += show.prices[seat_type]
        return to_money(total)
