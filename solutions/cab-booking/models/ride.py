from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from models.enums import RideStatus, VehicleType
from models.location import Location


@dataclass
class Ride:
    ride_id: str
    rider_id: str
    pickup: Location
    dropoff: Location
    vehicle_type: VehicleType
    estimated_distance_km: Decimal
    estimated_duration_minutes: Decimal
    estimated_fare: Decimal
    requested_at: datetime
    status: RideStatus = RideStatus.REQUESTED
    driver_id: str | None = None
    assigned_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    actual_distance_km: Decimal | None = None
    actual_duration_minutes: Decimal | None = None
    final_fare: Decimal | None = None
    payment_ids: list[str] = field(default_factory=list)
    driver_rating: int | None = None
