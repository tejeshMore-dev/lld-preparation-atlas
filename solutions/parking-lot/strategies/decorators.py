from models.ticket import Ticket
from strategies.pricing import PricingStrategy


class WeekendSurchargeDecorator(PricingStrategy):
    def __init__(
        self,
        base_strategy: PricingStrategy,
        surcharge_percentage: float,
    ) -> None:
        if surcharge_percentage < 0:
            raise ValueError("Surcharge percentage cannot be negative")
        self.base_strategy = base_strategy
        self.surcharge_percentage = surcharge_percentage

    def compute_fee(self, ticket: Ticket) -> float:
        base_fee = self.base_strategy.compute_fee(ticket)
        charged_at = ticket.exit_time or ticket.entry_time
        if charged_at.weekday() < 5:
            return base_fee

        surcharge = base_fee * (self.surcharge_percentage / 100)
        return base_fee + surcharge
