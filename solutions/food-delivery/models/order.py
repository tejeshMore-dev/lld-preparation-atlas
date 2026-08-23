from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from models.enums import OrderStatus
from models.location import Location
from models.price_breakdown import PriceBreakdown


@dataclass(frozen=True)
class OrderLine:
    item_id: str
    item_name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


@dataclass
class Order:
    order_id: str
    customer_id: str
    restaurant_id: str
    delivery_location: Location
    lines: tuple[OrderLine, ...]
    pricing: PriceBreakdown
    delivery_distance_km: Decimal
    created_at: datetime
    status: OrderStatus = OrderStatus.PENDING_PAYMENT
    delivery_partner_id: str | None = None
    payment_ids: list[str] = field(default_factory=list)
    confirmed_at: datetime | None = None
    preparation_started_at: datetime | None = None
    ready_at: datetime | None = None
    picked_up_at: datetime | None = None
    delivered_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None

    @property
    def total_amount(self) -> Decimal:
        return self.pricing.total
