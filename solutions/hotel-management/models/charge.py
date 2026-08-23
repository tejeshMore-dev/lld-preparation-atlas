from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from models.enums import ChargeType


@dataclass(frozen=True)
class Charge:
    charge_id: str
    charge_type: ChargeType
    description: str
    amount: Decimal
    created_at: datetime
