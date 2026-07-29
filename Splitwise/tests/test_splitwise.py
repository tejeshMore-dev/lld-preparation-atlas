import unittest
from decimal import Decimal

from models.enums import SplitType
from services.balance_sheet import BalanceSheet
from services.splitwise_service import SplitwiseService


class SplitwiseServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SplitwiseService()
        self.alice = self.service.create_user("Alice", "alice@example.com", "alice")
        self.bob = self.service.create_user("Bob", "bob@example.com", "bob")
        self.charlie = self.service.create_user(
            "Charlie",
            "charlie@example.com",
            "charlie",
        )

    def test_equal_split_distributes_rounding_cents(self) -> None:
        expense = self.service.add_expense(
            "Snacks",
            "100",
            self.alice.user_id,
            [self.alice.user_id, self.bob.user_id, self.charlie.user_id],
            SplitType.EQUAL,
        )

        self.assertEqual(
            [split.amount for split in expense.splits],
            [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")],
        )
        self.assertEqual(
            self.service.balance_sheet.amount_owed("bob", "alice"),
            Decimal("33.33"),
        )

    def test_exact_split_nets_opposing_debts(self) -> None:
        self.service.add_expense(
            "Dinner",
            "90",
            "alice",
            ["alice", "bob", "charlie"],
            SplitType.EQUAL,
        )
        self.service.add_expense(
            "Taxi",
            "60",
            "bob",
            ["alice", "charlie"],
            SplitType.EXACT,
            {"alice": "20", "charlie": "40"},
        )

        self.assertEqual(
            self.service.balance_sheet.amount_owed("bob", "alice"),
            Decimal("10.00"),
        )
        self.assertEqual(
            self.service.balance_sheet.amount_owed("alice", "bob"),
            Decimal("0.00"),
        )
        self.assertEqual(
            self.service.balance_sheet.amount_owed("charlie", "bob"),
            Decimal("40.00"),
        )

    def test_percentage_split_is_exact_to_the_cent(self) -> None:
        expense = self.service.add_expense(
            "Groceries",
            "100",
            "alice",
            ["alice", "bob", "charlie"],
            SplitType.PERCENTAGE,
            {"alice": "33.33", "bob": "33.33", "charlie": "33.34"},
        )

        self.assertEqual(
            sum((split.amount for split in expense.splits), Decimal("0")),
            Decimal("100.00"),
        )
        self.assertEqual(expense.splits[2].amount, Decimal("33.34"))

    def test_invalid_split_does_not_change_ledger(self) -> None:
        with self.assertRaises(ValueError):
            self.service.add_expense(
                "Invalid",
                "100",
                "alice",
                ["alice", "bob"],
                SplitType.EXACT,
                {"alice": "10", "bob": "20"},
            )

        self.assertEqual(self.service.expenses, {})
        self.assertEqual(self.service.get_all_balances(), [])

    def test_group_requires_payer_and_participants_to_be_members(self) -> None:
        group = self.service.create_group("Trip", "alice", "trip")
        self.service.add_group_member(group.group_id, "bob")

        with self.assertRaises(ValueError):
            self.service.add_expense(
                "Hotel",
                "300",
                "alice",
                ["alice", "bob", "charlie"],
                SplitType.EQUAL,
                group_id=group.group_id,
            )

    def test_partial_and_complete_settlement(self) -> None:
        self.service.add_expense(
            "Dinner",
            "100",
            "alice",
            ["bob"],
            SplitType.EQUAL,
        )

        self.service.settle_up("bob", "alice", "40")
        self.assertEqual(
            self.service.balance_sheet.amount_owed("bob", "alice"),
            Decimal("60.00"),
        )
        self.service.settle_up("bob", "alice", "60")
        self.assertEqual(self.service.get_all_balances(), [])
        with self.assertRaises(ValueError):
            self.service.settle_up("bob", "alice", "1")

    def test_simplification_preserves_net_positions_and_reduces_transfers(self) -> None:
        sheet = BalanceSheet()
        sheet.add_debt("alice", "bob", "50")
        sheet.add_debt("bob", "charlie", "50")
        before = sheet.get_net_positions()

        simplified = sheet.simplify_debts()

        self.assertEqual(sheet.get_net_positions(), before)
        self.assertEqual(len(simplified), 1)
        self.assertEqual(simplified[0].debtor_id, "alice")
        self.assertEqual(simplified[0].creditor_id, "charlie")
        self.assertEqual(simplified[0].amount, Decimal("50.00"))

    def test_group_and_user_expense_history(self) -> None:
        group = self.service.create_group("Trip", "alice", "trip")
        self.service.add_group_member("trip", "bob")
        expense = self.service.add_expense(
            "Train",
            "200",
            "alice",
            ["alice", "bob"],
            SplitType.EQUAL,
            group_id="trip",
        )

        self.assertEqual(self.service.get_group_expenses("trip"), [expense])
        self.assertEqual(self.service.get_user_expenses("bob"), [expense])

    def test_duplicate_users_members_and_participants_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.service.create_user("Another Alice", "ALICE@example.com")

        group = self.service.create_group("Trip", "alice", "trip")
        self.service.add_group_member("trip", "bob")
        with self.assertRaises(ValueError):
            self.service.add_group_member("trip", "bob")
        with self.assertRaises(ValueError):
            self.service.add_expense(
                "Duplicate participants",
                "50",
                "alice",
                ["alice", "alice"],
                SplitType.EQUAL,
            )


if __name__ == "__main__":
    unittest.main()
