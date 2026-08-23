from decimal import Decimal, InvalidOperation

from models.money import MoneyInput, to_money
from models.price_breakdown import PriceBreakdown
from strategies.pricing_strategy import PricingStrategy


class StandardPricingStrategy(PricingStrategy):
    def __init__(
        self,
        base_delivery_fee: MoneyInput = "30",
        per_km_fee: MoneyInput = "8",
        tax_percent: MoneyInput = "5",
    ) -> None:
        self._base_delivery_fee = to_money(base_delivery_fee)
        self._per_km_fee = to_money(per_km_fee)
        try:
            self._tax_percent = Decimal(str(tax_percent))
        except (InvalidOperation, ValueError) as error:
            raise ValueError("Tax percentage must be numeric") from error
        if (
            self._base_delivery_fee < 0
            or self._per_km_fee < 0
            or not self._tax_percent.is_finite()
            or self._tax_percent < 0
        ):
            raise ValueError("Pricing values must be finite and non-negative")

    def calculate(self, subtotal: Decimal, delivery_distance_km: Decimal) -> PriceBreakdown:
        if subtotal < 0 or delivery_distance_km < 0:
            raise ValueError("Subtotal and delivery distance cannot be negative")
        normalized_subtotal = to_money(subtotal)
        delivery_fee = to_money(
            self._base_delivery_fee + self._per_km_fee * delivery_distance_km
        )
        tax = to_money(normalized_subtotal * self._tax_percent / Decimal("100"))
        discount = Decimal("0.00")
        return PriceBreakdown(
            subtotal=normalized_subtotal,
            delivery_fee=delivery_fee,
            tax=tax,
            discount=discount,
            total=to_money(normalized_subtotal + delivery_fee + tax - discount),
        )
