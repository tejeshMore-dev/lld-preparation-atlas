from decimal import Decimal, ROUND_DOWN
from typing import Mapping

from models.money import CENT, MoneyInput, to_money
from models.split import Split
from strategies.split_strategy import SplitStrategy


class PercentageSplitStrategy(SplitStrategy):
    def calculate(
        self,
        total: Decimal,
        participant_ids: list[str],
        values: Mapping[str, MoneyInput] | None = None,
    ) -> list[Split]:
        if values is None:
            raise ValueError("Percentage split requires a percentage for every participant")
        if set(values) != set(participant_ids):
            raise ValueError("Percentage values must match the participants")

        percentages = {user_id: to_money(values[user_id]) for user_id in participant_ids}
        if any(percentage < 0 for percentage in percentages.values()):
            raise ValueError("Percentages cannot be negative")
        if sum(percentages.values(), Decimal("0")) != Decimal("100.00"):
            raise ValueError("Percentages must add up to 100")

        raw_amounts = {
            user_id: total * percentages[user_id] / Decimal("100")
            for user_id in participant_ids
        }
        amounts = {
            user_id: raw_amounts[user_id].quantize(CENT, rounding=ROUND_DOWN)
            for user_id in participant_ids
        }
        remaining_cents = int((total - sum(amounts.values(), Decimal("0"))) / CENT)
        priority = sorted(
            participant_ids,
            key=lambda user_id: raw_amounts[user_id] - amounts[user_id],
            reverse=True,
        )
        for user_id in priority[:remaining_cents]:
            amounts[user_id] += CENT

        return [Split(user_id, amounts[user_id]) for user_id in participant_ids]
