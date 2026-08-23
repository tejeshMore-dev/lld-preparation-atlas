from dataclasses import dataclass
from decimal import Decimal

from models.enums import AccountStatus
from models.money import MoneyInput, to_money


@dataclass
class BankAccount:
    account_id: str
    owner_name: str
    balance: Decimal
    status: AccountStatus = AccountStatus.ACTIVE

    def debit(self, amount: MoneyInput) -> None:
        debit_amount = to_money(amount)
        self._ensure_active()
        if debit_amount <= 0:
            raise ValueError("Debit amount must be greater than zero")
        if debit_amount > self.balance:
            raise ValueError("Insufficient account balance")
        self.balance -= debit_amount

    def credit(self, amount: MoneyInput) -> None:
        credit_amount = to_money(amount)
        self._ensure_active()
        if credit_amount <= 0:
            raise ValueError("Credit amount must be greater than zero")
        self.balance += credit_amount

    def _ensure_active(self) -> None:
        if self.status != AccountStatus.ACTIVE:
            raise ValueError("Account is not active")
