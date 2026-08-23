from models.delivery_partner import DeliveryPartner
from models.location import Location
from strategies.distance_strategy import DistanceStrategy
from strategies.matching_strategy import MatchingStrategy


class NearestPartnerStrategy(MatchingStrategy):
    def __init__(self, distance_strategy: DistanceStrategy) -> None:
        self._distance_strategy = distance_strategy

    def select_partner(
        self,
        partners: list[DeliveryPartner],
        restaurant_location: Location,
    ) -> DeliveryPartner | None:
        if not partners:
            return None
        return min(
            partners,
            key=lambda partner: (
                self._distance_strategy.calculate_km(
                    partner.location,
                    restaurant_location,
                ),
                partner.partner_id,
            ),
        )
