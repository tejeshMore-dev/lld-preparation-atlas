from abc import ABC, abstractmethod
from datetime import date, timedelta
from decimal import Decimal

from models.money import to_money
from models.room import Room


class PricingStrategy(ABC):
    """Prices individual nights and provides a reusable whole-stay calculation."""

    @abstractmethod
    def price_for_night(self, room: Room, stay_date: date) -> Decimal:
        raise NotImplementedError

    def calculate(self, room: Room, check_in_date: date, check_out_date: date) -> Decimal:
        if check_out_date <= check_in_date:
            raise ValueError("Check-out date must be after check-in date")
        total = Decimal("0")
        current_date = check_in_date
        while current_date < check_out_date:
            total += self.price_for_night(room, current_date)
            current_date += timedelta(days=1)
        return to_money(total)
