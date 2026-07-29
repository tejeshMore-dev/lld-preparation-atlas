from decimal import Decimal, ROUND_DOWN
from typing import Mapping

from models.money import CENT, MoneyInput
from models.split import Split
from strategies.split_strategy import SplitStrategy


class EqualSplitStrategy(SplitStrategy):
    def calculate(
        self,
        total: Decimal,
        participant_ids: list[str],
        values: Mapping[str, MoneyInput] | None = None,
    ) -> list[Split]:
        if values is not None:
            raise ValueError("Equal split does not accept custom values")

        base = (total / len(participant_ids)).quantize(CENT, rounding=ROUND_DOWN)
        remaining_cents = int((total - base * len(participant_ids)) / CENT)

        return [
            Split(user_id, base + (CENT if index < remaining_cents else Decimal("0")))
            for index, user_id in enumerate(participant_ids)
        ]
