from datetime import date
from decimal import Decimal

from models.money import to_money
from models.room import Room
from strategies.pricing_strategy import PricingStrategy


class StandardPricingStrategy(PricingStrategy):
    def price_for_night(self, room: Room, stay_date: date) -> Decimal:
        return to_money(room.nightly_rate)
