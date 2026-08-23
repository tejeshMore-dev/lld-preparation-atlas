from typing import Optional

from models.enums import SpotType, VehicleType
from models.vehicle import Vehicle


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
        required_spot = {
            VehicleType.MOTORCYCLE: SpotType.REGULAR,
            VehicleType.CAR: SpotType.COMPACT,
            VehicleType.TRUCK: SpotType.LARGE,
        }[vehicle.vehicle_type]
        return SIZE_RANK[self.spot_type] >= SIZE_RANK[required_spot]

    def assign(self, vehicle: Vehicle) -> None:
        if self.is_occupied:
            raise ValueError(f"Parking spot {self.spot_id} is already occupied")
        if not self.can_fit_vehicle(vehicle):
            raise ValueError(
                f"Vehicle {vehicle.license_plate} does not fit spot {self.spot_id}"
            )

        self.vehicle = vehicle
        self.is_occupied = True

    def vacate(self, vehicle: Vehicle) -> None:
        if not self.is_occupied or self.vehicle != vehicle:
            raise ValueError(
                f"Parking spot {self.spot_id} is not occupied by this vehicle"
            )

        self.vehicle = None
        self.is_occupied = False

    def is_available(self) -> bool:
        return not self.is_occupied
