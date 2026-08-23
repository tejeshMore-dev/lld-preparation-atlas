from abc import ABC, abstractmethod


class CashSelectionStrategy(ABC):
    @abstractmethod
    def select_notes(
        self,
        amount: int,
        inventory: dict[int, int],
    ) -> dict[int, int] | None:
        raise NotImplementedError
