from decimal import Decimal, InvalidOperation
from threading import RLock
from uuid import uuid4

from models.driver import Driver
from models.enums import DriverStatus, PaymentMethod, PaymentStatus, RideStatus, VehicleType
from models.location import Location
from models.payment import Payment
from models.ride import Ride
from services.catalog_service import CatalogService
from services.clock import Clock, SystemClock
from services.payment_gateway import PaymentGateway
from strategies.distance_strategy import DistanceStrategy
from strategies.fare_strategy import FareStrategy
from strategies.matching_strategy import MatchingStrategy


class RideService:
    """Coordinates estimates, dispatch, trip state, payment, and ratings."""

    ACTIVE_RIDE_STATUSES = {
        RideStatus.REQUESTED,
        RideStatus.DRIVER_ASSIGNED,
        RideStatus.IN_PROGRESS,
    }

    def __init__(
        self,
        catalog: CatalogService,
        distance_strategy: DistanceStrategy,
        matching_strategy: MatchingStrategy,
        fare_strategy: FareStrategy,
        payment_gateway: PaymentGateway,
        clock: Clock | None = None,
        max_pickup_distance_km: Decimal | int | float | str = "10",
        average_speed_kmph: Decimal | int | float | str = "30",
    ) -> None:
        self._catalog = catalog
        self._distance_strategy = distance_strategy
        self._matching_strategy = matching_strategy
        self._fare_strategy = fare_strategy
        self._payment_gateway = payment_gateway
        self._clock = clock or SystemClock()
        self._max_pickup_distance_km = self._to_distance(max_pickup_distance_km)
        self._average_speed_kmph = self._to_distance(average_speed_kmph)
        if self._max_pickup_distance_km <= 0 or self._average_speed_kmph <= 0:
            raise ValueError("Pickup radius and average speed must be positive")
        # This is the atomic in-process dispatch boundary. Production systems
        # commonly partition it geographically and use durable atomic claims.
        self._dispatch_lock = RLock()
        self.rides: dict[str, Ride] = {}
        self.payments: dict[str, Payment] = {}

    def go_online(self, driver_id: str, location: Location | None = None) -> Driver:
        with self._dispatch_lock:
            driver = self._catalog.get_driver(driver_id)
            if driver.status is DriverStatus.ON_TRIP:
                raise ValueError("A driver on a trip cannot change availability")
            if location is not None:
                driver.location = location
            driver.status = DriverStatus.AVAILABLE
            return driver

    def go_offline(self, driver_id: str) -> Driver:
        with self._dispatch_lock:
            driver = self._catalog.get_driver(driver_id)
            if driver.status is DriverStatus.ON_TRIP:
                raise ValueError("A driver on a trip cannot go offline")
            driver.status = DriverStatus.OFFLINE
            return driver

    def update_driver_location(self, driver_id: str, location: Location) -> Driver:
        with self._dispatch_lock:
            driver = self._catalog.get_driver(driver_id)
            driver.location = location
            return driver

    def find_nearby_drivers(
        self,
        pickup: Location,
        vehicle_type: VehicleType,
        max_distance_km: Decimal | int | float | str | None = None,
    ) -> list[Driver]:
        radius = (
            self._max_pickup_distance_km
            if max_distance_km is None
            else self._to_distance(max_distance_km)
        )
        if radius <= 0:
            raise ValueError("Search radius must be positive")
        with self._dispatch_lock:
            candidates = [
                driver
                for driver in self._catalog.drivers.values()
                if driver.status is DriverStatus.AVAILABLE
                and driver.vehicle.vehicle_type is vehicle_type
                and self._distance_strategy.calculate_km(driver.location, pickup) <= radius
            ]
            return sorted(
                candidates,
                key=lambda driver: (
                    self._distance_strategy.calculate_km(driver.location, pickup),
                    driver.driver_id,
                ),
            )

    def request_ride(
        self,
        rider_id: str,
        pickup: Location,
        dropoff: Location,
        vehicle_type: VehicleType,
    ) -> Ride:
        self._catalog.get_rider(rider_id)
        distance = self._distance_strategy.calculate_km(pickup, dropoff)
        if distance <= 0:
            raise ValueError("Pickup and drop-off must be different")
        estimated_duration = (
            distance / self._average_speed_kmph * Decimal("60")
        ).quantize(Decimal("0.01"))

        with self._dispatch_lock:
            if any(
                ride.rider_id == rider_id and ride.status in self.ACTIVE_RIDE_STATUSES
                for ride in self.rides.values()
            ):
                raise ValueError("Rider already has an active ride")
            ride = Ride(
                ride_id=str(uuid4()),
                rider_id=rider_id,
                pickup=pickup,
                dropoff=dropoff,
                vehicle_type=vehicle_type,
                estimated_distance_km=distance,
                estimated_duration_minutes=estimated_duration,
                estimated_fare=self._fare_strategy.calculate(
                    vehicle_type,
                    distance,
                    estimated_duration,
                ),
                requested_at=self._clock.now(),
            )
            self.rides[ride.ride_id] = ride
            self._try_match_locked(ride)
            return ride

    def retry_matching(self, ride_id: str) -> Ride:
        with self._dispatch_lock:
            ride = self.get_ride(ride_id)
            if ride.status is not RideStatus.REQUESTED:
                raise ValueError("Only an unmatched requested ride can be retried")
            self._try_match_locked(ride)
            return ride

    def start_ride(self, ride_id: str, driver_id: str) -> Ride:
        with self._dispatch_lock:
            ride = self.get_ride(ride_id)
            if ride.status is RideStatus.IN_PROGRESS:
                return ride
            if ride.status is not RideStatus.DRIVER_ASSIGNED:
                raise ValueError("Ride must have an assigned driver before it can start")
            if ride.driver_id != driver_id:
                raise ValueError("Only the assigned driver can start this ride")
            driver = self._catalog.get_driver(driver_id)
            if driver.status is not DriverStatus.ON_TRIP:
                raise RuntimeError("Assigned driver is not reserved for this ride")
            ride.status = RideStatus.IN_PROGRESS
            ride.started_at = self._clock.now()
            driver.location = ride.pickup
            return ride

    def complete_ride(
        self,
        ride_id: str,
        driver_id: str,
        actual_distance_km: Decimal | int | float | str | None = None,
    ) -> Ride:
        with self._dispatch_lock:
            ride = self.get_ride(ride_id)
            if ride.status is RideStatus.COMPLETED:
                return ride
            if ride.status is not RideStatus.IN_PROGRESS:
                raise ValueError("Only an in-progress ride can be completed")
            if ride.driver_id != driver_id:
                raise ValueError("Only the assigned driver can complete this ride")
            if ride.started_at is None:
                raise RuntimeError("In-progress ride has no start time")
            now = self._clock.now()
            elapsed_seconds = (now - ride.started_at).total_seconds()
            if elapsed_seconds < 0:
                raise ValueError("Completion time cannot precede start time")
            distance = (
                self._distance_strategy.calculate_km(ride.pickup, ride.dropoff)
                if actual_distance_km is None
                else self._to_distance(actual_distance_km)
            )
            if distance <= 0:
                raise ValueError("Actual trip distance must be positive")
            duration = Decimal(str(elapsed_seconds / 60)).quantize(Decimal("0.01"))
            final_fare = self._fare_strategy.calculate(
                ride.vehicle_type,
                distance,
                duration,
            )

            ride.actual_distance_km = distance
            ride.actual_duration_minutes = duration
            ride.final_fare = final_fare
            ride.completed_at = now
            ride.status = RideStatus.COMPLETED
            driver = self._catalog.get_driver(driver_id)
            driver.location = ride.dropoff
            driver.status = DriverStatus.AVAILABLE
            return ride

    def cancel_ride(self, ride_id: str, reason: str) -> Ride:
        if not reason.strip():
            raise ValueError("Cancellation reason is required")
        with self._dispatch_lock:
            ride = self.get_ride(ride_id)
            if ride.status is RideStatus.CANCELLED:
                return ride
            if ride.status not in {RideStatus.REQUESTED, RideStatus.DRIVER_ASSIGNED}:
                raise ValueError(f"Ride cannot be cancelled in {ride.status.name} state")
            if ride.driver_id is not None:
                driver = self._catalog.get_driver(ride.driver_id)
                driver.status = DriverStatus.AVAILABLE
            ride.status = RideStatus.CANCELLED
            ride.cancelled_at = self._clock.now()
            ride.cancellation_reason = reason.strip()
            return ride

    def pay_for_ride(self, ride_id: str, method: PaymentMethod) -> Payment:
        with self._dispatch_lock:
            ride = self.get_ride(ride_id)
            if ride.status is not RideStatus.COMPLETED or ride.final_fare is None:
                raise ValueError("Only a completed ride can be paid")
            for payment_id in reversed(ride.payment_ids):
                payment = self.payments[payment_id]
                if payment.status is PaymentStatus.COMPLETED:
                    return payment
            payment = self._payment_gateway.charge(ride.ride_id, ride.final_fare, method)
            self.payments[payment.payment_id] = payment
            ride.payment_ids.append(payment.payment_id)
            return payment

    def rate_driver(self, ride_id: str, rider_id: str, rating: int) -> Driver:
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        with self._dispatch_lock:
            ride = self.get_ride(ride_id)
            if ride.rider_id != rider_id:
                raise ValueError("Only the ride's rider can rate its driver")
            if ride.status is not RideStatus.COMPLETED:
                raise ValueError("Only a completed ride can be rated")
            if not any(
                self.payments[payment_id].status is PaymentStatus.COMPLETED
                for payment_id in ride.payment_ids
            ):
                raise ValueError("Ride must be paid before rating")
            if ride.driver_rating is not None:
                raise ValueError("Driver has already been rated for this ride")
            if ride.driver_id is None:
                raise RuntimeError("Completed ride has no driver")
            driver = self._catalog.get_driver(ride.driver_id)
            total = driver.average_rating * driver.rating_count + Decimal(rating)
            driver.rating_count += 1
            driver.average_rating = (total / driver.rating_count).quantize(Decimal("0.01"))
            ride.driver_rating = rating
            return driver

    def get_ride(self, ride_id: str) -> Ride:
        try:
            return self.rides[ride_id]
        except KeyError as error:
            raise ValueError(f"Ride '{ride_id}' does not exist") from error

    def get_rider_history(self, rider_id: str) -> list[Ride]:
        self._catalog.get_rider(rider_id)
        return sorted(
            (ride for ride in list(self.rides.values()) if ride.rider_id == rider_id),
            key=lambda ride: ride.requested_at,
            reverse=True,
        )

    def get_driver_history(self, driver_id: str) -> list[Ride]:
        self._catalog.get_driver(driver_id)
        return sorted(
            (ride for ride in list(self.rides.values()) if ride.driver_id == driver_id),
            key=lambda ride: ride.requested_at,
            reverse=True,
        )

    def _try_match_locked(self, ride: Ride) -> None:
        candidates = [
            driver
            for driver in self._catalog.drivers.values()
            if driver.status is DriverStatus.AVAILABLE
            and driver.vehicle.vehicle_type is ride.vehicle_type
            and self._distance_strategy.calculate_km(driver.location, ride.pickup)
            <= self._max_pickup_distance_km
        ]
        driver = self._matching_strategy.select_driver(candidates, ride.pickup)
        if driver is None:
            return
        driver.status = DriverStatus.ON_TRIP
        ride.driver_id = driver.driver_id
        ride.assigned_at = self._clock.now()
        ride.status = RideStatus.DRIVER_ASSIGNED

    @staticmethod
    def _to_distance(value: Decimal | int | float | str) -> Decimal:
        try:
            distance = Decimal(str(value)).quantize(Decimal("0.001"))
        except (InvalidOperation, ValueError) as error:
            raise ValueError(f"Invalid distance value: {value}") from error
        if not distance.is_finite():
            raise ValueError("Distance must be finite")
        return distance
