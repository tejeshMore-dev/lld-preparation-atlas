import uuid
from datetime import datetime

from models.elevator_car import ElevatorCar
from models.enums import (
    Direction,
    DoorState,
    ElevatorState,
    EventType,
    RequestStatus,
)
from models.event import ElevatorEvent
from models.request import CarRequest, HallRequest
from strategies.scheduling_strategy import SchedulingStrategy


class ElevatorSystem:
    def __init__(
        self,
        elevators: list[ElevatorCar],
        scheduling_strategy: SchedulingStrategy,
    ) -> None:
        if not elevators:
            raise ValueError("An elevator system requires at least one elevator")
        elevator_ids = [elevator.elevator_id for elevator in elevators]
        if len(elevator_ids) != len(set(elevator_ids)):
            raise ValueError("Elevator IDs must be unique")
        floor_ranges = {
            (elevator.min_floor, elevator.max_floor)
            for elevator in elevators
        }
        if len(floor_ranges) != 1:
            raise ValueError("All elevators must use the same building floor range")

        self.elevators = {elevator.elevator_id: elevator for elevator in elevators}
        self.scheduling_strategy = scheduling_strategy
        self.hall_requests: dict[str, HallRequest] = {}
        self.car_requests: dict[str, CarRequest] = {}
        self.event_history: list[ElevatorEvent] = []
        self.min_floor, self.max_floor = floor_ranges.pop()

    def request_elevator(self, floor: int, direction: Direction) -> HallRequest:
        self._validate_building_floor(floor)
        if direction == Direction.IDLE:
            raise ValueError("A hall request must specify UP or DOWN")
        if floor == self.max_floor and direction == Direction.UP:
            raise ValueError("Cannot request UP from the highest floor")
        if floor == self.min_floor and direction == Direction.DOWN:
            raise ValueError("Cannot request DOWN from the lowest floor")

        existing = next(
            (
                request
                for request in self.hall_requests.values()
                if request.floor == floor
                and request.direction == direction
                and request.status != RequestStatus.COMPLETED
            ),
            None,
        )
        if existing is not None:
            return existing

        request = HallRequest(
            request_id=str(uuid.uuid4()),
            floor=floor,
            direction=direction,
            created_at=datetime.now(),
        )
        self.hall_requests[request.request_id] = request
        self._dispatch_hall_request(request)
        return request

    def select_floor(self, elevator_id: str, destination_floor: int) -> CarRequest:
        elevator = self._get_elevator(elevator_id)
        elevator.validate_floor(destination_floor)
        if elevator.state == ElevatorState.OUT_OF_SERVICE:
            raise ValueError("Cannot select a floor in an out-of-service elevator")
        if (
            destination_floor == elevator.current_floor
            and elevator.state == ElevatorState.MOVING
        ):
            raise ValueError("Elevator has already departed from the current floor")

        existing = next(
            (
                request
                for request in self.car_requests.values()
                if request.elevator_id == elevator_id
                and request.destination_floor == destination_floor
                and request.status != RequestStatus.COMPLETED
            ),
            None,
        )
        if existing is not None:
            return existing

        request = CarRequest(
            request_id=str(uuid.uuid4()),
            elevator_id=elevator_id,
            destination_floor=destination_floor,
            created_at=datetime.now(),
        )
        self.car_requests[request.request_id] = request

        if destination_floor == elevator.current_floor and elevator.state != ElevatorState.MOVING:
            event = elevator.serve_current_floor()
            self.event_history.append(event)
            request.status = RequestStatus.COMPLETED
        else:
            elevator.add_stop(destination_floor)
        return request

    def tick(self) -> list[ElevatorEvent]:
        self._dispatch_pending_requests()
        events: list[ElevatorEvent] = []

        for elevator in sorted(self.elevators.values(), key=lambda item: item.elevator_id):
            event = elevator.step()
            if event is None:
                continue
            events.append(event)
            self.event_history.append(event)
            if event.event_type == EventType.ARRIVED:
                self._complete_requests(elevator.elevator_id, event.floor)

        self._dispatch_pending_requests()
        return events

    def run_until_idle(self, max_ticks: int = 1000) -> list[ElevatorEvent]:
        if max_ticks <= 0:
            raise ValueError("max_ticks must be greater than zero")

        emitted: list[ElevatorEvent] = []
        for _ in range(max_ticks):
            if not self._has_work():
                return emitted
            emitted.extend(self.tick())
        raise RuntimeError("Elevator system did not become idle within max_ticks")

    def set_out_of_service(self, elevator_id: str) -> None:
        self._get_elevator(elevator_id).set_out_of_service()

    def restore_service(self, elevator_id: str) -> None:
        self._get_elevator(elevator_id).restore_service()
        self._dispatch_pending_requests()

    def get_pending_hall_requests(self) -> list[HallRequest]:
        return sorted(
            (
                request
                for request in self.hall_requests.values()
                if request.status == RequestStatus.PENDING
            ),
            key=lambda request: request.created_at,
        )

    def _dispatch_hall_request(self, request: HallRequest) -> bool:
        if request.status != RequestStatus.PENDING:
            return False

        elevator = self.scheduling_strategy.select_elevator(
            list(self.elevators.values()),
            request.floor,
            request.direction,
        )
        if elevator is None:
            return False

        request.assigned_elevator_id = elevator.elevator_id
        request.status = RequestStatus.ASSIGNED
        if request.floor == elevator.current_floor and elevator.state != ElevatorState.MOVING:
            event = elevator.serve_current_floor()
            self.event_history.append(event)
            request.status = RequestStatus.COMPLETED
        else:
            elevator.add_stop(request.floor)
        return True

    def _dispatch_pending_requests(self) -> None:
        for request in self.get_pending_hall_requests():
            self._dispatch_hall_request(request)

    def _complete_requests(self, elevator_id: str, floor: int) -> None:
        for request in self.hall_requests.values():
            if (
                request.status == RequestStatus.ASSIGNED
                and request.assigned_elevator_id == elevator_id
                and request.floor == floor
            ):
                request.status = RequestStatus.COMPLETED

        for request in self.car_requests.values():
            if (
                request.status == RequestStatus.ASSIGNED
                and request.elevator_id == elevator_id
                and request.destination_floor == floor
            ):
                request.status = RequestStatus.COMPLETED

    def _has_work(self) -> bool:
        active_requests = any(
            request.status != RequestStatus.COMPLETED
            for request in self.hall_requests.values()
        ) or any(
            request.status != RequestStatus.COMPLETED
            for request in self.car_requests.values()
        )
        active_elevators = any(
            elevator.pending_stops or elevator.door_state == DoorState.OPEN
            for elevator in self.elevators.values()
        )
        return active_requests or active_elevators

    def _get_elevator(self, elevator_id: str) -> ElevatorCar:
        try:
            return self.elevators[elevator_id]
        except KeyError as error:
            raise ValueError(f'Elevator "{elevator_id}" not found') from error

    def _validate_building_floor(self, floor: int) -> None:
        if not self.min_floor <= floor <= self.max_floor:
            raise ValueError(f"Floor {floor} is outside the building range")
