from abc import ABC, abstractmethod

from models.campaign import Campaign
from models.user import User


class EligibilityRule(ABC):
    @abstractmethod
    def is_eligible(self, user: User, campaign: Campaign) -> bool:
        raise NotImplementedError
