from functools import lru_cache

from strategies.cash_selection_strategy import CashSelectionStrategy


class ExactCashStrategy(CashSelectionStrategy):
    """Finds an exact bounded-note combination, preferring larger notes."""

    def select_notes(
        self,
        amount: int,
        inventory: dict[int, int],
    ) -> dict[int, int] | None:
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if amount == 0:
            return {}

        denominations = tuple(sorted(inventory, reverse=True))

        @lru_cache(maxsize=None)
        def search(index: int, remaining: int) -> tuple[tuple[int, int], ...] | None:
            if remaining == 0:
                return ()
            if index == len(denominations) or remaining < 0:
                return None

            denomination = denominations[index]
            maximum = min(inventory[denomination], remaining // denomination)
            for count in range(maximum, -1, -1):
                result = search(index + 1, remaining - denomination * count)
                if result is not None:
                    return ((denomination, count),) + result
            return None

        result = search(0, amount)
        if result is None:
            return None
        return {
            denomination: count
            for denomination, count in result
            if count > 0
        }
