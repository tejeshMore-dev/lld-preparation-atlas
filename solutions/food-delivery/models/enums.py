from enum import Enum, auto


class RestaurantStatus(Enum):
    OPEN = auto()
    CLOSED = auto()


class MenuItemStatus(Enum):
    AVAILABLE = auto()
    UNAVAILABLE = auto()


class DeliveryPartnerStatus(Enum):
    OFFLINE = auto()
    AVAILABLE = auto()
    ON_DELIVERY = auto()


class OrderStatus(Enum):
    PENDING_PAYMENT = auto()
    CONFIRMED = auto()
    PREPARING = auto()
    READY_FOR_PICKUP = auto()
    OUT_FOR_DELIVERY = auto()
    DELIVERED = auto()
    CANCELLED = auto()


class PaymentMethod(Enum):
    CARD = auto()
    UPI = auto()
    WALLET = auto()
    CASH = auto()


class PaymentStatus(Enum):
    COMPLETED = auto()
    FAILED = auto()
    REFUNDED = auto()
