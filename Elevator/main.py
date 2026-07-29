from models.elevator_car import ElevatorCar
from models.enums import Direction, EventType, RequestStatus
from services.elevator_system import ElevatorSystem
from strategies.direction_aware_nearest_strategy import DirectionAwareNearestStrategy


def main() -> None:
    system = ElevatorSystem(
        elevators=[
            ElevatorCar("E1", min_floor=0, max_floor=10, current_floor=0),
            ElevatorCar("E2", min_floor=0, max_floor=10, current_floor=5),
            ElevatorCar("E3", min_floor=0, max_floor=10, current_floor=10),
        ],
        scheduling_strategy=DirectionAwareNearestStrategy(),
    )

    pickup = system.request_elevator(floor=3, direction=Direction.UP)
    while pickup.status != RequestStatus.COMPLETED:
        system.tick()

    elevator = system.elevators[pickup.assigned_elevator_id]
    elevator.board_passengers()
    destination = system.select_floor(elevator.elevator_id, destination_floor=8)

    events = []
    while destination.status != RequestStatus.COMPLETED:
        events.extend(system.tick())
    elevator.exit_passengers()
    events.extend(system.run_until_idle())
    for event in events:
        if event.event_type in (EventType.MOVED, EventType.ARRIVED):
            print(
                f"{event.elevator_id}: {event.event_type.name.lower()} "
                f"at floor {event.floor}"
            )

    # Door is closed after run_until_idle; the trip is complete.
    print(f"Final floor: {elevator.current_floor}")


if __name__ == "__main__":
    main()
