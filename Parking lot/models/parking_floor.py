from models.parking_spots import ParkingSpot
from models.vehicle import Vehicle
from strategies.allocation import SpotAllocationStrategy


class ParkingFloor:
    def __init__(self, floor_id: int):
        self.floor_id = floor_id
        self.spots: list[ParkingSpot] = []

    def add_spot(self, spot: ParkingSpot) -> None:
        if spot.floor_number != self.floor_id:
            raise ValueError("Parking spot floor number does not match the floor")
        if any(existing.spot_id == spot.spot_id for existing in self.spots):
            raise ValueError(f'Parking spot "{spot.spot_id}" already exists')
        self.spots.append(spot)

    def find_spot(
        self,
        vehicle: Vehicle,
        strategy: SpotAllocationStrategy,
    ) -> ParkingSpot | None:
        return strategy.select(self.spots, vehicle)
