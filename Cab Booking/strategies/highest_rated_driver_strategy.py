from models.driver import Driver
from models.location import Location
from strategies.distance_strategy import DistanceStrategy
from strategies.matching_strategy import MatchingStrategy


class HighestRatedDriverStrategy(MatchingStrategy):
    """Prefers rating, then uses pickup distance as a tie-breaker."""

    def __init__(self, distance_strategy: DistanceStrategy) -> None:
        self._distance_strategy = distance_strategy

    def select_driver(self, drivers: list[Driver], pickup: Location) -> Driver | None:
        if not drivers:
            return None
        return min(
            drivers,
            key=lambda driver: (
                -driver.average_rating,
                self._distance_strategy.calculate_km(driver.location, pickup),
                driver.driver_id,
            ),
        )
