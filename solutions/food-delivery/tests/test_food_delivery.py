import threading
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from models.customer import Customer
from models.delivery_partner import DeliveryPartner
from models.enums import (
    DeliveryPartnerStatus,
    MenuItemStatus,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    RestaurantStatus,
)
from models.location import Location
from models.menu_item import MenuItem
from models.money import to_money
from models.restaurant import Restaurant
from services.catalog_service import CatalogService
from services.clock import Clock
from services.food_delivery_service import FoodDeliveryService
from services.in_memory_payment_gateway import InMemoryPaymentGateway
from strategies.free_delivery_decorator import FreeDeliveryDecorator
from strategies.haversine_distance_strategy import HaversineDistanceStrategy
from strategies.nearest_partner_strategy import NearestPartnerStrategy
from strategies.standard_pricing_strategy import StandardPricingStrategy


class MutableClock(Clock):
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current

    def advance(self, **kwargs) -> None:
        self.current += timedelta(**kwargs)


class FoodDeliveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = MutableClock(datetime(2030, 1, 1, 10, 0))
        self.catalog = CatalogService()
        self.catalog.add_customer(Customer("c1", "Asha", "asha@example.com", "9000000001"))
        self.catalog.add_customer(Customer("c2", "Ravi", "ravi@example.com", "9000000002"))
        self.restaurant_location = Location(12.9716, 77.5946)
        self.delivery_location = Location(12.9352, 77.6245)
        self.catalog.add_restaurant(
            Restaurant("r1", "Design Diner", "Continental", self.restaurant_location)
        )
        self.catalog.add_menu_item(
            "r1", MenuItem("i1", "Burger", "Classic burger", "200", False)
        )
        self.catalog.add_menu_item(
            "r1", MenuItem("i2", "Fries", "Crispy fries", "100", True)
        )
        self.catalog.add_restaurant(
            Restaurant(
                "r2",
                "Pattern Pizza",
                "Italian",
                Location(12.9800, 77.6000),
            )
        )
        self.catalog.add_menu_item(
            "r2", MenuItem("p1", "Margherita", "Cheese pizza", "300", True)
        )

        self.partner1 = DeliveryPartner(
            "dp1", "Deepa", "9111111111", Location(12.9720, 77.5950)
        )
        self.partner2 = DeliveryPartner(
            "dp2", "Manoj", "9222222222", Location(12.9900, 77.6000)
        )
        self.catalog.add_delivery_partner(self.partner1)
        self.catalog.add_delivery_partner(self.partner2)

        self.distance = HaversineDistanceStrategy()
        self.pricing = StandardPricingStrategy()
        self.gateway = InMemoryPaymentGateway(self.clock)
        self.service = FoodDeliveryService(
            self.catalog,
            self.distance,
            self.pricing,
            NearestPartnerStrategy(self.distance),
            self.gateway,
            self.clock,
        )
        self.service.go_online("dp1")
        self.service.go_online("dp2")

    def add_standard_cart(self, customer_id: str = "c1") -> None:
        self.service.add_to_cart(customer_id, "r1", "i1", 2)
        self.service.add_to_cart(customer_id, "r1", "i2", 1)

    def create_order(self, customer_id: str = "c1"):
        self.add_standard_cart(customer_id)
        return self.service.checkout(customer_id, self.delivery_location)

    def create_paid_ready_order(self, customer_id: str = "c1"):
        order = self.create_order(customer_id)
        self.service.pay_for_order(order.order_id, PaymentMethod.UPI)
        self.service.start_preparing(order.order_id)
        self.service.mark_ready_for_pickup(order.order_id)
        return order

    def test_location_and_restaurant_search_filters(self) -> None:
        with self.assertRaisesRegex(ValueError, "Latitude"):
            Location(100, 0)
        restaurants = self.service.search_restaurants(
            self.delivery_location,
            cuisine="continental",
            max_distance_km="10",
        )
        self.assertEqual(["r1"], [restaurant.restaurant_id for restaurant in restaurants])
        self.catalog.set_restaurant_status("r1", RestaurantStatus.CLOSED)
        self.assertEqual([], self.service.search_restaurants(self.delivery_location, "Continental"))

    def test_cart_accumulates_quantity_and_enforces_one_restaurant(self) -> None:
        self.service.add_to_cart("c1", "r1", "i1", 1)
        cart = self.service.add_to_cart("c1", "r1", "i1", 2)
        self.assertEqual(3, cart.quantities["i1"])
        with self.assertRaisesRegex(ValueError, "one restaurant"):
            self.service.add_to_cart("c1", "r2", "p1", 1)

    def test_unavailable_item_is_rejected_at_cart_and_checkout(self) -> None:
        self.catalog.set_menu_item_status("r1", "i1", MenuItemStatus.UNAVAILABLE)
        with self.assertRaisesRegex(ValueError, "unavailable"):
            self.service.add_to_cart("c1", "r1", "i1", 1)
        self.catalog.set_menu_item_status("r1", "i1", MenuItemStatus.AVAILABLE)
        self.service.add_to_cart("c1", "r1", "i1", 1)
        self.catalog.set_menu_item_status("r1", "i1", MenuItemStatus.UNAVAILABLE)
        with self.assertRaisesRegex(ValueError, "became unavailable"):
            self.service.checkout("c1", self.delivery_location)

    def test_checkout_snapshots_lines_and_itemized_pricing(self) -> None:
        order = self.create_order()
        self.assertEqual(Decimal("500.00"), order.pricing.subtotal)
        self.assertEqual(Decimal("25.00"), order.pricing.tax)
        expected_delivery = to_money(
            Decimal("30") + Decimal("8") * order.delivery_distance_km
        )
        self.assertEqual(expected_delivery, order.pricing.delivery_fee)
        self.assertEqual(
            to_money(Decimal("500") + Decimal("25") + expected_delivery),
            order.total_amount,
        )
        self.assertTrue(self.service.get_cart("c1").is_empty)

    def test_order_line_price_is_immutable_snapshot(self) -> None:
        order = self.create_order()
        self.catalog.get_menu_item("r1", "i1").price = Decimal("999.00")
        burger_line = next(line for line in order.lines if line.item_id == "i1")
        self.assertEqual(Decimal("200.00"), burger_line.unit_price)
        self.assertEqual(Decimal("400.00"), burger_line.line_total)

    def test_free_delivery_decorator(self) -> None:
        free_service = FoodDeliveryService(
            self.catalog,
            self.distance,
            FreeDeliveryDecorator(self.pricing, "500"),
            NearestPartnerStrategy(self.distance),
            self.gateway,
            self.clock,
        )
        free_service.add_to_cart("c1", "r1", "i1", 2)
        free_service.add_to_cart("c1", "r1", "i2", 1)
        order = free_service.checkout("c1", self.delivery_location)
        self.assertEqual(Decimal("0.00"), order.pricing.delivery_fee)
        self.assertEqual(Decimal("525.00"), order.total_amount)

    def test_payment_failure_retry_and_idempotency(self) -> None:
        order = self.create_order()
        self.gateway.fail_next_charge = True
        failed = self.service.pay_for_order(order.order_id, PaymentMethod.CARD)
        self.assertIs(PaymentStatus.FAILED, failed.status)
        self.assertIs(OrderStatus.PENDING_PAYMENT, order.status)
        completed = self.service.pay_for_order(order.order_id, PaymentMethod.UPI)
        repeated = self.service.pay_for_order(order.order_id, PaymentMethod.UPI)
        self.assertIs(PaymentStatus.COMPLETED, completed.status)
        self.assertIs(completed, repeated)
        self.assertIs(OrderStatus.CONFIRMED, order.status)
        self.assertEqual(2, len(order.payment_ids))

    def test_restaurant_preparation_transition_order_is_enforced(self) -> None:
        order = self.create_order()
        with self.assertRaisesRegex(ValueError, "preparing"):
            self.service.mark_ready_for_pickup(order.order_id)
        self.service.pay_for_order(order.order_id, PaymentMethod.CARD)
        self.service.start_preparing(order.order_id)
        self.service.mark_ready_for_pickup(order.order_id)
        self.assertIs(OrderStatus.READY_FOR_PICKUP, order.status)

    def test_nearest_available_partner_is_assigned_once(self) -> None:
        order = self.create_paid_ready_order()
        partner = self.service.assign_delivery_partner(order.order_id)
        repeated = self.service.assign_delivery_partner(order.order_id)
        self.assertEqual("dp1", partner.partner_id)
        self.assertIs(partner, repeated)
        self.assertIs(DeliveryPartnerStatus.ON_DELIVERY, self.partner1.status)

    def test_ready_order_can_retry_assignment_when_partner_comes_online(self) -> None:
        self.service.go_offline("dp1")
        self.service.go_offline("dp2")
        order = self.create_paid_ready_order()
        self.assertIsNone(self.service.assign_delivery_partner(order.order_id))
        self.service.go_online("dp1")
        self.assertEqual("dp1", self.service.assign_delivery_partner(order.order_id).partner_id)

    def test_only_assigned_partner_can_pick_up_and_deliver(self) -> None:
        order = self.create_paid_ready_order()
        partner = self.service.assign_delivery_partner(order.order_id)
        with self.assertRaisesRegex(ValueError, "assigned"):
            self.service.pick_up_order(order.order_id, "dp2")
        self.service.pick_up_order(order.order_id, partner.partner_id)
        with self.assertRaisesRegex(ValueError, "assigned"):
            self.service.deliver_order(order.order_id, "dp2")
        self.service.deliver_order(order.order_id, partner.partner_id)
        with self.assertRaisesRegex(ValueError, "assigned"):
            self.service.deliver_order(order.order_id, "dp2")

    def test_delivery_releases_partner_and_updates_location(self) -> None:
        order = self.create_paid_ready_order()
        partner = self.service.assign_delivery_partner(order.order_id)
        self.service.pick_up_order(order.order_id, partner.partner_id)
        self.service.deliver_order(order.order_id, partner.partner_id)
        self.assertIs(OrderStatus.DELIVERED, order.status)
        self.assertIs(DeliveryPartnerStatus.AVAILABLE, partner.status)
        self.assertEqual(self.delivery_location, partner.location)

    def test_pending_cancellation_needs_no_refund(self) -> None:
        order = self.create_order()
        self.service.cancel_order(order.order_id, "Changed plans")
        self.assertIs(OrderStatus.CANCELLED, order.status)
        self.assertEqual([], order.payment_ids)

    def test_paid_cancellation_refunds_and_releases_partner(self) -> None:
        order = self.create_paid_ready_order()
        payment = self.service.payments[order.payment_ids[-1]]
        partner = self.service.assign_delivery_partner(order.order_id)
        self.service.cancel_order(order.order_id, "Restaurant issue")
        self.assertIs(PaymentStatus.REFUNDED, payment.status)
        self.assertIs(OrderStatus.CANCELLED, order.status)
        self.assertIs(DeliveryPartnerStatus.AVAILABLE, partner.status)

    def test_out_for_delivery_order_cannot_be_cancelled(self) -> None:
        order = self.create_paid_ready_order()
        partner = self.service.assign_delivery_partner(order.order_id)
        self.service.pick_up_order(order.order_id, partner.partner_id)
        with self.assertRaisesRegex(ValueError, "OUT_FOR_DELIVERY"):
            self.service.cancel_order(order.order_id, "Too late")

    def test_partner_cannot_go_offline_while_reserved(self) -> None:
        order = self.create_paid_ready_order()
        partner = self.service.assign_delivery_partner(order.order_id)
        with self.assertRaisesRegex(ValueError, "cannot go offline"):
            self.service.go_offline(partner.partner_id)

    def test_customer_and_restaurant_histories_are_newest_first(self) -> None:
        first = self.create_order()
        self.clock.advance(seconds=1)
        self.add_standard_cart()
        second = self.service.checkout("c1", self.delivery_location)
        self.assertEqual([second, first], self.service.get_customer_orders("c1"))
        self.assertEqual([second, first], self.service.get_restaurant_orders("r1"))

    def test_concurrent_orders_assign_one_available_partner_once(self) -> None:
        self.service.go_offline("dp2")
        first = self.create_paid_ready_order("c1")
        second = self.create_paid_ready_order("c2")
        barrier = threading.Barrier(2)
        results = []

        def assign(order_id: str) -> None:
            barrier.wait()
            results.append(self.service.assign_delivery_partner(order_id))

        threads = [
            threading.Thread(target=assign, args=(first.order_id,)),
            threading.Thread(target=assign, args=(second.order_id,)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(1, sum(partner is not None for partner in results))
        self.assertEqual(1, sum(order.delivery_partner_id == "dp1" for order in (first, second)))


if __name__ == "__main__":
    unittest.main()
