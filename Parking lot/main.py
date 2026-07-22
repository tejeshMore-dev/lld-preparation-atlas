from models.enums import VehicleType
from models.enums import PaymentMethod

from models.vehicle import Vehicle
from models.parking_floor import ParkingFloor
from models.parking_spots import ParkingSpot, SpotType

from services.parking_lot import ParkingLot
from services.payment_processor import UPIPaymentProcessor

from strategies.decorators import WeekendSurchargeDecorator
from strategies.allocation import NearestFirstStratergy
from strategies.pricing import HourlySlabStratergy


def build_parking_lot():
    allocation_strategy = NearestFirstStratergy()
    pricing_strategy = WeekendSurchargeDecorator(HourlySlabStratergy(), surcharge_percentage=20)
    payment_processor = UPIPaymentProcessor()

    parking_lot =ParkingLot("My Parking Lot", allocation_strategy, pricing_strategy, payment_processor)

    floor1 = ParkingFloor(1) 
    floor1.add_spot( ParkingSpot( "A1", SpotType.COMPACT, distance_from_entrance=5, floor_number=floor1.floor_id ) ) 
    floor1.add_spot( ParkingSpot( "A2", SpotType.LARGE, distance_from_entrance=15, floor_number=floor1.floor_id ) ) 
    floor1.add_spot( ParkingSpot( "A3", SpotType.REGULAR, distance_from_entrance=2, floor_number=floor1.floor_id ) ) 
    parking_lot.add_floor(floor1)

    return parking_lot


def main():
    parking_lot = build_parking_lot()

    car = Vehicle("MH12AB1234", VehicleType.CAR) 
    bike = Vehicle("MH14XY9999", VehicleType.MOTORCYCLE)

    ticket1 = parking_lot.park_vehicle(car)
    ticket2 = parking_lot.park_vehicle(bike)

    receipt1 = parking_lot.exit_vehicle( ticket1.ticket_id, PaymentMethod.UPI)
    print(f"Receipt for ticket_id {ticket1.ticket_id}: Amount Paid: {receipt1.amount}, Payment Method: {receipt1.payment_method}, Status: {receipt1.status}")

    receipt2 = parking_lot.exit_vehicle( ticket2.ticket_id, PaymentMethod.UPI)
    print(f"Receipt for ticket_id {ticket2.ticket_id}: Amount Paid: {receipt2.amount}, Payment Method: {receipt2.payment_method}, Status: {receipt2.status}")
    
if __name__ == "__main__":
    main()