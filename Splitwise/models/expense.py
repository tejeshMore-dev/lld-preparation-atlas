from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from models.enums import SplitType
from models.split import Split


@dataclass(frozen=True)
class Expense:
    expense_id: str
    description: str
    amount: Decimal
    paid_by_id: str
    splits: tuple[Split, ...]
    split_type: SplitType
    created_at: datetime
    group_id: str | None = None
