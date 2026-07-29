from decimal import Decimal

from models.money import MoneyInput, to_money
from models.price_breakdown import PriceBreakdown
from strategies.pricing_strategy import PricingStrategy


class FreeDeliveryDecorator(PricingStrategy):
    def __init__(self, wrapped: PricingStrategy, minimum_subtotal: MoneyInput) -> None:
        self._wrapped = wrapped
        self._minimum_subtotal = to_money(minimum_subtotal)
        if self._minimum_subtotal < 0:
            raise ValueError("Free-delivery threshold cannot be negative")

    def calculate(self, subtotal: Decimal, delivery_distance_km: Decimal) -> PriceBreakdown:
        breakdown = self._wrapped.calculate(subtotal, delivery_distance_km)
        if breakdown.subtotal < self._minimum_subtotal:
            return breakdown
        return PriceBreakdown(
            subtotal=breakdown.subtotal,
            delivery_fee=Decimal("0.00"),
            tax=breakdown.tax,
            discount=breakdown.discount,
            total=to_money(breakdown.subtotal + breakdown.tax - breakdown.discount),
        )
