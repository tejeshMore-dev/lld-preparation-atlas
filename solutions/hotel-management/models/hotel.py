from dataclasses import dataclass, field

from models.money import to_money
from models.room import Room


@dataclass
class Hotel:
    hotel_id: str
    name: str
    city: str
    address: str
    rooms: dict[str, Room] = field(default_factory=dict)

    def add_room(self, room: Room) -> None:
        if room.room_id in self.rooms:
            raise ValueError(f"Room '{room.room_id}' already exists")
        if any(existing.number == room.number for existing in self.rooms.values()):
            raise ValueError(f"Room number '{room.number}' already exists")
        if room.capacity <= 0:
            raise ValueError("Room capacity must be positive")
        room.nightly_rate = to_money(room.nightly_rate)
        if room.nightly_rate <= 0:
            raise ValueError("Nightly rate must be positive")
        self.rooms[room.room_id] = room
