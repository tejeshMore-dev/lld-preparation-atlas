from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from models.location import Location
from strategies.distance_strategy import DistanceStrategy


class HaversineDistanceStrategy(DistanceStrategy):
    EARTH_RADIUS_KM = 6371.0

    def calculate_km(self, start: Location, end: Location) -> Decimal:
        latitude_delta = radians(end.latitude - start.latitude)
        longitude_delta = radians(end.longitude - start.longitude)
        start_latitude = radians(start.latitude)
        end_latitude = radians(end.latitude)
        value = (
            sin(latitude_delta / 2) ** 2
            + cos(start_latitude)
            * cos(end_latitude)
            * sin(longitude_delta / 2) ** 2
        )
        distance = 2 * self.EARTH_RADIUS_KM * asin(sqrt(value))
        return Decimal(str(distance)).quantize(Decimal("0.001"))
