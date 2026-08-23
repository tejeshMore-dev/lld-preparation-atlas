from models.campaign import Campaign
from models.user import User
from strategies.eligibility_rule import EligibilityRule


class SegmentEligibilityRule(EligibilityRule):
    def __init__(self, required_segments: set[str] | frozenset[str], match_any: bool = True) -> None:
        self._required = frozenset(segment.strip().casefold() for segment in required_segments)
        if not self._required:
            raise ValueError("At least one required segment is needed")
        self._match_any = match_any

    def is_eligible(self, user: User, campaign: Campaign) -> bool:
        user_segments = {segment.strip().casefold() for segment in user.segments}
        if self._match_any:
            return bool(user_segments & self._required)
        return self._required.issubset(user_segments)
