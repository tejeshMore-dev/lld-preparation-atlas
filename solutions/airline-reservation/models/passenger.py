from dataclasses import dataclass


@dataclass(frozen=True)
class Passenger:
    passenger_id: str
    name: str
    email: str
    passport_number: str
