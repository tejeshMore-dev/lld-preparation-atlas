from abc import ABC, abstractmethod
from datetime import time
from math import ceil

from models.ticket import Ticket
from models.enums import VehicleType

class PricingStrategy(ABC):

    @abstractmethod
    def compute_fee(self, ticket: Ticket) -> float:
        pass


class HourlySlabStratergy(PricingStrategy):

    HOURLY_RATE = {
        VehicleType.MOTORCYCLE: 10,
        VehicleType.CAR: 20,
        VehicleType.TRUCK: 30
    }

    def compute_fee(self, ticket: Ticket):
        entry_time = ticket.entry_time
        exit_time = ticket.exit_time

        duration = (exit_time - entry_time)

        return ceil(duration.total_seconds() / 3600) * self.HOURLY_RATE[ticket.vehicle.vehicle_type]

class DailySlabStratergy(PricingStrategy):

    def compute_fee(self, ticket: Ticket):
        pass    
        
        