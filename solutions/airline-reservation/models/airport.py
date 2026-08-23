from dataclasses import dataclass


@dataclass(frozen=True)
class Airport:
    code: str
    name: str
    city: str
    timezone: str
