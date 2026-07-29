from dataclasses import dataclass
from decimal import Decimal

from models.enums import MenuItemStatus


@dataclass
class MenuItem:
    item_id: str
    name: str
    description: str
    price: Decimal
    is_vegetarian: bool
    status: MenuItemStatus = MenuItemStatus.AVAILABLE
