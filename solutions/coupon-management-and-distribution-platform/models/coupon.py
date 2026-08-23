from dataclasses import dataclass
from datetime import datetime

from models.enums import CouponStatus


@dataclass
class Coupon:
    coupon_id: str
    code: str
    campaign_id: str
    user_id: str
    issued_at: datetime
    status: CouponStatus = CouponStatus.AVAILABLE
    reserved_order_id: str | None = None
    reserved_at: datetime | None = None
    reserved_until: datetime | None = None
    redeemed_order_id: str | None = None
    redeemed_at: datetime | None = None
    revoked_at: datetime | None = None
