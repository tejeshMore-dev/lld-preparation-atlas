from abc import ABC, abstractmethod
from typing import Optional

from models.parking_spots import ParkingSpot
from models.vehicle import Vehicle
from models.enums import SpotType

SIZE_RANK = {
    SpotType.REGULAR: 0,
    SpotType.COMPACT: 1,
    SpotType.LARGE: 2
}

class SpotAllocationStrategy(ABC):

    @abstractmethod
    def select(self, spots: list[ParkingSpot], vehicle: Vehicle) -> Optional[ParkingSpot]:
        pass

class NearestFirstStratergy(SpotAllocationStrategy):

    def select(self, spots: list[ParkingSpot], vehicle: Vehicle) -> Optional[ParkingSpot]:
        fitting = [ 
            spot 
            for spot in spots 
            if spot.is_available() and spot.can_fit_vehicle(vehicle)
            ]

        if not fitting:
            return None

        return min(
            fitting, 
            key=lambda spot: spot.distance_from_entrance,
        )

class BestFitStratergy(SpotAllocationStrategy):

    def select(self, spots: list[ParkingSpot], vehicle: Vehicle) -> Optional[ParkingSpot]:
        fitting = [ 
                    spot 
                    for spot in spots 
                    if spot.is_available() and spot.can_fit_vehicle(vehicle)
                    ]
        
        if not fitting:
            return None

        return min(
            fitting, 
            key=lambda spot: SIZE_RANK[spot.spot_type],
        )

