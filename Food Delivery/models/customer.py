from dataclasses import dataclass


@dataclass(frozen=True)
class Customer:
    customer_id: str
    name: str
    email: str
    phone: str
