from models.elevator_car import ElevatorCar
from models.enums import Direction
from strategies.scheduling_strategy import SchedulingStrategy


class DirectionAwareNearestStrategy(SchedulingStrategy):
    """Chooses the nearest idle or on-the-way compatible elevator."""

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
                elevator.estimated_distance_to(floor),
                0 if elevator.direction == direction else 1,
                len(elevator.pending_stops),
                elevator.elevator_id,
            ),
            default=None,
        )
