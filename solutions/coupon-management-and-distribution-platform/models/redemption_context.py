from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RedemptionContext:
    order_id: str
    order_amount: Decimal
    categories: frozenset[str]
