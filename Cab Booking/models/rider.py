from dataclasses import dataclass


@dataclass(frozen=True)
class Rider:
    rider_id: str
    name: str
    email: str
    phone: str
