from models.user import User
from strategies.distribution_strategy import DistributionStrategy


class LoyaltyPriorityDistributionStrategy(DistributionStrategy):
    def select_recipients(self, eligible_users: list[User], limit: int) -> list[User]:
        return sorted(
            eligible_users,
            key=lambda user: (-user.loyalty_points, user.user_id),
        )[:limit]
