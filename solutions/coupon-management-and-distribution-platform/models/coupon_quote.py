from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class CouponQuote:
    coupon_code: str
    order_id: str
    order_amount: Decimal
    discount_amount: Decimal
    payable_amount: Decimal
    reserved_until: datetime
