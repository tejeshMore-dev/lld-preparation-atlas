from enum import Enum, auto


class Direction(Enum):
    DOWN = -1
    IDLE = 0
    UP = 1


class ElevatorState(Enum):
    IDLE = auto()
    MOVING = auto()
    OUT_OF_SERVICE = auto()


class DoorState(Enum):
    OPEN = auto()
    CLOSED = auto()


class RequestStatus(Enum):
    PENDING = auto()
    ASSIGNED = auto()
    COMPLETED = auto()


class EventType(Enum):
    MOVED = auto()
    ARRIVED = auto()
    DOOR_CLOSED = auto()
