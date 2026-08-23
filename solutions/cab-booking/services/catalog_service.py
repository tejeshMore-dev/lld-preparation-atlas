from models.driver import Driver
from models.enums import DriverStatus
from models.rider import Rider


class CatalogService:
    """Manages registered riders, drivers, vehicles, and driver availability."""

    def __init__(self) -> None:
        self.riders: dict[str, Rider] = {}
        self.drivers: dict[str, Driver] = {}

    def add_rider(self, rider: Rider) -> None:
        if rider.rider_id in self.riders:
            raise ValueError(f"Rider '{rider.rider_id}' already exists")
        if any(existing.email.casefold() == rider.email.casefold() for existing in self.riders.values()):
            raise ValueError(f"Email '{rider.email}' is already registered")
        if any(existing.phone == rider.phone for existing in self.riders.values()):
            raise ValueError(f"Phone '{rider.phone}' is already registered")
        self.riders[rider.rider_id] = rider

    def add_driver(self, driver: Driver) -> None:
        if driver.driver_id in self.drivers:
            raise ValueError(f"Driver '{driver.driver_id}' already exists")
        if driver.status is DriverStatus.ON_TRIP:
            raise ValueError("A newly registered driver cannot already be on a trip")
        if driver.vehicle.capacity <= 0:
            raise ValueError("Vehicle capacity must be positive")
        if any(existing.phone == driver.phone for existing in self.drivers.values()):
            raise ValueError(f"Driver phone '{driver.phone}' is already registered")
        if any(
            existing.vehicle.vehicle_id == driver.vehicle.vehicle_id
            for existing in self.drivers.values()
        ):
            raise ValueError(f"Vehicle '{driver.vehicle.vehicle_id}' is already registered")
        if any(
            existing.vehicle.registration_number.casefold()
            == driver.vehicle.registration_number.casefold()
            for existing in self.drivers.values()
        ):
            raise ValueError(
                f"Registration '{driver.vehicle.registration_number}' is already registered"
            )
        self.drivers[driver.driver_id] = driver

    def get_rider(self, rider_id: str) -> Rider:
        try:
            return self.riders[rider_id]
        except KeyError as error:
            raise ValueError(f"Rider '{rider_id}' does not exist") from error

    def get_driver(self, driver_id: str) -> Driver:
        try:
            return self.drivers[driver_id]
        except KeyError as error:
            raise ValueError(f"Driver '{driver_id}' does not exist") from error
