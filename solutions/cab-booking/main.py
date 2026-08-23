from datetime import datetime, timedelta

from models.driver import Driver
from models.enums import PaymentMethod, VehicleType
from models.location import Location
from models.rider import Rider
from models.vehicle import Vehicle
from services.catalog_service import CatalogService
from services.clock import Clock
from services.in_memory_payment_gateway import InMemoryPaymentGateway
from services.ride_service import RideService
from strategies.haversine_distance_strategy import HaversineDistanceStrategy
from strategies.nearest_driver_strategy import NearestDriverStrategy
from strategies.standard_fare_strategy import StandardFareStrategy


class DemoClock(Clock):
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current


def build_demo() -> tuple[CatalogService, RideService, DemoClock]:
    clock = DemoClock(datetime.now())
    catalog = CatalogService()
    catalog.add_rider(Rider("rider-1", "Asha", "asha@example.com", "9000000001"))
    pickup = Location(12.9716, 77.5946)
    drivers = [
        Driver(
            "driver-1",
            "Deepa",
            "9111111111",
            Vehicle("cab-1", "KA01AA1001", "Hatchback", VehicleType.MINI, 4),
            Location(12.9720, 77.5950),
        ),
        Driver(
            "driver-2",
            "Manoj",
            "9222222222",
            Vehicle("cab-2", "KA01AA1002", "Hatchback", VehicleType.MINI, 4),
            Location(12.9900, 77.6000),
        ),
    ]
    for driver in drivers:
        catalog.add_driver(driver)

    distance = HaversineDistanceStrategy()
    service = RideService(
        catalog,
        distance,
        NearestDriverStrategy(distance),
        StandardFareStrategy(),
        InMemoryPaymentGateway(clock),
        clock,
    )
    for driver in drivers:
        service.go_online(driver.driver_id)
    return catalog, service, clock


def main() -> None:
    catalog, service, clock = build_demo()
    pickup = Location(12.9716, 77.5946)
    dropoff = Location(12.9352, 77.6245)
    nearby = service.find_nearby_drivers(pickup, VehicleType.MINI)
    print("Nearby drivers:", [driver.name for driver in nearby])

    ride = service.request_ride("rider-1", pickup, dropoff, VehicleType.MINI)
    driver = catalog.get_driver(ride.driver_id)
    print(f"Assigned {driver.name}; estimated fare Rs. {ride.estimated_fare}")
    service.start_ride(ride.ride_id, driver.driver_id)
    clock.current += timedelta(minutes=20)
    service.complete_ride(ride.ride_id, driver.driver_id, actual_distance_km="8")
    print(f"Ride {ride.status.name}; final fare Rs. {ride.final_fare}")

    payment = service.pay_for_ride(ride.ride_id, PaymentMethod.UPI)
    service.rate_driver(ride.ride_id, "rider-1", 5)
    print(f"Payment {payment.status.name}; driver rating {driver.average_rating}")


if __name__ == "__main__":
    main()
