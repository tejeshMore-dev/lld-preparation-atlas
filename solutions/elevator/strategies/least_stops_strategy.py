from models.elevator_car import ElevatorCar
from models.enums import Direction
from strategies.scheduling_strategy import SchedulingStrategy


class LeastStopsStrategy(SchedulingStrategy):
    """Prefers the eligible car with the smallest pending-stop workload."""

    def select_elevator(
        self,
        elevators: list[ElevatorCar],
        floor: int,
        direction: Direction,
    ) -> ElevatorCar | None:
        eligible = [
            elevator
            for elevator in elevators
            if elevator.is_eligible_for(floor, direction)
        ]
        return min(
            eligible,
            key=lambda elevator: (
                len(elevator.pending_stops),
                elevator.estimated_distance_to(floor),
                elevator.elevator_id,
            ),
            default=None,
        )
