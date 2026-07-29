import uuid
from datetime import datetime
from decimal import Decimal
from typing import Mapping

from models.balance import Balance
from models.enums import SplitType
from models.expense import Expense
from models.group import Group
from models.money import MoneyInput, to_money
from models.settlement import Settlement
from models.user import User
from services.balance_sheet import BalanceSheet
from strategies.split_strategy_factory import SplitStrategyFactory


class SplitwiseService:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.groups: dict[str, Group] = {}
        self.expenses: dict[str, Expense] = {}
        self.settlements: list[Settlement] = []
        self.balance_sheet = BalanceSheet()

    def create_user(
        self,
        name: str,
        email: str,
        user_id: str | None = None,
    ) -> User:
        if not name.strip():
            raise ValueError("User name cannot be empty")
        normalized_email = email.strip().lower()
        if not normalized_email or "@" not in normalized_email:
            raise ValueError("A valid email is required")
        if any(user.email == normalized_email for user in self.users.values()):
            raise ValueError("A user with this email already exists")

        identifier = user_id or str(uuid.uuid4())
        if identifier in self.users:
            raise ValueError("User ID already exists")
        user = User(identifier, name.strip(), normalized_email)
        self.users[identifier] = user
        return user

    def create_group(
        self,
        name: str,
        created_by_id: str,
        group_id: str | None = None,
    ) -> Group:
        self._get_user(created_by_id)
        if not name.strip():
            raise ValueError("Group name cannot be empty")

        identifier = group_id or str(uuid.uuid4())
        if identifier in self.groups:
            raise ValueError("Group ID already exists")
        group = Group(
            group_id=identifier,
            name=name.strip(),
            created_by_id=created_by_id,
            member_ids={created_by_id},
        )
        self.groups[identifier] = group
        return group

    def add_group_member(self, group_id: str, user_id: str) -> None:
        group = self._get_group(group_id)
        self._get_user(user_id)
        group.add_member(user_id)

    def add_expense(
        self,
        description: str,
        amount: MoneyInput,
        paid_by_id: str,
        participant_ids: list[str],
        split_type: SplitType,
        split_values: Mapping[str, MoneyInput] | None = None,
        group_id: str | None = None,
        expense_id: str | None = None,
    ) -> Expense:
        if not description.strip():
            raise ValueError("Expense description cannot be empty")
        total = to_money(amount)
        if total <= 0:
            raise ValueError("Expense amount must be greater than zero")

        self._get_user(paid_by_id)
        participants = self._validate_participants(participant_ids)
        group = self._get_group(group_id) if group_id is not None else None
        if group is not None:
            required_members = set(participants) | {paid_by_id}
            if not required_members.issubset(group.member_ids):
                raise ValueError("Payer and participants must belong to the group")

        identifier = expense_id or str(uuid.uuid4())
        if identifier in self.expenses:
            raise ValueError("Expense ID already exists")

        strategy = SplitStrategyFactory.get_strategy(split_type)
        splits = tuple(strategy.calculate(total, participants, split_values))
        expense = Expense(
            expense_id=identifier,
            description=description.strip(),
            amount=total,
            paid_by_id=paid_by_id,
            splits=splits,
            split_type=split_type,
            created_at=datetime.now(),
            group_id=group_id,
        )

        self.expenses[identifier] = expense
        if group is not None:
            group.expense_ids.append(identifier)
        for split in splits:
            self.balance_sheet.add_debt(split.user_id, paid_by_id, split.amount)
        return expense

    def settle_up(
        self,
        paid_by_id: str,
        paid_to_id: str,
        amount: MoneyInput,
    ) -> Settlement:
        self._get_user(paid_by_id)
        self._get_user(paid_to_id)
        payment = to_money(amount)
        self.balance_sheet.settle_debt(paid_by_id, paid_to_id, payment)

        settlement = Settlement(
            settlement_id=str(uuid.uuid4()),
            paid_by_id=paid_by_id,
            paid_to_id=paid_to_id,
            amount=payment,
            created_at=datetime.now(),
        )
        self.settlements.append(settlement)
        return settlement

    def get_all_balances(self) -> list[Balance]:
        return self.balance_sheet.get_all_balances()

    def get_user_balances(self, user_id: str) -> list[Balance]:
        self._get_user(user_id)
        return self.balance_sheet.get_user_balances(user_id)

    def simplify_debts(self) -> list[Balance]:
        return self.balance_sheet.simplify_debts()

    def get_group_expenses(self, group_id: str) -> list[Expense]:
        group = self._get_group(group_id)
        return [self.expenses[expense_id] for expense_id in group.expense_ids]

    def get_user_expenses(self, user_id: str) -> list[Expense]:
        self._get_user(user_id)
        return [
            expense
            for expense in self.expenses.values()
            if expense.paid_by_id == user_id
            or any(split.user_id == user_id for split in expense.splits)
        ]

    def format_balances(self) -> list[str]:
        return [
            f"{self.users[balance.debtor_id].name} owes "
            f"{self.users[balance.creditor_id].name} INR {balance.amount:.2f}"
            for balance in self.get_all_balances()
        ]

    def _validate_participants(self, participant_ids: list[str]) -> list[str]:
        if not participant_ids:
            raise ValueError("An expense requires at least one participant")
        if len(participant_ids) != len(set(participant_ids)):
            raise ValueError("Expense participants must be unique")
        for user_id in participant_ids:
            self._get_user(user_id)
        return list(participant_ids)

    def _get_user(self, user_id: str) -> User:
        try:
            return self.users[user_id]
        except KeyError as error:
            raise ValueError(f'User "{user_id}" not found') from error

    def _get_group(self, group_id: str | None) -> Group:
        if group_id is None:
            raise ValueError("Group ID is required")
        try:
            return self.groups[group_id]
        except KeyError as error:
            raise ValueError(f'Group "{group_id}" not found') from error
