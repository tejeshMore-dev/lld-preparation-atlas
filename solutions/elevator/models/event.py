from dataclasses import dataclass

from models.enums import EventType


@dataclass(frozen=True)
class ElevatorEvent:
    elevator_id: str
    event_type: EventType
    floor: int
