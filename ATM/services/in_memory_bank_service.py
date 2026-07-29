from datetime import date
from decimal import Decimal

from models.account import BankAccount
from models.card import Card
from models.enums import AccountStatus, CardStatus
from models.errors import AuthenticationError
from models.money import MoneyInput, to_money
from services.bank_gateway import BankGateway


class InMemoryBankService(BankGateway):
    MAX_PIN_ATTEMPTS = 3

    def __init__(self) -> None:
        self.accounts: dict[str, BankAccount] = {}
        self.cards: dict[str, Card] = {}

    def create_account(
        self,
        account_id: str,
        owner_name: str,
        opening_balance: MoneyInput = "0",
    ) -> BankAccount:
        if not account_id.strip():
            raise ValueError("Account ID cannot be empty")
        if account_id in self.accounts:
            raise ValueError("Account ID already exists")
        if not owner_name.strip():
            raise ValueError("Account owner name cannot be empty")
        balance = to_money(opening_balance)
        if balance < 0:
            raise ValueError("Opening balance cannot be negative")

        account = BankAccount(account_id, owner_name.strip(), balance)
        self.accounts[account_id] = account
        return account

    def issue_card(
        self,
        card_number: str,
        account_id: str,
        pin: str,
        expiry_date: date,
    ) -> Card:
        if not card_number.strip():
            raise ValueError("Card number cannot be empty")
        if card_number in self.cards:
            raise ValueError("Card number already exists")
        self._get_account(account_id)._ensure_active()
        if expiry_date < date.today():
            raise ValueError("Cannot issue an already expired card")

        card = Card.issue(card_number, account_id, pin, expiry_date)
        self.cards[card_number] = card
        return card

    def get_card(self, card_number: str) -> Card:
        try:
            return self.cards[card_number]
        except KeyError as error:
            raise ValueError("Card not recognized") from error

    def authenticate(self, card_number: str, pin: str) -> str:
        card = self.get_card(card_number)
        if card.is_expired():
            card.status = CardStatus.EXPIRED
            raise AuthenticationError("Card has expired", end_session=True)
        if card.status != CardStatus.ACTIVE:
            raise AuthenticationError("Card is not active", end_session=True)

        account = self._get_account(card.account_id)
        if account.status != AccountStatus.ACTIVE:
            raise AuthenticationError(
                "Linked account is not active",
                end_session=True,
            )

        if not card.verify_pin(pin):
            card.failed_pin_attempts += 1
            if card.failed_pin_attempts >= self.MAX_PIN_ATTEMPTS:
                card.status = CardStatus.BLOCKED
                raise AuthenticationError(
                    "Invalid PIN; card has been blocked",
                    end_session=True,
                )
            attempts_left = self.MAX_PIN_ATTEMPTS - card.failed_pin_attempts
            raise AuthenticationError(
                f"Invalid PIN; {attempts_left} attempt(s) remaining"
            )

        card.failed_pin_attempts = 0
        return card.account_id

    def get_balance(self, account_id: str) -> Decimal:
        account = self._get_account(account_id)
        account._ensure_active()
        return account.balance

    def debit(self, account_id: str, amount: MoneyInput) -> None:
        self._get_account(account_id).debit(amount)

    def credit(self, account_id: str, amount: MoneyInput) -> None:
        self._get_account(account_id).credit(amount)

    def transfer(
        self,
        source_account_id: str,
        target_account_id: str,
        amount: MoneyInput,
    ) -> None:
        if source_account_id == target_account_id:
            raise ValueError("Source and target accounts must be different")
        source = self._get_account(source_account_id)
        target = self._get_account(target_account_id)
        transfer_amount = to_money(amount)

        source.debit(transfer_amount)
        try:
            target.credit(transfer_amount)
        except ValueError:
            source.credit(transfer_amount)
            raise

    def _get_account(self, account_id: str) -> BankAccount:
        try:
            return self.accounts[account_id]
        except KeyError as error:
            raise ValueError(f'Account "{account_id}" not found') from error
