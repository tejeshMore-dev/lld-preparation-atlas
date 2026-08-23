from dataclasses import dataclass, field

from models.seat import Seat


@dataclass
class Aircraft:
    aircraft_id: str
    model: str
    registration_number: str
    seats: dict[str, Seat] = field(default_factory=dict)

    def add_seat(self, seat: Seat) -> None:
        if seat.seat_id in self.seats:
            raise ValueError(f"Seat '{seat.seat_id}' already exists")
        if any(existing.number == seat.number for existing in self.seats.values()):
            raise ValueError(f"Seat number '{seat.number}' already exists")
        self.seats[seat.seat_id] = seat
