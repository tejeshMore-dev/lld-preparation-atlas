from decimal import Decimal, InvalidOperation
from threading import RLock
from uuid import uuid4

from models.cart import Cart
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
from models.money import to_money
from models.order import Order, OrderLine
from models.payment import Payment
from models.restaurant import Restaurant
from services.catalog_service import CatalogService
from services.clock import Clock, SystemClock
from services.payment_gateway import PaymentGateway
from strategies.distance_strategy import DistanceStrategy
from strategies.matching_strategy import MatchingStrategy
from strategies.pricing_strategy import PricingStrategy


class FoodDeliveryService:
    """Coordinates carts, ordering, restaurant workflow, dispatch, and delivery."""

    def __init__(
        self,
        catalog: CatalogService,
        distance_strategy: DistanceStrategy,
        pricing_strategy: PricingStrategy,
        matching_strategy: MatchingStrategy,
        payment_gateway: PaymentGateway,
        clock: Clock | None = None,
        max_partner_distance_km: Decimal | int | float | str = "10",
    ) -> None:
        self._catalog = catalog
        self._distance_strategy = distance_strategy
        self._pricing_strategy = pricing_strategy
        self._matching_strategy = matching_strategy
        self._payment_gateway = payment_gateway
        self._clock = clock or SystemClock()
        self._max_partner_distance_km = self._to_distance(max_partner_distance_km)
        if self._max_partner_distance_km <= 0:
            raise ValueError("Partner search radius must be finite and positive")
        # Live partner ownership and order transitions share this atomic boundary.
        self._lock = RLock()
        self.carts: dict[str, Cart] = {}
        self.orders: dict[str, Order] = {}
        self.payments: dict[str, Payment] = {}

    def search_restaurants(
        self,
        delivery_location: Location,
        cuisine: str | None = None,
        max_distance_km: Decimal | int | float | str = "10",
    ) -> list[Restaurant]:
        radius = self._to_distance(max_distance_km)
        if radius <= 0:
            raise ValueError("Restaurant search radius must be finite and positive")
        cuisine_key = cuisine.strip().casefold() if cuisine is not None else None
        with self._lock:
            restaurants = [
                restaurant
                for restaurant in self._catalog.restaurants.values()
                if restaurant.status is RestaurantStatus.OPEN
                and (
                    cuisine_key is None
                    or restaurant.cuisine.strip().casefold() == cuisine_key
                )
                and self._distance_strategy.calculate_km(
                    restaurant.location,
                    delivery_location,
                )
                <= radius
            ]
            return sorted(
                restaurants,
                key=lambda restaurant: (
                    self._distance_strategy.calculate_km(
                        restaurant.location,
                        delivery_location,
                    ),
                    restaurant.name.casefold(),
                ),
            )

    def add_to_cart(
        self,
        customer_id: str,
        restaurant_id: str,
        item_id: str,
        quantity: int = 1,
    ) -> Cart:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        with self._lock:
            self._catalog.get_customer(customer_id)
            restaurant = self._catalog.get_restaurant(restaurant_id)
            if restaurant.status is not RestaurantStatus.OPEN:
                raise ValueError("Restaurant is closed")
            item = self._catalog.get_menu_item(restaurant_id, item_id)
            if item.status is not MenuItemStatus.AVAILABLE:
                raise ValueError(f"Menu item '{item_id}' is unavailable")
            cart = self.carts.setdefault(customer_id, Cart(customer_id))
            if cart.restaurant_id is not None and cart.restaurant_id != restaurant_id:
                raise ValueError("A cart can contain items from only one restaurant")
            cart.restaurant_id = restaurant_id
            cart.quantities[item_id] = cart.quantities.get(item_id, 0) + quantity
            return cart

    def update_cart_item(self, customer_id: str, item_id: str, quantity: int) -> Cart:
        with self._lock:
            cart = self.get_cart(customer_id)
            if item_id not in cart.quantities:
                raise ValueError(f"Menu item '{item_id}' is not in the cart")
            if quantity <= 0:
                del cart.quantities[item_id]
                if cart.is_empty:
                    cart.restaurant_id = None
            else:
                cart.quantities[item_id] = quantity
            return cart

    def clear_cart(self, customer_id: str) -> Cart:
        with self._lock:
            cart = self.get_cart(customer_id)
            cart.clear()
            return cart

    def checkout(self, customer_id: str, delivery_location: Location) -> Order:
        with self._lock:
            self._catalog.get_customer(customer_id)
            cart = self.get_cart(customer_id)
            if cart.is_empty or cart.restaurant_id is None:
                raise ValueError("Cannot checkout an empty cart")
            restaurant = self._catalog.get_restaurant(cart.restaurant_id)
            if restaurant.status is not RestaurantStatus.OPEN:
                raise ValueError("Restaurant is closed")

            lines = []
            subtotal = Decimal("0")
            for item_id, quantity in cart.quantities.items():
                item = self._catalog.get_menu_item(restaurant.restaurant_id, item_id)
                if item.status is not MenuItemStatus.AVAILABLE:
                    raise ValueError(f"Menu item '{item_id}' became unavailable")
                line_total = to_money(item.price * quantity)
                lines.append(
                    OrderLine(
                        item_id=item.item_id,
                        item_name=item.name,
                        unit_price=item.price,
                        quantity=quantity,
                        line_total=line_total,
                    )
                )
                subtotal += line_total

            distance = self._distance_strategy.calculate_km(
                restaurant.location,
                delivery_location,
            )
            order = Order(
                order_id=str(uuid4()),
                customer_id=customer_id,
                restaurant_id=restaurant.restaurant_id,
                delivery_location=delivery_location,
                lines=tuple(lines),
                pricing=self._pricing_strategy.calculate(to_money(subtotal), distance),
                delivery_distance_km=distance,
                created_at=self._clock.now(),
            )
            self.orders[order.order_id] = order
            # The order is now a durable snapshot in this model. Payment retries
            # operate on the order; new cart edits cannot change its price.
            cart.clear()
            return order

    def pay_for_order(self, order_id: str, method: PaymentMethod) -> Payment:
        with self._lock:
            order = self.get_order(order_id)
            for payment_id in reversed(order.payment_ids):
                payment = self.payments[payment_id]
                if payment.status is PaymentStatus.COMPLETED:
                    return payment
            if order.status is not OrderStatus.PENDING_PAYMENT:
                raise ValueError(f"Order cannot be paid in {order.status.name} state")
            payment = self._payment_gateway.charge(
                order.order_id,
                order.total_amount,
                method,
            )
            self.payments[payment.payment_id] = payment
            order.payment_ids.append(payment.payment_id)
            if payment.status is PaymentStatus.COMPLETED:
                order.status = OrderStatus.CONFIRMED
                order.confirmed_at = self._clock.now()
            return payment

    def start_preparing(self, order_id: str) -> Order:
        with self._lock:
            order = self.get_order(order_id)
            if order.status is OrderStatus.PREPARING:
                return order
            if order.status is not OrderStatus.CONFIRMED:
                raise ValueError("Only a confirmed order can start preparation")
            order.status = OrderStatus.PREPARING
            order.preparation_started_at = self._clock.now()
            return order

    def mark_ready_for_pickup(self, order_id: str) -> Order:
        with self._lock:
            order = self.get_order(order_id)
            if order.status is OrderStatus.READY_FOR_PICKUP:
                return order
            if order.status is not OrderStatus.PREPARING:
                raise ValueError("Only a preparing order can become ready")
            order.status = OrderStatus.READY_FOR_PICKUP
            order.ready_at = self._clock.now()
            return order

    def assign_delivery_partner(self, order_id: str) -> DeliveryPartner | None:
        with self._lock:
            order = self.get_order(order_id)
            if order.status is not OrderStatus.READY_FOR_PICKUP:
                raise ValueError("Delivery partner can be assigned only when order is ready")
            if order.delivery_partner_id is not None:
                return self._catalog.get_delivery_partner(order.delivery_partner_id)
            restaurant = self._catalog.get_restaurant(order.restaurant_id)
            candidates = [
                partner
                for partner in self._catalog.delivery_partners.values()
                if partner.status is DeliveryPartnerStatus.AVAILABLE
                and self._distance_strategy.calculate_km(
                    partner.location,
                    restaurant.location,
                )
                <= self._max_partner_distance_km
            ]
            partner = self._matching_strategy.select_partner(
                candidates,
                restaurant.location,
            )
            if partner is None:
                return None
            partner.status = DeliveryPartnerStatus.ON_DELIVERY
            order.delivery_partner_id = partner.partner_id
            return partner

    def pick_up_order(self, order_id: str, partner_id: str) -> Order:
        with self._lock:
            order = self.get_order(order_id)
            if order.status is OrderStatus.OUT_FOR_DELIVERY:
                if order.delivery_partner_id != partner_id:
                    raise ValueError("Only the assigned delivery partner can pick up this order")
                return order
            if order.status is not OrderStatus.READY_FOR_PICKUP:
                raise ValueError("Only a ready order can be picked up")
            if order.delivery_partner_id != partner_id:
                raise ValueError("Only the assigned delivery partner can pick up this order")
            partner = self._catalog.get_delivery_partner(partner_id)
            if partner.status is not DeliveryPartnerStatus.ON_DELIVERY:
                raise RuntimeError("Assigned partner is not reserved for delivery")
            restaurant = self._catalog.get_restaurant(order.restaurant_id)
            partner.location = restaurant.location
            order.status = OrderStatus.OUT_FOR_DELIVERY
            order.picked_up_at = self._clock.now()
            return order

    def deliver_order(self, order_id: str, partner_id: str) -> Order:
        with self._lock:
            order = self.get_order(order_id)
            if order.status is OrderStatus.DELIVERED:
                if order.delivery_partner_id != partner_id:
                    raise ValueError("Only the assigned delivery partner can deliver this order")
                return order
            if order.status is not OrderStatus.OUT_FOR_DELIVERY:
                raise ValueError("Only an out-for-delivery order can be delivered")
            if order.delivery_partner_id != partner_id:
                raise ValueError("Only the assigned delivery partner can deliver this order")
            partner = self._catalog.get_delivery_partner(partner_id)
            partner.location = order.delivery_location
            partner.status = DeliveryPartnerStatus.AVAILABLE
            order.status = OrderStatus.DELIVERED
            order.delivered_at = self._clock.now()
            return order

    def cancel_order(self, order_id: str, reason: str) -> Order:
        if not reason.strip():
            raise ValueError("Cancellation reason is required")
        with self._lock:
            order = self.get_order(order_id)
            if order.status is OrderStatus.CANCELLED:
                return order
            if order.status in {OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED}:
                raise ValueError(f"Order cannot be cancelled in {order.status.name} state")
            for payment_id in order.payment_ids:
                payment = self.payments[payment_id]
                if payment.status is PaymentStatus.COMPLETED:
                    self._payment_gateway.refund(payment)
            if order.delivery_partner_id is not None:
                partner = self._catalog.get_delivery_partner(order.delivery_partner_id)
                partner.status = DeliveryPartnerStatus.AVAILABLE
            order.status = OrderStatus.CANCELLED
            order.cancelled_at = self._clock.now()
            order.cancellation_reason = reason.strip()
            return order

    def go_online(
        self,
        partner_id: str,
        location: Location | None = None,
    ) -> DeliveryPartner:
        with self._lock:
            partner = self._catalog.get_delivery_partner(partner_id)
            if partner.status is DeliveryPartnerStatus.ON_DELIVERY:
                raise ValueError("Partner on a delivery cannot change availability")
            if location is not None:
                partner.location = location
            partner.status = DeliveryPartnerStatus.AVAILABLE
            return partner

    def go_offline(self, partner_id: str) -> DeliveryPartner:
        with self._lock:
            partner = self._catalog.get_delivery_partner(partner_id)
            if partner.status is DeliveryPartnerStatus.ON_DELIVERY:
                raise ValueError("Partner on a delivery cannot go offline")
            partner.status = DeliveryPartnerStatus.OFFLINE
            return partner

    def update_partner_location(
        self,
        partner_id: str,
        location: Location,
    ) -> DeliveryPartner:
        with self._lock:
            partner = self._catalog.get_delivery_partner(partner_id)
            partner.location = location
            return partner

    def get_cart(self, customer_id: str) -> Cart:
        with self._lock:
            self._catalog.get_customer(customer_id)
            return self.carts.setdefault(customer_id, Cart(customer_id))

    def get_order(self, order_id: str) -> Order:
        with self._lock:
            try:
                return self.orders[order_id]
            except KeyError as error:
                raise ValueError(f"Order '{order_id}' does not exist") from error

    def get_customer_orders(self, customer_id: str) -> list[Order]:
        with self._lock:
            self._catalog.get_customer(customer_id)
            return sorted(
                (order for order in list(self.orders.values()) if order.customer_id == customer_id),
                key=lambda order: order.created_at,
                reverse=True,
            )

    def get_restaurant_orders(self, restaurant_id: str) -> list[Order]:
        with self._lock:
            self._catalog.get_restaurant(restaurant_id)
            return sorted(
                (order for order in list(self.orders.values()) if order.restaurant_id == restaurant_id),
                key=lambda order: order.created_at,
                reverse=True,
            )

    @staticmethod
    def _to_distance(value: Decimal | int | float | str) -> Decimal:
        try:
            distance = Decimal(str(value)).quantize(Decimal("0.001"))
        except (InvalidOperation, ValueError) as error:
            raise ValueError(f"Invalid distance value: {value}") from error
        if not distance.is_finite():
            raise ValueError("Distance must be finite")
        return distance
