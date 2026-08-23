from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Redemption:
    redemption_id: str
    coupon_id: str
    campaign_id: str
    user_id: str
    order_id: str
    order_amount: Decimal
    discount_amount: Decimal
    payable_amount: Decimal
    redeemed_at: datetime
