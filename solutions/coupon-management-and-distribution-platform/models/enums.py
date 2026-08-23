from enum import Enum, auto


class CampaignStatus(Enum):
    DRAFT = auto()
    ACTIVE = auto()
    PAUSED = auto()
    ENDED = auto()


class CouponStatus(Enum):
    AVAILABLE = auto()
    RESERVED = auto()
    REDEEMED = auto()
    EXPIRED = auto()
    REVOKED = auto()


class DistributionChannel(Enum):
    APP = auto()
    EMAIL = auto()
    SMS = auto()
    CLAIM = auto()
