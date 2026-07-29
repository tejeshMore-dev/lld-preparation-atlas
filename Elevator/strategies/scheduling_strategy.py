from abc import ABC, abstractmethod

from models.elevator_car import ElevatorCar
from models.enums import Direction


class SchedulingStrategy(ABC):
    @abstractmethod
    def select_elevator(
        self,
        elevators: list[ElevatorCar],
        floor: int,
        direction: Direction,
    ) -> ElevatorCar | None:
        raise NotImplementedError
