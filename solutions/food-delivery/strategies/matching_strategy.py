from abc import ABC, abstractmethod

from models.delivery_partner import DeliveryPartner
from models.location import Location


class MatchingStrategy(ABC):
    @abstractmethod
    def select_partner(
        self,
        partners: list[DeliveryPartner],
        restaurant_location: Location,
    ) -> DeliveryPartner | None:
        raise NotImplementedError
