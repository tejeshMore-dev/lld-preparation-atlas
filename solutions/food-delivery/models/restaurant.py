from dataclasses import dataclass, field

from models.enums import RestaurantStatus
from models.location import Location
from models.menu_item import MenuItem


@dataclass
class Restaurant:
    restaurant_id: str
    name: str
    cuisine: str
    location: Location
    status: RestaurantStatus = RestaurantStatus.OPEN
    menu: dict[str, MenuItem] = field(default_factory=dict)

    def add_menu_item(self, item: MenuItem) -> None:
        if item.item_id in self.menu:
            raise ValueError(f"Menu item '{item.item_id}' already exists")
        if any(existing.name.casefold() == item.name.casefold() for existing in self.menu.values()):
            raise ValueError(f"Menu item name '{item.name}' already exists")
        if item.price <= 0:
            raise ValueError("Menu item price must be positive")
        self.menu[item.item_id] = item
