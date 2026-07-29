from enum import Enum, auto


class SeatType(Enum):
    REGULAR = auto()
    PREMIUM = auto()
    RECLINER = auto()


class ShowSeatStatus(Enum):
    AVAILABLE = auto()
    HELD = auto()
    BOOKED = auto()


class BookingStatus(Enum):
    PENDING_PAYMENT = auto()
    CONFIRMED = auto()
    CANCELLED = auto()
    EXPIRED = auto()


class PaymentMethod(Enum):
    CARD = auto()
    UPI = auto()
    WALLET = auto()


class PaymentStatus(Enum):
    COMPLETED = auto()
    FAILED = auto()
    REFUNDED = auto()
