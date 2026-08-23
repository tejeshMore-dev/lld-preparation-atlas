from dataclasses import dataclass

from models.enums import DeliveryPartnerStatus
from models.location import Location


@dataclass
class DeliveryPartner:
    partner_id: str
    name: str
    phone: str
    location: Location
    status: DeliveryPartnerStatus = DeliveryPartnerStatus.OFFLINE
