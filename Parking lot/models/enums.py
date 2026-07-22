from enum import Enum, auto

class VehicleType(Enum):
    MOTORCYCLE = auto()
    CAR = auto()
    TRUCK = auto()

class SpotType(Enum):
    REGULAR = auto()
    COMPACT = auto()
    LARGE = auto()

class PaymentMethod(Enum):
    CASH = auto()
    CREDIT_CARD = auto()
    MOBILE_PAYMENT = auto()
    UPI = auto()

class PaymentStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    FAILED = auto()

class TicketStatus(Enum):
    ACTIVE = auto()
    EXPIRED = auto()
    PAID = auto()
