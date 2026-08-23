from models.campaign import Campaign
from models.user import User
from strategies.eligibility_rule import EligibilityRule


class EveryoneEligibilityRule(EligibilityRule):
    def is_eligible(self, user: User, campaign: Campaign) -> bool:
        return True
