import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import date

from models.enums import CardStatus


@dataclass
class Card:
    card_number: str
    account_id: str
    pin_salt: str
    pin_hash: str
    expiry_date: date
    status: CardStatus = CardStatus.ACTIVE
    failed_pin_attempts: int = 0

    @classmethod
    def issue(
        cls,
        card_number: str,
        account_id: str,
        pin: str,
        expiry_date: date,
    ) -> "Card":
        cls._validate_pin(pin)
        salt = secrets.token_hex(16)
        return cls(
            card_number=card_number,
            account_id=account_id,
            pin_salt=salt,
            pin_hash=cls._hash_pin(pin, salt),
            expiry_date=expiry_date,
        )

    def verify_pin(self, pin: str) -> bool:
        candidate = self._hash_pin(pin, self.pin_salt)
        return hmac.compare_digest(candidate, self.pin_hash)

    def is_expired(self, today: date | None = None) -> bool:
        return self.expiry_date < (today or date.today())

    @staticmethod
    def _validate_pin(pin: str) -> None:
        if len(pin) != 4 or not pin.isdigit():
            raise ValueError("PIN must contain exactly four digits")

    @staticmethod
    def _hash_pin(pin: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            bytes.fromhex(salt),
            100_000,
        ).hex()
