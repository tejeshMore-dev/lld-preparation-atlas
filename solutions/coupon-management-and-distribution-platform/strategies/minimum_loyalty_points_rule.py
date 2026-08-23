from models.campaign import Campaign
from models.user import User
from strategies.eligibility_rule import EligibilityRule


class MinimumLoyaltyPointsRule(EligibilityRule):
    def __init__(self, minimum_points: int) -> None:
        if minimum_points < 0:
            raise ValueError("Minimum loyalty points cannot be negative")
        self._minimum_points = minimum_points

    def is_eligible(self, user: User, campaign: Campaign) -> bool:
        return user.loyalty_points >= self._minimum_points
