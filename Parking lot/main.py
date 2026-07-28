from models.enums import PaymentMethod, SpotType, VehicleType
from models.parking_floor import ParkingFloor
from models.parking_spots import ParkingSpot
from models.vehicle import Vehicle
from services.parking_lot import ParkingLot
from services.payment_processor import UPIPaymentProcessor
from strategies.allocation import NearestFirstStrategy
from strategies.decorators import WeekendSurchargeDecorator
from strategies.pricing import HourlySlabStrategy


def build_parking_lot() -> ParkingLot:
    parking_lot = ParkingLot(
        name="My Parking Lot",
        spot_allocation_strategy=NearestFirstStrategy(),
        pricing_strategy=WeekendSurchargeDecorator(
            HourlySlabStrategy(),
            surcharge_percentage=20,
        ),
        payment_processor=UPIPaymentProcessor(),
    )

    floor1 = ParkingFloor(1)
    floor1.add_spot(ParkingSpot("A1", SpotType.COMPACT, 1, 5))
    floor1.add_spot(ParkingSpot("A2", SpotType.LARGE, 1, 15))
    floor1.add_spot(ParkingSpot("A3", SpotType.REGULAR, 1, 2))
    parking_lot.add_floor(floor1)
    return parking_lot


def main() -> None:
    parking_lot = build_parking_lot()
    car = Vehicle("MH12AB1234", VehicleType.CAR)
    bike = Vehicle("MH14XY9999", VehicleType.MOTORCYCLE)

    car_ticket = parking_lot.park_vehicle(car)
    bike_ticket = parking_lot.park_vehicle(bike)

    print(parking_lot.exit_vehicle(car_ticket.ticket_id, PaymentMethod.UPI))
    print(parking_lot.exit_vehicle(bike_ticket.ticket_id, PaymentMethod.UPI))


if __name__ == "__main__":
    main()
