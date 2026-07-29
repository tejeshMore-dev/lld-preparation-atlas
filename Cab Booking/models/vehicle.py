from dataclasses import dataclass

from models.enums import VehicleType


@dataclass(frozen=True)
class Vehicle:
    vehicle_id: str
    registration_number: str
    model: str
    vehicle_type: VehicleType
    capacity: int
