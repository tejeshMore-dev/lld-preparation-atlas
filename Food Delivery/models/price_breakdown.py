from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PriceBreakdown:
    subtotal: Decimal
    delivery_fee: Decimal
    tax: Decimal
    discount: Decimal
    total: Decimal
