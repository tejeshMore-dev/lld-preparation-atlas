from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not isfinite(self.latitude) or not isfinite(self.longitude):
            raise ValueError("Coordinates must be finite")
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")
