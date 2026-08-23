import unittest
from datetime import date
from decimal import Decimal

from models.enums import ATMState, AccountStatus, CardStatus, TransactionStatus
from services.atm import ATM
from services.cash_dispenser import CashDispenser
from services.in_memory_bank_service import InMemoryBankService
from strategies.exact_cash_strategy import ExactCashStrategy


class FailingCashDispenser(CashDispenser):
    def dispense(self, notes: dict[int, int]) -> None:
        raise RuntimeError("Simulated hardware failure")


class ATMTest(unittest.TestCase):
    def setUp(self) -> None:
        self.bank = InMemoryBankService()
        self.alice = self.bank.create_account("alice", "Alice", "10000")
        self.bob = self.bank.create_account("bob", "Bob", "1000")
        self.card = self.bank.issue_card(
            "card-1",
            "alice",
            "1234",
            date(2030, 12, 31),
        )
        self.dispenser = CashDispenser(
            {500: 10, 200: 10, 100: 10},
            ExactCashStrategy(),
        )
        self.atm = ATM("atm-1", self.bank, self.dispenser, "5000")

    def authenticate(self) -> None:
        self.atm.insert_card("card-1")
        self.atm.enter_pin("1234")

    def test_authentication_and_balance_inquiry(self) -> None:
        self.authenticate()

        balance = self.atm.check_balance()

        self.assertEqual(balance, Decimal("10000.00"))
        self.assertEqual(self.atm.state, ATMState.AUTHENTICATED)
        self.assertEqual(self.atm.transactions[-1].status, TransactionStatus.COMPLETED)

    def test_three_wrong_pins_block_card_and_end_session(self) -> None:
        self.atm.insert_card("card-1")

        with self.assertRaises(ValueError):
            self.atm.enter_pin("0000")
        with self.assertRaises(ValueError):
            self.atm.enter_pin("0000")
        with self.assertRaises(ValueError):
            self.atm.enter_pin("0000")

        self.assertEqual(self.card.status, CardStatus.BLOCKED)
        self.assertEqual(self.atm.state, ATMState.IDLE)
        self.assertIsNone(self.atm.current_card)

    def test_withdrawal_updates_account_and_cash_inventory(self) -> None:
        self.authenticate()
        cash_before = self.dispenser.total_cash

        transaction = self.atm.withdraw("1300")

        self.assertEqual(transaction.status, TransactionStatus.COMPLETED)
        self.assertEqual(transaction.cash_breakdown, {500: 2, 200: 1, 100: 1})
        self.assertEqual(self.alice.balance, Decimal("8700.00"))
        self.assertEqual(self.dispenser.total_cash, cash_before - 1300)

    def test_insufficient_balance_declines_without_changing_cash(self) -> None:
        self.authenticate()
        self.alice.balance = Decimal("100.00")
        cash_before = self.dispenser.total_cash

        transaction = self.atm.withdraw("500")

        self.assertEqual(transaction.status, TransactionStatus.DECLINED)
        self.assertEqual(self.alice.balance, Decimal("100.00"))
        self.assertEqual(self.dispenser.total_cash, cash_before)

    def test_unavailable_note_combination_does_not_debit_account(self) -> None:
        atm = ATM(
            "atm-2",
            self.bank,
            CashDispenser({500: 2}, ExactCashStrategy()),
        )
        atm.insert_card("card-1")
        atm.enter_pin("1234")

        transaction = atm.withdraw("300")

        self.assertEqual(transaction.status, TransactionStatus.DECLINED)
        self.assertEqual(self.alice.balance, Decimal("10000.00"))

    def test_cash_hardware_failure_rolls_back_account_debit(self) -> None:
        atm = ATM(
            "atm-2",
            self.bank,
            FailingCashDispenser({500: 2}, ExactCashStrategy()),
        )
        atm.insert_card("card-1")
        atm.enter_pin("1234")

        transaction = atm.withdraw("500")

        self.assertEqual(transaction.status, TransactionStatus.FAILED)
        self.assertEqual(self.alice.balance, Decimal("10000.00"))

    def test_deposit_updates_account_and_recycler_inventory(self) -> None:
        self.authenticate()
        count_before = self.dispenser.inventory[500]

        transaction = self.atm.deposit({500: 2, 200: 1})

        self.assertEqual(transaction.status, TransactionStatus.COMPLETED)
        self.assertEqual(transaction.amount, Decimal("1200.00"))
        self.assertEqual(self.alice.balance, Decimal("11200.00"))
        self.assertEqual(self.dispenser.inventory[500], count_before + 2)

    def test_transfer_is_atomic_and_declines_insufficient_balance(self) -> None:
        self.authenticate()

        completed = self.atm.transfer("bob", "750")
        declined = self.atm.transfer("bob", "20000")

        self.assertEqual(completed.status, TransactionStatus.COMPLETED)
        self.assertEqual(declined.status, TransactionStatus.DECLINED)
        self.assertEqual(self.alice.balance, Decimal("9250.00"))
        self.assertEqual(self.bob.balance, Decimal("1750.00"))

    def test_limits_and_fractional_withdrawals_are_declined(self) -> None:
        self.authenticate()

        above_limit = self.atm.withdraw("5100")
        fractional = self.atm.withdraw("100.50")

        self.assertEqual(above_limit.status, TransactionStatus.DECLINED)
        self.assertEqual(fractional.status, TransactionStatus.DECLINED)
        self.assertEqual(self.alice.balance, Decimal("10000.00"))

    def test_exact_cash_strategy_handles_bounded_inventory(self) -> None:
        strategy = ExactCashStrategy()

        notes = strategy.select_notes(600, {500: 1, 200: 3, 100: 0})

        self.assertEqual(notes, {200: 3})

    def test_expired_and_blocked_accounts_cannot_authenticate(self) -> None:
        self.card.expiry_date = date(2020, 1, 1)
        self.atm.insert_card("card-1")
        with self.assertRaises(ValueError):
            self.atm.enter_pin("1234")
        self.assertEqual(self.card.status, CardStatus.EXPIRED)

        active_card = self.bank.issue_card("card-2", "bob", "4321", date(2030, 1, 1))
        self.bob.status = AccountStatus.BLOCKED
        self.atm.insert_card(active_card.card_number)
        with self.assertRaises(ValueError):
            self.atm.enter_pin("4321")
        self.assertEqual(self.atm.state, ATMState.IDLE)

    def test_session_and_out_of_service_transitions(self) -> None:
        with self.assertRaises(ValueError):
            self.atm.check_balance()

        self.atm.set_out_of_service()
        with self.assertRaises(ValueError):
            self.atm.insert_card("card-1")
        self.atm.restore_service()
        self.authenticate()
        with self.assertRaises(ValueError):
            self.atm.set_out_of_service()
        self.assertEqual(self.atm.eject_card(), "card-1")
        self.assertEqual(self.atm.state, ATMState.IDLE)


if __name__ == "__main__":
    unittest.main()
