from abc import ABC, abstractmethod
from decimal import Decimal

from models.card import Card
from models.money import MoneyInput


class BankGateway(ABC):
    @abstractmethod
    def get_card(self, card_number: str) -> Card:
        raise NotImplementedError

    @abstractmethod
    def authenticate(self, card_number: str, pin: str) -> str:
        """Return the linked account ID after successful authentication."""
        raise NotImplementedError

    @abstractmethod
    def get_balance(self, account_id: str) -> Decimal:
        raise NotImplementedError

    @abstractmethod
    def debit(self, account_id: str, amount: MoneyInput) -> None:
        raise NotImplementedError

    @abstractmethod
    def credit(self, account_id: str, amount: MoneyInput) -> None:
        raise NotImplementedError

    @abstractmethod
    def transfer(
        self,
        source_account_id: str,
        target_account_id: str,
        amount: MoneyInput,
    ) -> None:
        raise NotImplementedError
