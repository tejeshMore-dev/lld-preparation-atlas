from dataclasses import dataclass, field

from models.seat import Seat


@dataclass
class Screen:
    screen_id: str
    name: str
    seats: dict[str, Seat] = field(default_factory=dict)

    def add_seat(self, seat: Seat) -> None:
        if seat.seat_id in self.seats:
            raise ValueError(f'Seat "{seat.seat_id}" already exists in the screen')
        if any(
            existing.row == seat.row and existing.number == seat.number
            for existing in self.seats.values()
        ):
            raise ValueError("Seat row and number must be unique within the screen")
        self.seats[seat.seat_id] = seat
