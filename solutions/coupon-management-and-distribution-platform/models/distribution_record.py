from dataclasses import dataclass
from datetime import datetime

from models.enums import DistributionChannel


@dataclass(frozen=True)
class DistributionRecord:
    distribution_id: str
    campaign_id: str
    coupon_id: str
    user_id: str
    channel: DistributionChannel
    distributed_at: datetime
