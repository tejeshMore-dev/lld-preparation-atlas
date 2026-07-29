from decimal import Decimal
from typing import Mapping

from models.money import MoneyInput, to_money
from models.split import Split
from strategies.split_strategy import SplitStrategy


class ExactSplitStrategy(SplitStrategy):
    def calculate(
        self,
        total: Decimal,
        participant_ids: list[str],
        values: Mapping[str, MoneyInput] | None = None,
    ) -> list[Split]:
        if values is None:
            raise ValueError("Exact split requires an amount for every participant")
        if set(values) != set(participant_ids):
            raise ValueError("Exact split values must match the participants")

        splits = [Split(user_id, to_money(values[user_id])) for user_id in participant_ids]
        if any(split.amount < 0 for split in splits):
            raise ValueError("Exact split amounts cannot be negative")
        if sum((split.amount for split in splits), Decimal("0")) != total:
            raise ValueError("Exact split amounts must add up to the expense total")
        return splits
