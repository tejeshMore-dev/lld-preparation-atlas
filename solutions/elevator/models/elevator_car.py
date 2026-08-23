from models.enums import Direction, DoorState, ElevatorState, EventType
from models.event import ElevatorEvent


class ElevatorCar:
    def __init__(
        self,
        elevator_id: str,
        min_floor: int,
        max_floor: int,
        current_floor: int = 0,
        capacity: int = 8,
    ) -> None:
        if min_floor >= max_floor:
            raise ValueError("Minimum floor must be below maximum floor")
        if not min_floor <= current_floor <= max_floor:
            raise ValueError("Current floor is outside the elevator range")
        if capacity <= 0:
            raise ValueError("Elevator capacity must be greater than zero")

        self.elevator_id = elevator_id
        self.min_floor = min_floor
        self.max_floor = max_floor
        self.current_floor = current_floor
        self.capacity = capacity
        self.passenger_count = 0
        self.state = ElevatorState.IDLE
        self.direction = Direction.IDLE
        self.door_state = DoorState.CLOSED
        self.pending_stops: set[int] = set()

    def add_stop(self, floor: int) -> bool:
        self._validate_floor(floor)
        if self.state == ElevatorState.OUT_OF_SERVICE:
            raise ValueError("Cannot add a stop to an out-of-service elevator")
        if floor == self.current_floor:
            if self.state == ElevatorState.MOVING:
                raise ValueError("Elevator has already departed from the current floor")
            return False

        self.pending_stops.add(floor)
        self._update_direction()
        return True

    def is_eligible_for(self, floor: int, direction: Direction) -> bool:
        if not self.min_floor <= floor <= self.max_floor:
            return False
        if self.state == ElevatorState.OUT_OF_SERVICE:
            return False
        if self.passenger_count >= self.capacity:
            return False
        if self.direction == Direction.IDLE:
            return True
        if direction != self.direction:
            return False

        if direction == Direction.UP:
            return (
                floor > self.current_floor
                if self.state == ElevatorState.MOVING
                else floor >= self.current_floor
            )
        return (
            floor < self.current_floor
            if self.state == ElevatorState.MOVING
            else floor <= self.current_floor
        )

    def estimated_distance_to(self, floor: int) -> int:
        self._validate_floor(floor)
        return abs(self.current_floor - floor)

    def validate_floor(self, floor: int) -> None:
        self._validate_floor(floor)

    def serve_current_floor(self) -> ElevatorEvent:
        if self.state == ElevatorState.MOVING:
            raise ValueError("A moving elevator cannot open its doors")
        if self.state == ElevatorState.OUT_OF_SERVICE:
            raise ValueError("Elevator is out of service")
        self.pending_stops.discard(self.current_floor)
        self.state = ElevatorState.IDLE
        self.open_door()
        self._update_direction()
        return ElevatorEvent(self.elevator_id, EventType.ARRIVED, self.current_floor)

    def step(self) -> ElevatorEvent | None:
        if self.state == ElevatorState.OUT_OF_SERVICE:
            return None

        if self.door_state == DoorState.OPEN:
            self.close_door()
            self.state = ElevatorState.MOVING if self.pending_stops else ElevatorState.IDLE
            return ElevatorEvent(
                self.elevator_id,
                EventType.DOOR_CLOSED,
                self.current_floor,
            )

        if not self.pending_stops:
            self.state = ElevatorState.IDLE
            self.direction = Direction.IDLE
            return None

        target = self._next_target()
        self.direction = Direction.UP if target > self.current_floor else Direction.DOWN
        self.state = ElevatorState.MOVING
        self.current_floor += self.direction.value

        if self.current_floor in self.pending_stops:
            self.pending_stops.remove(self.current_floor)
            self.state = ElevatorState.IDLE
            self.open_door()
            self._update_direction()
            return ElevatorEvent(
                self.elevator_id,
                EventType.ARRIVED,
                self.current_floor,
            )

        return ElevatorEvent(
            self.elevator_id,
            EventType.MOVED,
            self.current_floor,
        )

    def open_door(self) -> None:
        if self.state == ElevatorState.MOVING:
            raise ValueError("Cannot open the door while the elevator is moving")
        if self.state == ElevatorState.OUT_OF_SERVICE:
            raise ValueError("Cannot open an out-of-service elevator")
        self.door_state = DoorState.OPEN

    def close_door(self) -> None:
        self.door_state = DoorState.CLOSED

    def board_passengers(self, count: int = 1) -> None:
        if self.door_state != DoorState.OPEN:
            raise ValueError("Passengers can board only while the door is open")
        if count <= 0:
            raise ValueError("Passenger count must be greater than zero")
        if self.passenger_count + count > self.capacity:
            raise ValueError("Elevator capacity exceeded")
        self.passenger_count += count

    def exit_passengers(self, count: int = 1) -> None:
        if self.door_state != DoorState.OPEN:
            raise ValueError("Passengers can exit only while the door is open")
        if count <= 0 or count > self.passenger_count:
            raise ValueError("Invalid exiting passenger count")
        self.passenger_count -= count

    def set_out_of_service(self) -> None:
        if self.pending_stops or self.passenger_count:
            raise ValueError("Elevator must be empty with no pending stops")
        if self.state == ElevatorState.MOVING:
            raise ValueError("A moving elevator cannot be taken out of service")
        self.close_door()
        self.direction = Direction.IDLE
        self.state = ElevatorState.OUT_OF_SERVICE

    def restore_service(self) -> None:
        if self.state != ElevatorState.OUT_OF_SERVICE:
            raise ValueError("Elevator is not out of service")
        self.state = ElevatorState.IDLE

    def _next_target(self) -> int:
        above = sorted(floor for floor in self.pending_stops if floor > self.current_floor)
        below = sorted(
            (floor for floor in self.pending_stops if floor < self.current_floor),
            reverse=True,
        )

        if self.direction == Direction.UP and above:
            return above[0]
        if self.direction == Direction.DOWN and below:
            return below[0]
        if above and not below:
            return above[0]
        if below and not above:
            return below[0]
        return min(self.pending_stops, key=lambda floor: (abs(floor - self.current_floor), floor))

    def _update_direction(self) -> None:
        if not self.pending_stops:
            self.direction = Direction.IDLE
            return

        above = any(floor > self.current_floor for floor in self.pending_stops)
        below = any(floor < self.current_floor for floor in self.pending_stops)
        if self.direction == Direction.UP and above:
            return
        if self.direction == Direction.DOWN and below:
            return
        if above and not below:
            self.direction = Direction.UP
        elif below and not above:
            self.direction = Direction.DOWN
        else:
            nearest = min(
                self.pending_stops,
                key=lambda floor: (abs(floor - self.current_floor), floor),
            )
            self.direction = Direction.UP if nearest > self.current_floor else Direction.DOWN

    def _validate_floor(self, floor: int) -> None:
        if not self.min_floor <= floor <= self.max_floor:
            raise ValueError(
                f"Floor {floor} is outside elevator {self.elevator_id}'s range"
            )
