import threading
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from models.driver import Driver
from models.enums import DriverStatus, PaymentMethod, PaymentStatus, RideStatus, VehicleType
from models.location import Location
from models.rider import Rider
from models.vehicle import Vehicle
from services.catalog_service import CatalogService
from services.clock import Clock
from services.in_memory_payment_gateway import InMemoryPaymentGateway
from services.ride_service import RideService
from strategies.haversine_distance_strategy import HaversineDistanceStrategy
from strategies.highest_rated_driver_strategy import HighestRatedDriverStrategy
from strategies.nearest_driver_strategy import NearestDriverStrategy
from strategies.standard_fare_strategy import StandardFareStrategy
from strategies.surge_pricing_decorator import SurgePricingDecorator


class MutableClock(Clock):
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current

    def advance(self, **kwargs) -> None:
        self.current += timedelta(**kwargs)


class CabBookingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = MutableClock(datetime(2030, 1, 1, 10, 0))
        self.catalog = CatalogService()
        self.catalog.add_rider(Rider("r1", "Asha", "asha@example.com", "9000000001"))
        self.catalog.add_rider(Rider("r2", "Ravi", "ravi@example.com", "9000000002"))
        self.pickup = Location(12.9716, 77.5946)
        self.dropoff = Location(12.9352, 77.6245)

        self.driver1 = Driver(
            "d1",
            "Deepa",
            "9111111111",
            Vehicle("v1", "KA01AA1001", "Hatchback", VehicleType.MINI, 4),
            Location(12.9720, 77.5950),
            average_rating=Decimal("4.50"),
            rating_count=10,
        )
        self.driver2 = Driver(
            "d2",
            "Manoj",
            "9222222222",
            Vehicle("v2", "KA01AA1002", "Hatchback", VehicleType.MINI, 4),
            Location(12.9900, 77.6000),
            average_rating=Decimal("4.90"),
            rating_count=20,
        )
        self.driver3 = Driver(
            "d3",
            "Sara",
            "9333333333",
            Vehicle("v3", "KA01AA1003", "Sedan", VehicleType.SEDAN, 4),
            Location(12.9718, 77.5948),
        )
        for driver in (self.driver1, self.driver2, self.driver3):
            self.catalog.add_driver(driver)

        self.distance = HaversineDistanceStrategy()
        self.fare = StandardFareStrategy()
        self.gateway = InMemoryPaymentGateway(self.clock)
        self.service = RideService(
            self.catalog,
            self.distance,
            NearestDriverStrategy(self.distance),
            self.fare,
            self.gateway,
            self.clock,
        )
        for driver in (self.driver1, self.driver2, self.driver3):
            self.service.go_online(driver.driver_id)

    def request_mini(self, rider_id: str = "r1"):
        return self.service.request_ride(
            rider_id,
            self.pickup,
            self.dropoff,
            VehicleType.MINI,
        )

    def complete_ride(self):
        ride = self.request_mini()
        self.service.start_ride(ride.ride_id, ride.driver_id)
        self.clock.advance(minutes=20)
        self.service.complete_ride(ride.ride_id, ride.driver_id, "8")
        return ride

    def test_location_validation_and_haversine_distance(self) -> None:
        with self.assertRaisesRegex(ValueError, "Latitude"):
            Location(91, 0)
        self.assertEqual(Decimal("0.000"), self.distance.calculate_km(self.pickup, self.pickup))
        self.assertGreater(self.distance.calculate_km(self.pickup, self.dropoff), 0)

    def test_nearby_drivers_are_filtered_and_sorted_by_distance(self) -> None:
        drivers = self.service.find_nearby_drivers(
            self.pickup,
            VehicleType.MINI,
            max_distance_km="5",
        )
        self.assertEqual(["d1", "d2"], [driver.driver_id for driver in drivers])

    def test_request_estimates_and_assigns_nearest_compatible_driver(self) -> None:
        ride = self.request_mini()
        self.assertIs(RideStatus.DRIVER_ASSIGNED, ride.status)
        self.assertEqual("d1", ride.driver_id)
        self.assertIs(DriverStatus.ON_TRIP, self.driver1.status)
        self.assertGreater(ride.estimated_distance_km, 0)
        self.assertGreaterEqual(ride.estimated_fare, Decimal("80.00"))

    def test_vehicle_type_filters_driver_candidates(self) -> None:
        ride = self.service.request_ride(
            "r1", self.pickup, self.dropoff, VehicleType.SEDAN
        )
        self.assertEqual("d3", ride.driver_id)
        self.assertIs(DriverStatus.AVAILABLE, self.driver1.status)

    def test_highest_rated_strategy_is_replaceable(self) -> None:
        rated_service = RideService(
            self.catalog,
            self.distance,
            HighestRatedDriverStrategy(self.distance),
            self.fare,
            self.gateway,
            self.clock,
        )
        ride = rated_service.request_ride(
            "r1", self.pickup, self.dropoff, VehicleType.MINI
        )
        self.assertEqual("d2", ride.driver_id)

    def test_unmatched_request_can_be_retried_when_driver_comes_online(self) -> None:
        ride = self.service.request_ride(
            "r1", self.pickup, self.dropoff, VehicleType.SUV
        )
        self.assertIs(RideStatus.REQUESTED, ride.status)
        suv_driver = Driver(
            "d4",
            "Kabir",
            "9444444444",
            Vehicle("v4", "KA01AA1004", "SUV", VehicleType.SUV, 6),
            Location(12.972, 77.595),
        )
        self.catalog.add_driver(suv_driver)
        self.service.go_online("d4")
        self.service.retry_matching(ride.ride_id)
        self.assertIs(RideStatus.DRIVER_ASSIGNED, ride.status)
        self.assertEqual("d4", ride.driver_id)

    def test_rider_cannot_have_two_active_rides(self) -> None:
        self.request_mini()
        with self.assertRaisesRegex(ValueError, "active ride"):
            self.service.request_ride(
                "r1", self.pickup, self.dropoff, VehicleType.SEDAN
            )

    def test_assigned_ride_cancellation_releases_driver(self) -> None:
        ride = self.request_mini()
        self.service.cancel_ride(ride.ride_id, "Changed plans")
        self.assertIs(RideStatus.CANCELLED, ride.status)
        self.assertEqual("Changed plans", ride.cancellation_reason)
        self.assertIs(DriverStatus.AVAILABLE, self.driver1.status)

    def test_only_assigned_driver_can_start_or_complete(self) -> None:
        ride = self.request_mini()
        with self.assertRaisesRegex(ValueError, "assigned driver"):
            self.service.start_ride(ride.ride_id, "d2")
        self.service.start_ride(ride.ride_id, "d1")
        with self.assertRaisesRegex(ValueError, "assigned driver"):
            self.service.complete_ride(ride.ride_id, "d2", "5")

    def test_in_progress_ride_cannot_be_cancelled(self) -> None:
        ride = self.request_mini()
        self.service.start_ride(ride.ride_id, ride.driver_id)
        with self.assertRaisesRegex(ValueError, "IN_PROGRESS"):
            self.service.cancel_ride(ride.ride_id, "Stop")

    def test_completion_calculates_final_fare_and_releases_driver(self) -> None:
        ride = self.complete_ride()
        self.assertIs(RideStatus.COMPLETED, ride.status)
        self.assertEqual(Decimal("8.000"), ride.actual_distance_km)
        self.assertEqual(Decimal("20.00"), ride.actual_duration_minutes)
        self.assertEqual(Decimal("166.00"), ride.final_fare)
        self.assertIs(DriverStatus.AVAILABLE, self.driver1.status)
        self.assertEqual(self.dropoff, self.driver1.location)

    def test_payment_failure_retry_and_idempotency(self) -> None:
        ride = self.complete_ride()
        self.gateway.fail_next_charge = True
        failed = self.service.pay_for_ride(ride.ride_id, PaymentMethod.CARD)
        self.assertIs(PaymentStatus.FAILED, failed.status)
        completed = self.service.pay_for_ride(ride.ride_id, PaymentMethod.UPI)
        repeated = self.service.pay_for_ride(ride.ride_id, PaymentMethod.UPI)
        self.assertIs(PaymentStatus.COMPLETED, completed.status)
        self.assertIs(completed, repeated)
        self.assertEqual(2, len(ride.payment_ids))

    def test_driver_rating_requires_paid_completed_ride(self) -> None:
        ride = self.complete_ride()
        with self.assertRaisesRegex(ValueError, "paid"):
            self.service.rate_driver(ride.ride_id, "r1", 4)
        self.service.pay_for_ride(ride.ride_id, PaymentMethod.CASH)
        driver = self.service.rate_driver(ride.ride_id, "r1", 4)
        self.assertEqual(11, driver.rating_count)
        self.assertEqual(Decimal("4.45"), driver.average_rating)
        with self.assertRaisesRegex(ValueError, "already"):
            self.service.rate_driver(ride.ride_id, "r1", 5)

    def test_surge_pricing_decorator(self) -> None:
        surge = SurgePricingDecorator(self.fare, "1.5")
        self.assertEqual(
            Decimal("249.00"),
            surge.calculate(VehicleType.MINI, Decimal("8"), Decimal("20")),
        )

    def test_driver_cannot_go_offline_while_reserved(self) -> None:
        self.request_mini()
        with self.assertRaisesRegex(ValueError, "cannot go offline"):
            self.service.go_offline("d1")

    def test_completed_and_cancelled_rides_allow_new_request(self) -> None:
        cancelled = self.request_mini()
        self.service.cancel_ride(cancelled.ride_id, "No longer needed")
        replacement = self.request_mini()
        self.assertIs(RideStatus.DRIVER_ASSIGNED, replacement.status)

    def test_rider_and_driver_history_are_newest_first(self) -> None:
        first = self.request_mini()
        self.service.cancel_ride(first.ride_id, "Changed plans")
        self.clock.advance(seconds=1)
        second = self.request_mini()
        self.assertEqual([second, first], self.service.get_rider_history("r1"))
        self.assertEqual([second, first], self.service.get_driver_history("d1"))

    def test_concurrent_requests_assign_one_available_driver_once(self) -> None:
        self.service.go_offline("d2")
        barrier = threading.Barrier(2)
        rides = []

        def request(rider_id: str) -> None:
            barrier.wait()
            rides.append(self.request_mini(rider_id))

        threads = [
            threading.Thread(target=request, args=("r1",)),
            threading.Thread(target=request, args=("r2",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(1, sum(ride.status is RideStatus.DRIVER_ASSIGNED for ride in rides))
        self.assertEqual(1, sum(ride.status is RideStatus.REQUESTED for ride in rides))
        self.assertEqual(1, sum(ride.driver_id == "d1" for ride in rides))


if __name__ == "__main__":
    unittest.main()
