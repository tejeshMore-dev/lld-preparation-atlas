from datetime import datetime, timedelta

from models.customer import Customer
from models.delivery_partner import DeliveryPartner
from models.enums import PaymentMethod
from models.location import Location
from models.menu_item import MenuItem
from models.restaurant import Restaurant
from services.catalog_service import CatalogService
from services.clock import Clock
from services.food_delivery_service import FoodDeliveryService
from services.in_memory_payment_gateway import InMemoryPaymentGateway
from strategies.haversine_distance_strategy import HaversineDistanceStrategy
from strategies.nearest_partner_strategy import NearestPartnerStrategy
from strategies.standard_pricing_strategy import StandardPricingStrategy


class DemoClock(Clock):
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current


def build_demo() -> tuple[FoodDeliveryService, DemoClock]:
    clock = DemoClock(datetime.now())
    catalog = CatalogService()
    catalog.add_customer(Customer("customer-1", "Asha", "asha@example.com", "9000000001"))
    restaurant_location = Location(12.9716, 77.5946)
    catalog.add_restaurant(
        Restaurant("restaurant-1", "Design Diner", "Continental", restaurant_location)
    )
    catalog.add_menu_item(
        "restaurant-1", MenuItem("burger", "Burger", "Classic burger", "200", False)
    )
    catalog.add_menu_item(
        "restaurant-1", MenuItem("fries", "Fries", "Crispy fries", "100", True)
    )
    catalog.add_delivery_partner(
        DeliveryPartner("partner-1", "Deepa", "9111111111", Location(12.972, 77.595))
    )
    distance = HaversineDistanceStrategy()
    service = FoodDeliveryService(
        catalog,
        distance,
        StandardPricingStrategy(),
        NearestPartnerStrategy(distance),
        InMemoryPaymentGateway(clock),
        clock,
    )
    service.go_online("partner-1")
    return service, clock


def main() -> None:
    service, clock = build_demo()
    delivery_location = Location(12.9352, 77.6245)
    restaurants = service.search_restaurants(delivery_location)
    print("Nearby restaurants:", [restaurant.name for restaurant in restaurants])
    service.add_to_cart("customer-1", "restaurant-1", "burger", 2)
    service.add_to_cart("customer-1", "restaurant-1", "fries", 1)
    order = service.checkout("customer-1", delivery_location)
    print(
        f"Subtotal Rs. {order.pricing.subtotal}; delivery Rs. "
        f"{order.pricing.delivery_fee}; total Rs. {order.total_amount}"
    )
    payment = service.pay_for_order(order.order_id, PaymentMethod.UPI)
    service.start_preparing(order.order_id)
    clock.current += timedelta(minutes=20)
    service.mark_ready_for_pickup(order.order_id)
    partner = service.assign_delivery_partner(order.order_id)
    service.pick_up_order(order.order_id, partner.partner_id)
    clock.current += timedelta(minutes=15)
    service.deliver_order(order.order_id, partner.partner_id)
    print(f"Payment {payment.status.name}; order {order.status.name} by {partner.name}")


if __name__ == "__main__":
    main()
