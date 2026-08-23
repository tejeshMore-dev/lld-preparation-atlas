from abc import ABC, abstractmethod
from math import ceil

from models.enums import VehicleType
from models.ticket import Ticket


class PricingStrategy(ABC):
    @abstractmethod
    def compute_fee(self, ticket: Ticket) -> float:
        raise NotImplementedError

    @staticmethod
    def _duration_seconds(ticket: Ticket) -> float:
        if ticket.exit_time is None:
            raise ValueError("Ticket exit time is required to compute a fee")
        return max(0.0, (ticket.exit_time - ticket.entry_time).total_seconds())


class HourlySlabStrategy(PricingStrategy):
    HOURLY_RATE = {
        VehicleType.MOTORCYCLE: 10.0,
        VehicleType.CAR: 20.0,
        VehicleType.TRUCK: 30.0,
    }

    def compute_fee(self, ticket: Ticket) -> float:
        billable_hours = max(1, ceil(self._duration_seconds(ticket) / 3600))
        return billable_hours * self.HOURLY_RATE[ticket.vehicle.vehicle_type]


class DailySlabStrategy(PricingStrategy):
    DAILY_RATE = {
        VehicleType.MOTORCYCLE: 100.0,
        VehicleType.CAR: 200.0,
        VehicleType.TRUCK: 300.0,
    }

    def compute_fee(self, ticket: Ticket) -> float:
        billable_days = max(1, ceil(self._duration_seconds(ticket) / 86400))
        return billable_days * self.DAILY_RATE[ticket.vehicle.vehicle_type]
