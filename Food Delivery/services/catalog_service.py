from models.customer import Customer
from models.delivery_partner import DeliveryPartner
from models.enums import DeliveryPartnerStatus, MenuItemStatus, RestaurantStatus
from models.menu_item import MenuItem
from models.money import to_money
from models.restaurant import Restaurant


class CatalogService:
    """Manages stable customer, restaurant, menu, and partner registration data."""

    def __init__(self) -> None:
        self.customers: dict[str, Customer] = {}
        self.restaurants: dict[str, Restaurant] = {}
        self.delivery_partners: dict[str, DeliveryPartner] = {}

    def add_customer(self, customer: Customer) -> None:
        if customer.customer_id in self.customers:
            raise ValueError(f"Customer '{customer.customer_id}' already exists")
        if any(existing.email.casefold() == customer.email.casefold() for existing in self.customers.values()):
            raise ValueError(f"Email '{customer.email}' is already registered")
        self.customers[customer.customer_id] = customer

    def add_restaurant(self, restaurant: Restaurant) -> None:
        if restaurant.restaurant_id in self.restaurants:
            raise ValueError(f"Restaurant '{restaurant.restaurant_id}' already exists")
        self.restaurants[restaurant.restaurant_id] = restaurant

    def add_menu_item(self, restaurant_id: str, item: MenuItem) -> None:
        item.price = to_money(item.price)
        self.get_restaurant(restaurant_id).add_menu_item(item)

    def set_restaurant_status(
        self,
        restaurant_id: str,
        status: RestaurantStatus,
    ) -> Restaurant:
        restaurant = self.get_restaurant(restaurant_id)
        restaurant.status = status
        return restaurant

    def set_menu_item_status(
        self,
        restaurant_id: str,
        item_id: str,
        status: MenuItemStatus,
    ) -> MenuItem:
        item = self.get_menu_item(restaurant_id, item_id)
        item.status = status
        return item

    def add_delivery_partner(self, partner: DeliveryPartner) -> None:
        if partner.partner_id in self.delivery_partners:
            raise ValueError(f"Delivery partner '{partner.partner_id}' already exists")
        if partner.status is DeliveryPartnerStatus.ON_DELIVERY:
            raise ValueError("New delivery partner cannot already be on a delivery")
        if any(existing.phone == partner.phone for existing in self.delivery_partners.values()):
            raise ValueError(f"Partner phone '{partner.phone}' is already registered")
        self.delivery_partners[partner.partner_id] = partner

    def get_customer(self, customer_id: str) -> Customer:
        try:
            return self.customers[customer_id]
        except KeyError as error:
            raise ValueError(f"Customer '{customer_id}' does not exist") from error

    def get_restaurant(self, restaurant_id: str) -> Restaurant:
        try:
            return self.restaurants[restaurant_id]
        except KeyError as error:
            raise ValueError(f"Restaurant '{restaurant_id}' does not exist") from error

    def get_menu_item(self, restaurant_id: str, item_id: str) -> MenuItem:
        restaurant = self.get_restaurant(restaurant_id)
        try:
            return restaurant.menu[item_id]
        except KeyError as error:
            raise ValueError(f"Menu item '{item_id}' does not exist") from error

    def get_delivery_partner(self, partner_id: str) -> DeliveryPartner:
        try:
            return self.delivery_partners[partner_id]
        except KeyError as error:
            raise ValueError(f"Delivery partner '{partner_id}' does not exist") from error
