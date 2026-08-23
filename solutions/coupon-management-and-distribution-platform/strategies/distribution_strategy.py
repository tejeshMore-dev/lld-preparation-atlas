from abc import ABC, abstractmethod

from models.user import User


class DistributionStrategy(ABC):
    @abstractmethod
    def select_recipients(self, eligible_users: list[User], limit: int) -> list[User]:
        raise NotImplementedError
