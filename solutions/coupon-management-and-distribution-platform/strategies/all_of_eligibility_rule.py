from models.campaign import Campaign
from models.user import User
from strategies.eligibility_rule import EligibilityRule


class AllOfEligibilityRule(EligibilityRule):
    def __init__(self, *rules: EligibilityRule) -> None:
        if not rules:
            raise ValueError("At least one eligibility rule is required")
        self._rules = rules

    def is_eligible(self, user: User, campaign: Campaign) -> bool:
        return all(rule.is_eligible(user, campaign) for rule in self._rules)
