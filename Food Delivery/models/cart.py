from dataclasses import dataclass, field


@dataclass
class Cart:
    customer_id: str
    restaurant_id: str | None = None
    quantities: dict[str, int] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.quantities

    def clear(self) -> None:
        self.restaurant_id = None
        self.quantities.clear()
