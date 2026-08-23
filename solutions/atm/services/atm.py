import uuid
from datetime import datetime
from decimal import Decimal

from models.card import Card
from models.enums import ATMState, TransactionType
from models.errors import AuthenticationError
from models.money import MoneyInput, to_money
from models.transaction import Transaction
from services.bank_gateway import BankGateway
from services.cash_dispenser import CashDispenser


class ATM:
    def __init__(
        self,
        atm_id: str,
        bank_gateway: BankGateway,
        cash_dispenser: CashDispenser,
        withdrawal_limit: MoneyInput = "20000",
    ) -> None:
        if not atm_id.strip():
            raise ValueError("ATM ID cannot be empty")
        limit = to_money(withdrawal_limit)
        if limit <= 0:
            raise ValueError("Withdrawal limit must be greater than zero")

        self.atm_id = atm_id
        self.bank_gateway = bank_gateway
        self.cash_dispenser = cash_dispenser
        self.withdrawal_limit = limit
        self.state = ATMState.IDLE
        self.current_card: Card | None = None
        self.current_account_id: str | None = None
        self.transactions: list[Transaction] = []

    def insert_card(self, card_number: str) -> Card:
        if self.state == ATMState.OUT_OF_SERVICE:
            raise ValueError("ATM is out of service")
        if self.state != ATMState.IDLE:
            raise ValueError("Another card session is already active")

        card = self.bank_gateway.get_card(card_number)
        self.current_card = card
        self.state = ATMState.CARD_INSERTED
        return card

    def enter_pin(self, pin: str) -> None:
        if self.state != ATMState.CARD_INSERTED or self.current_card is None:
            raise ValueError("Insert a card before entering a PIN")

        try:
            account_id = self.bank_gateway.authenticate(
                self.current_card.card_number,
                pin,
            )
        except AuthenticationError as error:
            if error.end_session:
                self._clear_session()
            raise

        self.current_account_id = account_id
        self.state = ATMState.AUTHENTICATED

    def check_balance(self) -> Decimal:
        account_id = self._require_authenticated()
        transaction = self._new_transaction(
            TransactionType.BALANCE_INQUIRY,
            Decimal("0.00"),
        )
        try:
            balance = self.bank_gateway.get_balance(account_id)
            transaction.complete()
            return balance
        except ValueError as error:
            transaction.fail(str(error))
            raise

    def withdraw(self, amount: MoneyInput) -> Transaction:
        account_id = self._require_authenticated()
        withdrawal = to_money(amount)
        if withdrawal <= 0:
            raise ValueError("Withdrawal amount must be greater than zero")

        transaction = self._new_transaction(TransactionType.WITHDRAWAL, withdrawal)
        if withdrawal != withdrawal.to_integral_value():
            transaction.decline("ATM can dispense only whole currency amounts")
            return transaction
        if withdrawal > self.withdrawal_limit:
            transaction.decline("Withdrawal exceeds the per-transaction limit")
            return transaction

        notes = self.cash_dispenser.prepare_dispense(int(withdrawal))
        if notes is None:
            transaction.decline("ATM cannot dispense the requested amount exactly")
            return transaction

        try:
            self.bank_gateway.debit(account_id, withdrawal)
        except ValueError as error:
            transaction.decline(str(error))
            return transaction

        try:
            self.cash_dispenser.dispense(notes)
        except Exception as error:
            try:
                self.bank_gateway.credit(account_id, withdrawal)
            except Exception as compensation_error:
                transaction.fail(
                    "Cash dispensing and account compensation failed: "
                    f"{error}; {compensation_error}"
                )
                return transaction
            transaction.fail(f"Cash dispensing failed: {error}")
            return transaction

        transaction.cash_breakdown = notes
        transaction.complete()
        return transaction

    def deposit(self, notes: dict[int, int]) -> Transaction:
        account_id = self._require_authenticated()
        total = self.cash_dispenser.validate_notes(notes)
        amount = to_money(total)
        transaction = self._new_transaction(TransactionType.DEPOSIT, amount)

        try:
            self.bank_gateway.credit(account_id, amount)
        except ValueError as error:
            transaction.decline(str(error))
            return transaction

        try:
            self.cash_dispenser.load_cash(notes)
        except Exception as error:
            try:
                self.bank_gateway.debit(account_id, amount)
            except Exception as compensation_error:
                transaction.fail(
                    "Cash deposit and account compensation failed: "
                    f"{error}; {compensation_error}"
                )
                return transaction
            transaction.fail(f"Cash deposit failed: {error}")
            return transaction

        transaction.cash_breakdown = dict(notes)
        transaction.complete()
        return transaction

    def transfer(
        self,
        target_account_id: str,
        amount: MoneyInput,
    ) -> Transaction:
        source_account_id = self._require_authenticated()
        transfer_amount = to_money(amount)
        if transfer_amount <= 0:
            raise ValueError("Transfer amount must be greater than zero")

        transaction = self._new_transaction(
            TransactionType.TRANSFER,
            transfer_amount,
            target_account_id,
        )
        try:
            self.bank_gateway.transfer(
                source_account_id,
                target_account_id,
                transfer_amount,
            )
        except ValueError as error:
            transaction.decline(str(error))
            return transaction

        transaction.complete()
        return transaction

    def eject_card(self) -> str:
        if self.state not in (ATMState.CARD_INSERTED, ATMState.AUTHENTICATED):
            raise ValueError("No card is currently inserted")
        card_number = self.current_card.card_number
        self._clear_session()
        return card_number

    def cancel_session(self) -> str:
        return self.eject_card()

    def set_out_of_service(self) -> None:
        if self.state != ATMState.IDLE:
            raise ValueError("End the active card session first")
        self.state = ATMState.OUT_OF_SERVICE

    def restore_service(self) -> None:
        if self.state != ATMState.OUT_OF_SERVICE:
            raise ValueError("ATM is not out of service")
        self.state = ATMState.IDLE

    def get_account_transactions(self) -> list[Transaction]:
        account_id = self._require_authenticated()
        return [
            transaction
            for transaction in self.transactions
            if transaction.source_account_id == account_id
            or transaction.target_account_id == account_id
        ]

    def _new_transaction(
        self,
        transaction_type: TransactionType,
        amount: Decimal,
        target_account_id: str | None = None,
    ) -> Transaction:
        account_id = self._require_authenticated()
        transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            transaction_type=transaction_type,
            source_account_id=account_id,
            target_account_id=target_account_id,
            amount=amount,
            created_at=datetime.now(),
        )
        self.transactions.append(transaction)
        return transaction

    def _require_authenticated(self) -> str:
        if self.state != ATMState.AUTHENTICATED or self.current_account_id is None:
            raise ValueError("Authenticate the card before performing this operation")
        return self.current_account_id

    def _clear_session(self) -> None:
        self.current_card = None
        self.current_account_id = None
        self.state = ATMState.IDLE
