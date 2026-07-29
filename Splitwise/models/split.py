from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Split:
    user_id: str
    amount: Decimal
