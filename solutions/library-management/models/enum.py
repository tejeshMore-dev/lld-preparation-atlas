from enum import Enum, auto

class MemberType(Enum):
    STUDENT = auto()
    FACULTY = auto()
    LIBRARIAN = auto()

class BookStatus(Enum):
    AVAILABLE = auto()
    RESERVED = auto()
    ISSUED = auto()
    LOST = auto()

class AccountStatus(Enum):
    ACTIVE = auto()
    BLOCKED = auto()
    CLOSED = auto()

class ReservationStatus(Enum):
    WAITING = auto()
    READY = auto()
    COMPLETED = auto()
    CANCELLED = auto()

class NotificationType(Enum):
    RESERVATION_AVAILABLE = auto()
    DUE_REMINDER = auto()
    OVERDUE = auto()
