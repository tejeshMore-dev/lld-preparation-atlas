from typing import Optional

from models.enums import SpotType
from models.vehicle import Vehicle
from models.enums import VehicleType


SIZE_RANK = {
    SpotType.REGULAR: 0,
    SpotType.COMPACT: 1,
    SpotType.LARGE: 2,
}

class ParkingSpot:
    def __init__(
        self,
        spot_id: str,
        spot_type: SpotType,
        floor_number: int,
        distance_from_entrance: float
    ):
        self.spot_id = spot_id  
        self.spot_type = spot_type
        self.floor_number = floor_number
        self.distance_from_entrance = distance_from_entrance

        self.is_occupied = False
        self.vehicle: Optional[Vehicle] = None

    def can_fit_vehicle(self, vehicle: Vehicle) -> bool:

        if vehicle.vehicle_type == VehicleType.MOTORCYCLE:
            return SIZE_RANK[self.spot_type] >= SIZE_RANK[SpotType.REGULAR]

        if vehicle.vehicle_type == VehicleType.CAR:
            return SIZE_RANK[self.spot_type] >= SIZE_RANK[SpotType.COMPACT]

        return SIZE_RANK[self.spot_type] >= SIZE_RANK[SpotType.LARGE]       

    def assign(self, vehicle: Vehicle):
        if self.is_occupied:
            raise Exception(f"Parking spot {self.spot_id} is already occupied.")

        self.vehicle = vehicle
        self.is_occupied = True

    def vacate(self, vehicle: Vehicle):
        if not self.is_occupied or self.vehicle != vehicle:
            raise Exception(f"Parking spot {self.spot_id} is not occupied by this vehicle.")

        self.vehicle = None
        self.is_occupied = False

    def is_available(self) -> bool:
        return not self.is_occupied