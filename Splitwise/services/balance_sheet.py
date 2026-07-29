from collections import defaultdict
from decimal import Decimal

from models.balance import Balance
from models.money import MoneyInput, to_money


class BalanceSheet:
    """Stores normalized positive debts as (debtor, creditor) -> amount."""

    def __init__(self) -> None:
        self._debts: dict[tuple[str, str], Decimal] = {}

    def add_debt(
        self,
        debtor_id: str,
        creditor_id: str,
        amount: MoneyInput,
    ) -> None:
        debt = to_money(amount)
        if debt < 0:
            raise ValueError("Debt amount cannot be negative")
        if debt == 0 or debtor_id == creditor_id:
            return

        direct_key = (debtor_id, creditor_id)
        reverse_key = (creditor_id, debtor_id)
        reverse_debt = self._debts.get(reverse_key, Decimal("0.00"))

        if reverse_debt > debt:
            self._debts[reverse_key] = reverse_debt - debt
            return
        if reverse_debt == debt:
            self._debts.pop(reverse_key, None)
            return
        if reverse_debt:
            self._debts.pop(reverse_key)
            debt -= reverse_debt

        self._debts[direct_key] = self._debts.get(
            direct_key,
            Decimal("0.00"),
        ) + debt

    def settle_debt(
        self,
        debtor_id: str,
        creditor_id: str,
        amount: MoneyInput,
    ) -> Decimal:
        payment = to_money(amount)
        if payment <= 0:
            raise ValueError("Settlement amount must be greater than zero")

        key = (debtor_id, creditor_id)
        outstanding = self._debts.get(key, Decimal("0.00"))
        if outstanding == 0:
            raise ValueError("No outstanding balance exists in this direction")
        if payment > outstanding:
            raise ValueError("Settlement amount exceeds the outstanding balance")

        remaining = outstanding - payment
        if remaining == 0:
            self._debts.pop(key)
        else:
            self._debts[key] = remaining
        return remaining

    def amount_owed(self, debtor_id: str, creditor_id: str) -> Decimal:
        return self._debts.get((debtor_id, creditor_id), Decimal("0.00"))

    def get_all_balances(self) -> list[Balance]:
        return [
            Balance(debtor_id, creditor_id, amount)
            for (debtor_id, creditor_id), amount in sorted(self._debts.items())
        ]

    def get_user_balances(self, user_id: str) -> list[Balance]:
        return [
            balance
            for balance in self.get_all_balances()
            if user_id in (balance.debtor_id, balance.creditor_id)
        ]

    def get_net_positions(self) -> dict[str, Decimal]:
        positions: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for (debtor_id, creditor_id), amount in self._debts.items():
            positions[debtor_id] -= amount
            positions[creditor_id] += amount
        return {
            user_id: amount
            for user_id, amount in positions.items()
            if amount != 0
        }

    def simplify_debts(self) -> list[Balance]:
        """Rebuild debts while preserving every user's net position."""
        positions = self.get_net_positions()
        debtors = sorted(
            [[user_id, -amount] for user_id, amount in positions.items() if amount < 0]
        )
        creditors = sorted(
            [[user_id, amount] for user_id, amount in positions.items() if amount > 0]
        )

        self._debts.clear()
        debtor_index = 0
        creditor_index = 0
        while debtor_index < len(debtors) and creditor_index < len(creditors):
            debtor_id, debt = debtors[debtor_index]
            creditor_id, credit = creditors[creditor_index]
            transfer = min(debt, credit)
            self.add_debt(debtor_id, creditor_id, transfer)

            debtors[debtor_index][1] -= transfer
            creditors[creditor_index][1] -= transfer
            if debtors[debtor_index][1] == 0:
                debtor_index += 1
            if creditors[creditor_index][1] == 0:
                creditor_index += 1

        return self.get_all_balances()
