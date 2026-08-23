from dataclasses import dataclass


@dataclass(frozen=True)
class Merchant:
    merchant_id: str
    name: str
    email: str
