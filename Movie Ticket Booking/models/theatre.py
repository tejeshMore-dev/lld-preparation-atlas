from dataclasses import dataclass, field

from models.screen import Screen


@dataclass
class Theatre:
    theatre_id: str
    name: str
    city: str
    screens: dict[str, Screen] = field(default_factory=dict)

    def add_screen(self, screen: Screen) -> None:
        if screen.screen_id in self.screens:
            raise ValueError(f'Screen "{screen.screen_id}" already exists')
        if not screen.seats:
            raise ValueError("A screen must contain at least one seat")
        self.screens[screen.screen_id] = screen
