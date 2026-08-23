from abc import ABC, abstractmethod

from models.enums import SpotType
from models.parking_spots import ParkingSpot
from models.vehicle import Vehicle


SIZE_RANK = {
    SpotType.REGULAR: 0,
    SpotType.COMPACT: 1,
    SpotType.LARGE: 2,
}


class SpotAllocationStrategy(ABC):
    @abstractmethod
    def select(
        self,
        spots: list[ParkingSpot],
        vehicle: Vehicle,
    ) -> ParkingSpot | None:
        raise NotImplementedError


class NearestFirstStrategy(SpotAllocationStrategy):
    def select(
        self,
        spots: list[ParkingSpot],
        vehicle: Vehicle,
    ) -> ParkingSpot | None:
        fitting = [
            spot
            for spot in spots
            if spot.is_available() and spot.can_fit_vehicle(vehicle)
        ]
        return min(fitting, key=lambda spot: spot.distance_from_entrance, default=None)


class BestFitStrategy(SpotAllocationStrategy):
    def select(
        self,
        spots: list[ParkingSpot],
        vehicle: Vehicle,
    ) -> ParkingSpot | None:
        fitting = [
            spot
            for spot in spots
            if spot.is_available() and spot.can_fit_vehicle(vehicle)
        ]
        return min(
            fitting,
            key=lambda spot: (SIZE_RANK[spot.spot_type], spot.distance_from_entrance),
            default=None,
        )
