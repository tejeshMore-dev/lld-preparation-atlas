from strategies.cash_selection_strategy import CashSelectionStrategy


class CashDispenser:
    def __init__(
        self,
        inventory: dict[int, int],
        selection_strategy: CashSelectionStrategy,
    ) -> None:
        if not inventory:
            raise ValueError("Cash dispenser requires at least one denomination")
        if any(
            not isinstance(denomination, int) or denomination <= 0
            for denomination in inventory
        ):
            raise ValueError("Denominations must be positive integers")
        if any(not isinstance(count, int) or count < 0 for count in inventory.values()):
            raise ValueError("Note counts must be non-negative integers")

        self.inventory = dict(inventory)
        self.selection_strategy = selection_strategy

    @property
    def total_cash(self) -> int:
        return sum(
            denomination * count
            for denomination, count in self.inventory.items()
        )

    def prepare_dispense(self, amount: int) -> dict[int, int] | None:
        if not isinstance(amount, int) or amount <= 0:
            raise ValueError("Dispense amount must be a positive whole number")
        return self.selection_strategy.select_notes(amount, self.inventory)

    def dispense(self, notes: dict[int, int]) -> None:
        self.validate_notes(notes)
        if any(self.inventory[denomination] < count for denomination, count in notes.items()):
            raise ValueError("Cash inventory changed before dispensing")
        for denomination, count in notes.items():
            self.inventory[denomination] -= count

    def load_cash(self, notes: dict[int, int]) -> int:
        total = self.validate_notes(notes)
        for denomination, count in notes.items():
            self.inventory[denomination] += count
        return total

    def validate_notes(self, notes: dict[int, int]) -> int:
        if not notes:
            raise ValueError("At least one note is required")
        if any(denomination not in self.inventory for denomination in notes):
            raise ValueError("Unsupported cash denomination")
        if any(not isinstance(count, int) or count <= 0 for count in notes.values()):
            raise ValueError("Deposited note counts must be positive integers")
        return sum(denomination * count for denomination, count in notes.items())
