from abc import ABC, abstractmethod

from models.driver import Driver
from models.location import Location


class MatchingStrategy(ABC):
    @abstractmethod
    def select_driver(self, drivers: list[Driver], pickup: Location) -> Driver | None:
        raise NotImplementedError
