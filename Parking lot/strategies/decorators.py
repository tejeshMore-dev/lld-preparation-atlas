from strategies.pricing import PricingStrategy

from models.ticket import Ticket

class WeekendSurchargeDecorator(PricingStrategy):

    def __init__(self, base_strategy: PricingStrategy, surcharge_percentage: float):
        self.base_strategy = base_strategy
        self.surcharge_percentage = surcharge_percentage


    def compute_fee(self, ticket: Ticket) -> float:
        base_fee = self.base_strategy.compute_fee(ticket)
        surcharge = base_fee * (self.surcharge_percentage / 100)
        return base_fee + surcharge
