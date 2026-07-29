from enum import Enum, auto


class RoomType(Enum):
    STANDARD = auto()
    DELUXE = auto()
    SUITE = auto()


class RoomStatus(Enum):
    IN_SERVICE = auto()
    OUT_OF_SERVICE = auto()


class BookingStatus(Enum):
    PENDING_PAYMENT = auto()
    CONFIRMED = auto()
    CHECKED_IN = auto()
    CHECKED_OUT = auto()
    CANCELLED = auto()
    EXPIRED = auto()


class PaymentMethod(Enum):
    CARD = auto()
    UPI = auto()
    CASH = auto()


class PaymentStatus(Enum):
    COMPLETED = auto()
    FAILED = auto()
    REFUNDED = auto()


class ChargeType(Enum):
    ROOM_SERVICE = auto()
    LAUNDRY = auto()
    MINIBAR = auto()
    OTHER = auto()
