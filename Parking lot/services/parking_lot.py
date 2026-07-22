import uuid
from datetime import datetime
import threading

from models.enums import TicketStatus, PaymentMethod
from models.parking_floor import ParkingFloor
from models.vehicle import Vehicle
from models.ticket import Ticket

from strategies.allocation import SpotAllocationStrategy
from strategies.pricing import PricingStrategy

from services.payment_processor import PaymentProcessor

class ParkingLot:
    def __init__(self, name: str, spot_allocation_strategy: SpotAllocationStrategy, pricing_strategy: PricingStrategy, payment_processor: PaymentProcessor):
        self.name = name
        self.floors = []
        self.tickets = {}
        self.lock = threading.Lock()
        self.spot_allocation_strategy = spot_allocation_strategy
        self.pricing_strategy = pricing_strategy
        self.payment_processor = payment_processor

    def add_floor(self, floor: ParkingFloor):
        self.floors.append(floor)

    def park_vehicle(self, vehicle: Vehicle) -> bool:
        with self.lock:
            for floor in self.floors:
                spot = floor.find_spot(vehicle, self.spot_allocation_strategy)
                if spot:
                    spot.assign(vehicle)  # Mark the parking spot as occupied
                    ticket = Ticket(
                        ticket_id=str(uuid.uuid4()), 
                        vehicle=vehicle, 
                        spot=spot, 
                        entry_time=datetime.now(),
                        status=TicketStatus.ACTIVE
                        )
                    self.tickets[ticket.ticket_id] = ticket
                    return ticket
            

        return Exception("No available parking spots for the vehicle.")

    def exit_vehicle(self, ticket_id: str, payment_method: PaymentMethod) -> bool:
        ticket = self.tickets.get(ticket_id)

        if not ticket or ticket.status != TicketStatus.ACTIVE:
            return Exception("Invalid ticket.")

        with self.lock:
            ticket.exit_time = datetime.now()

            # Calculate the parking fee based on the pricing strategy
            fee = self.pricing_strategy.compute_fee(ticket)

            receipt = self.payment_processor.pay(fee, payment_method)
            receipt.ticket_id = ticket.ticket_id
            ticket.spot.vacate(ticket.vehicle)  # Mark the parking spot as available
            ticket.status = TicketStatus.PAID.value  # Mark the ticket as closed

            return receipt




        