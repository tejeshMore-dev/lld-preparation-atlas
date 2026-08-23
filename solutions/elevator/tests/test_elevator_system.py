import unittest

from models.elevator_car import ElevatorCar
from models.enums import (
    Direction,
    DoorState,
    ElevatorState,
    EventType,
    RequestStatus,
)
from services.elevator_system import ElevatorSystem
from strategies.direction_aware_nearest_strategy import DirectionAwareNearestStrategy
from strategies.least_stops_strategy import LeastStopsStrategy


class ElevatorSystemTest(unittest.TestCase):
    @staticmethod
    def make_system(
        cars: list[ElevatorCar] | None = None,
        strategy=None,
    ) -> ElevatorSystem:
        return ElevatorSystem(
            elevators=cars
            or [
                ElevatorCar("E1", 0, 10, current_floor=0),
                ElevatorCar("E2", 0, 10, current_floor=7),
            ],
            scheduling_strategy=strategy or DirectionAwareNearestStrategy(),
        )

    def test_nearest_elevator_is_assigned(self) -> None:
        system = self.make_system()

        request = system.request_elevator(6, Direction.DOWN)

        self.assertEqual(request.status, RequestStatus.ASSIGNED)
        self.assertEqual(request.assigned_elevator_id, "E2")
        self.assertIn(6, system.elevators["E2"].pending_stops)

    def test_opposite_direction_request_waits_then_completes(self) -> None:
        system = self.make_system([ElevatorCar("E1", 0, 10, current_floor=0)])
        upward = system.request_elevator(5, Direction.UP)
        downward = system.request_elevator(3, Direction.DOWN)

        self.assertEqual(upward.status, RequestStatus.ASSIGNED)
        self.assertEqual(downward.status, RequestStatus.PENDING)

        system.run_until_idle()

        self.assertEqual(upward.status, RequestStatus.COMPLETED)
        self.assertEqual(downward.status, RequestStatus.COMPLETED)
        self.assertEqual(system.elevators["E1"].current_floor, 3)

    def test_car_uses_look_order_for_internal_stops(self) -> None:
        system = self.make_system([ElevatorCar("E1", 0, 10, current_floor=0)])
        system.select_floor("E1", 5)
        system.select_floor("E1", 2)
        system.select_floor("E1", 4)

        events = system.run_until_idle()
        arrivals = [
            event.floor
            for event in events
            if event.event_type == EventType.ARRIVED
        ]

        self.assertEqual(arrivals, [2, 4, 5])
        self.assertTrue(
            all(
                request.status == RequestStatus.COMPLETED
                for request in system.car_requests.values()
            )
        )

    def test_current_floor_request_is_completed_immediately(self) -> None:
        system = self.make_system([ElevatorCar("E1", 0, 10, current_floor=4)])

        request = system.request_elevator(4, Direction.UP)

        self.assertEqual(request.status, RequestStatus.COMPLETED)
        self.assertEqual(request.assigned_elevator_id, "E1")
        self.assertEqual(system.elevators["E1"].door_state, DoorState.OPEN)

    def test_rejected_internal_request_does_not_leave_partial_state(self) -> None:
        system = self.make_system([ElevatorCar("E1", 0, 10, current_floor=0)])
        system.select_floor("E1", 3)
        system.tick()

        with self.assertRaises(ValueError):
            system.select_floor("E1", 1)

        self.assertEqual(len(system.car_requests), 1)

    def test_door_and_capacity_safety(self) -> None:
        car = ElevatorCar("E1", 0, 10, current_floor=0, capacity=2)
        car.serve_current_floor()
        car.board_passengers(2)

        with self.assertRaises(ValueError):
            car.board_passengers(1)

        car.exit_passengers(1)
        car.close_door()
        with self.assertRaises(ValueError):
            car.board_passengers(1)

        car.add_stop(3)
        car.step()
        self.assertEqual(car.state, ElevatorState.MOVING)
        with self.assertRaises(ValueError):
            car.open_door()

    def test_out_of_service_car_is_not_scheduled(self) -> None:
        first = ElevatorCar("E1", 0, 10, current_floor=2)
        second = ElevatorCar("E2", 0, 10, current_floor=8)
        system = self.make_system([first, second])
        system.set_out_of_service("E1")

        request = system.request_elevator(3, Direction.UP)

        self.assertEqual(request.assigned_elevator_id, "E2")

    def test_pending_request_dispatches_after_service_restoration(self) -> None:
        car = ElevatorCar("E1", 0, 10, current_floor=0)
        system = self.make_system([car])
        system.set_out_of_service("E1")
        request = system.request_elevator(3, Direction.UP)
        self.assertEqual(request.status, RequestStatus.PENDING)

        system.restore_service("E1")
        system.run_until_idle()

        self.assertEqual(request.status, RequestStatus.COMPLETED)

    def test_duplicate_active_hall_requests_are_coalesced(self) -> None:
        system = self.make_system()

        first = system.request_elevator(4, Direction.UP)
        second = system.request_elevator(4, Direction.UP)

        self.assertIs(first, second)
        self.assertEqual(len(system.hall_requests), 1)

    def test_floor_and_direction_validation(self) -> None:
        system = self.make_system()

        with self.assertRaises(ValueError):
            system.request_elevator(11, Direction.DOWN)
        with self.assertRaises(ValueError):
            system.request_elevator(10, Direction.UP)
        with self.assertRaises(ValueError):
            system.request_elevator(0, Direction.DOWN)
        with self.assertRaises(ValueError):
            system.request_elevator(3, Direction.IDLE)

    def test_all_cars_must_share_the_building_floor_range(self) -> None:
        with self.assertRaises(ValueError):
            self.make_system(
                [
                    ElevatorCar("E1", 0, 10),
                    ElevatorCar("E2", 0, 20),
                ]
            )

    def test_least_stops_strategy_is_replaceable(self) -> None:
        first = ElevatorCar("E1", 0, 10, current_floor=2)
        second = ElevatorCar("E2", 0, 10, current_floor=8)
        first.add_stop(4)
        first.add_stop(6)
        system = self.make_system([first, second], LeastStopsStrategy())

        request = system.request_elevator(5, Direction.UP)

        self.assertEqual(request.assigned_elevator_id, "E2")


if __name__ == "__main__":
    unittest.main()
