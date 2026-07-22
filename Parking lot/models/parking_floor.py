from typing import List, Optional

from models.parking_spots import ParkingSpot
from models.vehicle import Vehicle
from strategies.allocation import SpotAllocationStrategy

class ParkingFloor:
    def __init__(self, floor_id: int):
        self.floor_id = floor_id
        self.spots: List[ParkingSpot] = []

    def add_spot(self, spot: ParkingSpot):
        self.spots.append(spot)

    def find_spot(self, vehicle: Vehicle, strategy: SpotAllocationStrategy) -> Optional[ParkingSpot]:
        return strategy.select(self.spots, vehicle)

    