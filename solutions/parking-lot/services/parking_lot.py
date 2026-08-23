import threading
import uuid
from datetime import datetime

from models.enums import PaymentMethod, PaymentStatus, TicketStatus
from models.parking_floor import ParkingFloor
from models.receipt import Receipt
from models.ticket import Ticket
from models.vehicle import Vehicle
from services.payment_processor import PaymentProcessor
from strategies.allocation import SpotAllocationStrategy
from strategies.pricing import PricingStrategy


class ParkingLot:
    def __init__(
        self,
        name: str,
        spot_allocation_strategy: SpotAllocationStrategy,
        pricing_strategy: PricingStrategy,
        payment_processor: PaymentProcessor,
    ) -> None:
        self.name = name
        self.floors: list[ParkingFloor] = []
        self.tickets: dict[str, Ticket] = {}
        self.lock = threading.Lock()
        self.spot_allocation_strategy = spot_allocation_strategy
        self.pricing_strategy = pricing_strategy
        self.payment_processor = payment_processor

    def add_floor(self, floor: ParkingFloor) -> None:
        with self.lock:
            if any(existing.floor_id == floor.floor_id for existing in self.floors):
                raise ValueError(f'Parking floor "{floor.floor_id}" already exists')

            existing_spot_ids = {
                spot.spot_id
                for existing_floor in self.floors
                for spot in existing_floor.spots
            }
            duplicate_spot_ids = existing_spot_ids.intersection(
                spot.spot_id for spot in floor.spots
            )
            if duplicate_spot_ids:
                duplicate = sorted(duplicate_spot_ids)[0]
                raise ValueError(f'Parking spot "{duplicate}" already exists')

            self.floors.append(floor)

    def park_vehicle(self, vehicle: Vehicle) -> Ticket:
        with self.lock:
            already_parked = any(
                ticket.vehicle.license_plate == vehicle.license_plate
                and ticket.status == TicketStatus.ACTIVE
                for ticket in self.tickets.values()
            )
            if already_parked:
                raise ValueError(f"Vehicle {vehicle.license_plate} is already parked")

            all_spots = [spot for floor in self.floors for spot in floor.spots]
            spot = self.spot_allocation_strategy.select(all_spots, vehicle)
            if spot is None:
                raise RuntimeError("No available parking spots for the vehicle")

            spot.assign(vehicle)
            ticket = Ticket(
                ticket_id=str(uuid.uuid4()),
                vehicle=vehicle,
                spot=spot,
                entry_time=datetime.now(),
            )
            self.tickets[ticket.ticket_id] = ticket
            return ticket

    def exit_vehicle(
        self,
        ticket_id: str,
        payment_method: PaymentMethod,
    ) -> Receipt:
        with self.lock:
            ticket = self.tickets.get(ticket_id)
            if ticket is None or ticket.status != TicketStatus.ACTIVE:
                raise ValueError("Invalid or inactive ticket")

            ticket.exit_time = datetime.now()
            fee = self.pricing_strategy.compute_fee(ticket)
            receipt = self.payment_processor.pay(fee, payment_method)
            receipt.ticket_id = ticket.ticket_id

            if receipt.status != PaymentStatus.COMPLETED:
                ticket.exit_time = None
                raise RuntimeError("Payment failed; vehicle remains parked")

            ticket.spot.vacate(ticket.vehicle)
            ticket.status = TicketStatus.PAID
            return receipt
