from dataclasses import dataclass

from models.enums import CabinClass


@dataclass(frozen=True)
class Seat:
    seat_id: str
    number: str
    cabin_class: CabinClass
