
from dataclasses import dataclass
from models.enums import VehicleType

@dataclass
class Vehicle:
    license_plate: str
    vehicle_type: VehicleType

