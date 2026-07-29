from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Balance:
    debtor_id: str
    creditor_id: str
    amount: Decimal
