from datetime import datetime, timedelta
from decimal import Decimal

from models.enums import DistributionChannel
from models.merchant import Merchant
from models.redemption_context import RedemptionContext
from models.user import User
from services.catalog_service import CatalogService
from services.clock import Clock
from services.coupon_platform_service import CouponPlatformService
from strategies.loyalty_priority_distribution_strategy import LoyaltyPriorityDistributionStrategy
from strategies.percentage_discount import PercentageDiscount
from strategies.segment_eligibility_rule import SegmentEligibilityRule


class DemoClock(Clock):
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current


def build_demo() -> tuple[CouponPlatformService, DemoClock]:
    clock = DemoClock(datetime.now())
    catalog = CatalogService()
    catalog.add_merchant(Merchant("merchant-1", "Design Store", "merchant@example.com"))
    catalog.add_user(
        User("user-1", "Asha", "asha@example.com", frozenset({"premium"}), 300)
    )
    catalog.add_user(
        User("user-2", "Ravi", "ravi@example.com", frozenset({"premium"}), 700)
    )
    service = CouponPlatformService(catalog, clock)
    service.create_campaign(
        "campaign-1",
        "merchant-1",
        "Premium Weekend",
        "SAVE",
        clock.now() - timedelta(minutes=1),
        clock.now() + timedelta(days=7),
        total_supply=2,
        per_user_limit=1,
        minimum_order_value="500",
        discount_strategy=PercentageDiscount("20", "250"),
        eligibility_rule=SegmentEligibilityRule({"premium"}),
        distribution_strategy=LoyaltyPriorityDistributionStrategy(),
        applicable_categories={"fashion"},
    )
    service.activate_campaign("campaign-1")
    return service, clock


def main() -> None:
    service, _ = build_demo()
    coupons = service.distribute_campaign(
        "campaign-1",
        DistributionChannel.APP,
    )
    print("Distributed coupons:", [(coupon.user_id, coupon.code) for coupon in coupons])
    coupon = next(coupon for coupon in coupons if coupon.user_id == "user-1")
    context = RedemptionContext(
        "order-101",
        Decimal("1200"),
        frozenset({"fashion"}),
    )
    quote = service.reserve_coupon(coupon.code, "user-1", context)
    print(
        f"Reserved {quote.coupon_code}: discount Rs. {quote.discount_amount}, "
        f"payable Rs. {quote.payable_amount}"
    )
    redemption = service.redeem_coupon(coupon.code, "user-1", context)
    print(f"Redeemed for order {redemption.order_id}; status {coupon.status.name}")


if __name__ == "__main__":
    main()
