from enum import Enum, auto


class CabinClass(Enum):
    ECONOMY = auto()
    PREMIUM_ECONOMY = auto()
    BUSINESS = auto()
    FIRST = auto()


class FlightSeatStatus(Enum):
    AVAILABLE = auto()
    HELD = auto()
    BOOKED = auto()
    CHECKED_IN = auto()
    BOARDED = auto()


class FlightStatus(Enum):
    SCHEDULED = auto()
    BOARDING = auto()
    DEPARTED = auto()
    ARRIVED = auto()
    CANCELLED = auto()


class BookingStatus(Enum):
    PENDING_PAYMENT = auto()
    CONFIRMED = auto()
    CHECKED_IN = auto()
    BOARDED = auto()
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
