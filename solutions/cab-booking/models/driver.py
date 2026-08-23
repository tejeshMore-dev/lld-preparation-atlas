from dataclasses import dataclass
from decimal import Decimal

from models.enums import DriverStatus
from models.location import Location
from models.vehicle import Vehicle


@dataclass
class Driver:
    driver_id: str
    name: str
    phone: str
    vehicle: Vehicle
    location: Location
    status: DriverStatus = DriverStatus.OFFLINE
    average_rating: Decimal = Decimal("5.00")
    rating_count: int = 0
