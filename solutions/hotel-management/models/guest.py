from dataclasses import dataclass


@dataclass(frozen=True)
class Guest:
    guest_id: str
    name: str
    email: str
    phone: str
