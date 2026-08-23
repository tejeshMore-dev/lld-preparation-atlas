from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Mapping

from models.money import MoneyInput
from models.split import Split


class SplitStrategy(ABC):
    @abstractmethod
    def calculate(
        self,
        total: Decimal,
        participant_ids: list[str],
        values: Mapping[str, MoneyInput] | None = None,
    ) -> list[Split]:
        raise NotImplementedError
