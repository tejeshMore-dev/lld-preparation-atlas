from enum import Enum, auto


class VehicleType(Enum):
    MINI = auto()
    SEDAN = auto()
    SUV = auto()


class DriverStatus(Enum):
    OFFLINE = auto()
    AVAILABLE = auto()
    ON_TRIP = auto()


class RideStatus(Enum):
    REQUESTED = auto()
    DRIVER_ASSIGNED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    CANCELLED = auto()


class PaymentMethod(Enum):
    CASH = auto()
    CARD = auto()
    UPI = auto()
    WALLET = auto()


class PaymentStatus(Enum):
    COMPLETED = auto()
    FAILED = auto()
