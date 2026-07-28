import unittest
from datetime import datetime, timedelta

from models.enums import (
    PaymentMethod,
    PaymentStatus,
    SpotType,
    TicketStatus,
    VehicleType,
)
from models.parking_floor import ParkingFloor
from models.parking_spots import ParkingSpot
from models.receipt import Receipt
from models.ticket import Ticket
from models.vehicle import Vehicle
from services.parking_lot import ParkingLot
from services.payment_processor import PaymentProcessor, UPIPaymentProcessor
from strategies.allocation import BestFitStrategy, NearestFirstStrategy
from strategies.decorators import WeekendSurchargeDecorator
from strategies.pricing import DailySlabStrategy, HourlySlabStrategy


class FailedPaymentProcessor(PaymentProcessor):
    def pay(self, amount: float, payment_method: PaymentMethod) -> Receipt:
        return Receipt(
            receipt_id="failed-receipt",
            ticket_id="",
            status=PaymentStatus.FAILED,
            payment_method=payment_method,
            amount=amount,
            date=datetime.now(),
        )


class ParkingLotTest(unittest.TestCase):
    def make_lot(
        self,
        payment_processor: PaymentProcessor | None = None,
    ) -> ParkingLot:
        return ParkingLot(
            name="Test Lot",
            spot_allocation_strategy=NearestFirstStrategy(),
            pricing_strategy=HourlySlabStrategy(),
            payment_processor=payment_processor or UPIPaymentProcessor(),
        )

    @staticmethod
    def add_floor(
        lot: ParkingLot,
        floor_id: int,
        spots: list[ParkingSpot],
    ) -> None:
        floor = ParkingFloor(floor_id)
        for spot in spots:
            floor.add_spot(spot)
        lot.add_floor(floor)

    def test_nearest_strategy_is_global_across_floors(self) -> None:
        lot = self.make_lot()
        self.add_floor(
            lot,
            1,
            [ParkingSpot("A1", SpotType.COMPACT, 1, 20)],
        )
        self.add_floor(
            lot,
            2,
            [ParkingSpot("B1", SpotType.COMPACT, 2, 2)],
        )

        ticket = lot.park_vehicle(Vehicle("CAR-1", VehicleType.CAR))

        self.assertEqual(ticket.spot.spot_id, "B1")

    def test_best_fit_preserves_larger_spots(self) -> None:
        spots = [
            ParkingSpot("L1", SpotType.LARGE, 1, 1),
            ParkingSpot("R1", SpotType.REGULAR, 1, 10),
            ParkingSpot("C1", SpotType.COMPACT, 1, 20),
        ]

        selected = BestFitStrategy().select(
            spots,
            Vehicle("BIKE-1", VehicleType.MOTORCYCLE),
        )

        self.assertEqual(selected.spot_id, "R1")

    def test_duplicate_vehicle_and_no_available_spot_raise(self) -> None:
        lot = self.make_lot()
        self.add_floor(
            lot,
            1,
            [ParkingSpot("A1", SpotType.COMPACT, 1, 1)],
        )
        car = Vehicle("CAR-1", VehicleType.CAR)
        lot.park_vehicle(car)

        with self.assertRaises(ValueError):
            lot.park_vehicle(car)
        with self.assertRaises(RuntimeError):
            lot.park_vehicle(Vehicle("CAR-2", VehicleType.CAR))

    def test_spot_rejects_incompatible_vehicle(self) -> None:
        spot = ParkingSpot("R1", SpotType.REGULAR, 1, 1)
        with self.assertRaises(ValueError):
            spot.assign(Vehicle("TRUCK-1", VehicleType.TRUCK))

    def test_successful_exit_preserves_enum_types(self) -> None:
        lot = self.make_lot()
        self.add_floor(
            lot,
            1,
            [ParkingSpot("A1", SpotType.COMPACT, 1, 1)],
        )
        ticket = lot.park_vehicle(Vehicle("CAR-1", VehicleType.CAR))

        receipt = lot.exit_vehicle(ticket.ticket_id, PaymentMethod.UPI)

        self.assertEqual(ticket.status, TicketStatus.PAID)
        self.assertEqual(receipt.status, PaymentStatus.COMPLETED)
        self.assertEqual(receipt.payment_method, PaymentMethod.UPI)
        self.assertIn("UPI", str(receipt))
        self.assertTrue(ticket.spot.is_available())
        with self.assertRaises(ValueError):
            lot.exit_vehicle(ticket.ticket_id, PaymentMethod.UPI)

    def test_failed_payment_keeps_vehicle_parked(self) -> None:
        lot = self.make_lot(FailedPaymentProcessor())
        self.add_floor(
            lot,
            1,
            [ParkingSpot("A1", SpotType.COMPACT, 1, 1)],
        )
        ticket = lot.park_vehicle(Vehicle("CAR-1", VehicleType.CAR))

        with self.assertRaises(RuntimeError):
            lot.exit_vehicle(ticket.ticket_id, PaymentMethod.UPI)

        self.assertEqual(ticket.status, TicketStatus.ACTIVE)
        self.assertIsNone(ticket.exit_time)
        self.assertFalse(ticket.spot.is_available())

    def test_pricing_strategies_and_weekend_surcharge(self) -> None:
        vehicle = Vehicle("CAR-1", VehicleType.CAR)
        spot = ParkingSpot("A1", SpotType.COMPACT, 1, 1)
        monday = datetime(2026, 7, 27, 9)
        ticket = Ticket("ticket-1", vehicle, spot, monday)
        ticket.exit_time = monday + timedelta(hours=25)

        self.assertEqual(HourlySlabStrategy().compute_fee(ticket), 500.0)
        self.assertEqual(DailySlabStrategy().compute_fee(ticket), 400.0)
        weekday_fee = WeekendSurchargeDecorator(
            HourlySlabStrategy(),
            20,
        ).compute_fee(ticket)
        self.assertEqual(weekday_fee, 500.0)

        saturday = datetime(2026, 8, 1, 9)
        ticket.entry_time = saturday
        ticket.exit_time = saturday + timedelta(minutes=10)
        weekend_fee = WeekendSurchargeDecorator(
            HourlySlabStrategy(),
            20,
        ).compute_fee(ticket)
        self.assertEqual(weekend_fee, 24.0)

    def test_duplicate_floor_and_spot_ids_are_rejected(self) -> None:
        lot = self.make_lot()
        self.add_floor(
            lot,
            1,
            [ParkingSpot("A1", SpotType.COMPACT, 1, 1)],
        )

        duplicate_floor = ParkingFloor(1)
        with self.assertRaises(ValueError):
            lot.add_floor(duplicate_floor)

        another_floor = ParkingFloor(2)
        another_floor.add_spot(ParkingSpot("A1", SpotType.COMPACT, 2, 1))
        with self.assertRaises(ValueError):
            lot.add_floor(another_floor)


if __name__ == "__main__":
    unittest.main()
