from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Settlement:
    settlement_id: str
    paid_by_id: str
    paid_to_id: str
    amount: Decimal
    created_at: datetime
