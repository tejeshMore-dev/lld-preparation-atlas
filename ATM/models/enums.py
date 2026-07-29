from enum import Enum, auto


class ATMState(Enum):
    IDLE = auto()
    CARD_INSERTED = auto()
    AUTHENTICATED = auto()
    OUT_OF_SERVICE = auto()


class AccountStatus(Enum):
    ACTIVE = auto()
    BLOCKED = auto()
    CLOSED = auto()


class CardStatus(Enum):
    ACTIVE = auto()
    BLOCKED = auto()
    EXPIRED = auto()


class TransactionType(Enum):
    BALANCE_INQUIRY = auto()
    WITHDRAWAL = auto()
    DEPOSIT = auto()
    TRANSFER = auto()


class TransactionStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    DECLINED = auto()
    FAILED = auto()
