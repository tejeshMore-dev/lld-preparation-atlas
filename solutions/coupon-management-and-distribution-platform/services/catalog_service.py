from models.merchant import Merchant
from models.user import User


class CatalogService:
    """Manages stable merchant and user registration data."""

    def __init__(self) -> None:
        self.merchants: dict[str, Merchant] = {}
        self.users: dict[str, User] = {}

    def add_merchant(self, merchant: Merchant) -> None:
        if merchant.merchant_id in self.merchants:
            raise ValueError(f"Merchant '{merchant.merchant_id}' already exists")
        if any(existing.email.casefold() == merchant.email.casefold() for existing in self.merchants.values()):
            raise ValueError(f"Merchant email '{merchant.email}' is already registered")
        self.merchants[merchant.merchant_id] = merchant

    def add_user(self, user: User) -> None:
        if user.user_id in self.users:
            raise ValueError(f"User '{user.user_id}' already exists")
        if user.loyalty_points < 0:
            raise ValueError("Loyalty points cannot be negative")
        if any(existing.email.casefold() == user.email.casefold() for existing in self.users.values()):
            raise ValueError(f"User email '{user.email}' is already registered")
        self.users[user.user_id] = user

    def get_merchant(self, merchant_id: str) -> Merchant:
        try:
            return self.merchants[merchant_id]
        except KeyError as error:
            raise ValueError(f"Merchant '{merchant_id}' does not exist") from error

    def get_user(self, user_id: str) -> User:
        try:
            return self.users[user_id]
        except KeyError as error:
            raise ValueError(f"User '{user_id}' does not exist") from error
