from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from models.enums import TransactionStatus, TransactionType


@dataclass
class Transaction:
    transaction_id: str
    transaction_type: TransactionType
    source_account_id: str
    amount: Decimal
    created_at: datetime
    status: TransactionStatus = TransactionStatus.PENDING
    completed_at: datetime | None = None
    target_account_id: str | None = None
    decline_reason: str | None = None
    cash_breakdown: dict[int, int] = field(default_factory=dict)

    def complete(self) -> None:
        self.status = TransactionStatus.COMPLETED
        self.completed_at = datetime.now()

    def decline(self, reason: str) -> None:
        self.status = TransactionStatus.DECLINED
        self.decline_reason = reason
        self.completed_at = datetime.now()

    def fail(self, reason: str) -> None:
        self.status = TransactionStatus.FAILED
        self.decline_reason = reason
        self.completed_at = datetime.now()
