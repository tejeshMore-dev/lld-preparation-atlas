from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from models.enums import CampaignStatus


@dataclass
class Campaign:
    campaign_id: str
    merchant_id: str
    name: str
    code_prefix: str
    start_time: datetime
    end_time: datetime
    total_supply: int
    per_user_limit: int
    minimum_order_value: Decimal
    applicable_categories: frozenset[str]
    status: CampaignStatus = CampaignStatus.DRAFT
    issued_count: int = 0
    redeemed_count: int = 0
