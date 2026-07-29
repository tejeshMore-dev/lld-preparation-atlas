from dataclasses import dataclass, field

from models.aircraft import Aircraft


@dataclass
class Airline:
    airline_id: str
    name: str
    code: str
    aircraft: dict[str, Aircraft] = field(default_factory=dict)

    def add_aircraft(self, aircraft: Aircraft) -> None:
        if aircraft.aircraft_id in self.aircraft:
            raise ValueError(f"Aircraft '{aircraft.aircraft_id}' already exists")
        if any(
            existing.registration_number == aircraft.registration_number
            for existing in self.aircraft.values()
        ):
            raise ValueError(
                f"Aircraft registration '{aircraft.registration_number}' already exists"
            )
        if not aircraft.seats:
            raise ValueError("Aircraft must contain at least one seat")
        self.aircraft[aircraft.aircraft_id] = aircraft
