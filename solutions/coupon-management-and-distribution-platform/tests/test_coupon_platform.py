import threading
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from models.enums import CampaignStatus, CouponStatus, DistributionChannel
from models.merchant import Merchant
from models.redemption_context import RedemptionContext
from models.user import User
from services.catalog_service import CatalogService
from services.clock import Clock
from services.coupon_platform_service import CouponPlatformService
from strategies.all_of_eligibility_rule import AllOfEligibilityRule
from strategies.all_users_distribution_strategy import AllUsersDistributionStrategy
from strategies.fixed_amount_discount import FixedAmountDiscount
from strategies.loyalty_priority_distribution_strategy import LoyaltyPriorityDistributionStrategy
from strategies.minimum_loyalty_points_rule import MinimumLoyaltyPointsRule
from strategies.percentage_discount import PercentageDiscount
from strategies.segment_eligibility_rule import SegmentEligibilityRule


class MutableClock(Clock):
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current

    def advance(self, **kwargs) -> None:
        self.current += timedelta(**kwargs)


class CouponPlatformTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = MutableClock(datetime(2030, 1, 1, 10, 0))
        self.catalog = CatalogService()
        self.catalog.add_merchant(Merchant("m1", "Design Store", "merchant@example.com"))
        self.catalog.add_user(
            User("u1", "Asha", "asha@example.com", frozenset({"premium"}), 100)
        )
        self.catalog.add_user(
            User("u2", "Ravi", "ravi@example.com", frozenset({"premium"}), 500)
        )
        self.catalog.add_user(
            User("u3", "Sara", "sara@example.com", frozenset({"regular"}), 1000)
        )
        self.service = CouponPlatformService(
            self.catalog,
            self.clock,
            reservation_duration=timedelta(minutes=10),
        )

    def create_campaign(
        self,
        campaign_id: str = "camp1",
        total_supply: int = 3,
        per_user_limit: int = 1,
        discount_strategy=None,
        eligibility_rule=None,
        distribution_strategy=None,
        minimum_order_value="100",
        categories=None,
    ):
        campaign = self.service.create_campaign(
            campaign_id,
            "m1",
            "New Year Sale",
            "NY",
            datetime(2030, 1, 1, 9, 0),
            datetime(2030, 1, 10, 0, 0),
            total_supply,
            per_user_limit,
            minimum_order_value,
            discount_strategy or PercentageDiscount("20", "50"),
            eligibility_rule,
            distribution_strategy,
            categories,
        )
        self.service.activate_campaign(campaign_id)
        return campaign

    def context(self, order_id="order1", amount="400", categories=None):
        return RedemptionContext(
            order_id,
            Decimal(amount),
            frozenset(categories or {"fashion"}),
        )

    def test_campaign_validation_and_activation(self) -> None:
        with self.assertRaisesRegex(ValueError, "after start"):
            self.service.create_campaign(
                "bad", "m1", "Bad", "BAD", self.clock.now(), self.clock.now(),
                1, 1, "0", FixedAmountDiscount("10")
            )
        campaign = self.create_campaign()
        self.assertIs(CampaignStatus.ACTIVE, campaign.status)

    def test_distribution_filters_eligibility_and_generates_unique_codes(self) -> None:
        campaign = self.create_campaign(
            eligibility_rule=SegmentEligibilityRule({"premium"}),
            distribution_strategy=AllUsersDistributionStrategy(),
        )
        coupons = self.service.distribute_campaign(
            campaign.campaign_id,
            DistributionChannel.EMAIL,
        )
        self.assertEqual({"u1", "u2"}, {coupon.user_id for coupon in coupons})
        self.assertEqual(2, len({coupon.code for coupon in coupons}))
        self.assertTrue(all(coupon.code.startswith("NY-") for coupon in coupons))
        self.assertEqual(2, campaign.issued_count)

    def test_loyalty_priority_distribution(self) -> None:
        campaign = self.create_campaign(
            distribution_strategy=LoyaltyPriorityDistributionStrategy()
        )
        coupon = self.service.distribute_campaign(
            campaign.campaign_id,
            DistributionChannel.APP,
            limit=1,
        )[0]
        self.assertEqual("u3", coupon.user_id)

    def test_composable_all_of_eligibility(self) -> None:
        rule = AllOfEligibilityRule(
            SegmentEligibilityRule({"premium"}),
            MinimumLoyaltyPointsRule(200),
        )
        campaign = self.create_campaign(eligibility_rule=rule)
        coupons = self.service.distribute_campaign(campaign.campaign_id, DistributionChannel.SMS)
        self.assertEqual(["u2"], [coupon.user_id for coupon in coupons])

    def test_claim_enforces_user_and_supply_limits(self) -> None:
        campaign = self.create_campaign(total_supply=2, per_user_limit=1)
        self.service.claim_coupon(campaign.campaign_id, "u1")
        with self.assertRaisesRegex(ValueError, "campaign coupon limit"):
            self.service.claim_coupon(campaign.campaign_id, "u1")
        self.service.claim_coupon(campaign.campaign_id, "u2")
        with self.assertRaisesRegex(ValueError, "exhausted"):
            self.service.claim_coupon(campaign.campaign_id, "u3")

    def test_concurrent_claims_cannot_oversubscribe_supply(self) -> None:
        campaign = self.create_campaign(total_supply=1)
        barrier = threading.Barrier(2)
        successes = []
        failures = []

        def claim(user_id: str) -> None:
            barrier.wait()
            try:
                successes.append(self.service.claim_coupon(campaign.campaign_id, user_id))
            except ValueError as error:
                failures.append(str(error))

        threads = [
            threading.Thread(target=claim, args=("u1",)),
            threading.Thread(target=claim, args=("u2",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(1, len(successes))
        self.assertEqual(1, len(failures))
        self.assertEqual(1, campaign.issued_count)

    def test_percentage_discount_and_cap(self) -> None:
        campaign = self.create_campaign()
        coupon = self.service.claim_coupon(campaign.campaign_id, "u1")
        quote = self.service.reserve_coupon(coupon.code, "u1", self.context())
        self.assertEqual(Decimal("50.00"), quote.discount_amount)
        self.assertEqual(Decimal("350.00"), quote.payable_amount)

    def test_fixed_discount_never_makes_payable_negative(self) -> None:
        campaign = self.create_campaign(
            discount_strategy=FixedAmountDiscount("150"),
            minimum_order_value="0",
        )
        coupon = self.service.claim_coupon(campaign.campaign_id, "u1")
        quote = self.service.reserve_coupon(
            coupon.code, "u1", self.context(amount="100")
        )
        self.assertEqual(Decimal("100.00"), quote.discount_amount)
        self.assertEqual(Decimal("0.00"), quote.payable_amount)

    def test_minimum_order_and_category_are_validated(self) -> None:
        campaign = self.create_campaign(categories={"fashion"})
        coupon = self.service.claim_coupon(campaign.campaign_id, "u1")
        with self.assertRaisesRegex(ValueError, "minimum"):
            self.service.reserve_coupon(
                coupon.code, "u1", self.context(amount="99")
            )
        with self.assertRaisesRegex(ValueError, "categories"):
            self.service.reserve_coupon(
                coupon.code, "u1", self.context(categories={"grocery"})
            )

    def test_coupon_is_owned_by_issued_user(self) -> None:
        campaign = self.create_campaign()
        coupon = self.service.claim_coupon(campaign.campaign_id, "u1")
        with self.assertRaisesRegex(ValueError, "belong"):
            self.service.reserve_coupon(coupon.code, "u2", self.context())

    def test_reservation_blocks_another_order(self) -> None:
        campaign = self.create_campaign()
        coupon = self.service.claim_coupon(campaign.campaign_id, "u1")
        self.service.reserve_coupon(coupon.code, "u1", self.context("order1"))
        with self.assertRaisesRegex(ValueError, "another order"):
            self.service.reserve_coupon(coupon.code, "u1", self.context("order2"))

    def test_expired_reservation_is_released_for_retry(self) -> None:
        campaign = self.create_campaign()
        coupon = self.service.claim_coupon(campaign.campaign_id, "u1")
        self.service.reserve_coupon(coupon.code, "u1", self.context("order1"))
        self.clock.advance(minutes=10)
        quote = self.service.reserve_coupon(coupon.code, "u1", self.context("order2"))
        self.assertEqual("order2", quote.order_id)
        self.assertIs(CouponStatus.RESERVED, coupon.status)

    def test_manual_release_makes_coupon_available(self) -> None:
        campaign = self.create_campaign()
        coupon = self.service.claim_coupon(campaign.campaign_id, "u1")
        self.service.reserve_coupon(coupon.code, "u1", self.context())
        self.service.release_coupon(coupon.code, "u1", "order1")
        self.assertIs(CouponStatus.AVAILABLE, coupon.status)
        self.assertIsNone(coupon.reserved_order_id)

    def test_redemption_requires_reservation_and_is_idempotent(self) -> None:
        campaign = self.create_campaign()
        coupon = self.service.claim_coupon(campaign.campaign_id, "u1")
        context = self.context()
        with self.assertRaisesRegex(ValueError, "must be reserved"):
            self.service.redeem_coupon(coupon.code, "u1", context)
        self.service.reserve_coupon(coupon.code, "u1", context)
        first = self.service.redeem_coupon(coupon.code, "u1", context)
        second = self.service.redeem_coupon(coupon.code, "u1", context)
        self.assertIs(first, second)
        self.assertIs(CouponStatus.REDEEMED, coupon.status)
        self.assertEqual(1, campaign.redeemed_count)

    def test_paused_campaign_blocks_usage_then_can_resume(self) -> None:
        campaign = self.create_campaign()
        coupon = self.service.claim_coupon(campaign.campaign_id, "u1")
        self.service.pause_campaign(campaign.campaign_id)
        with self.assertRaisesRegex(ValueError, "not active"):
            self.service.reserve_coupon(coupon.code, "u1", self.context())
        self.service.resume_campaign(campaign.campaign_id)
        quote = self.service.reserve_coupon(coupon.code, "u1", self.context())
        self.assertEqual("order1", quote.order_id)

    def test_campaign_end_expires_unredeemed_coupons(self) -> None:
        campaign = self.create_campaign()
        coupon = self.service.claim_coupon(campaign.campaign_id, "u1")
        self.service.end_campaign(campaign.campaign_id)
        self.assertIs(CampaignStatus.ENDED, campaign.status)
        self.assertIs(CouponStatus.EXPIRED, coupon.status)

    def test_coupon_revocation(self) -> None:
        campaign = self.create_campaign()
        coupon = self.service.claim_coupon(campaign.campaign_id, "u1")
        self.service.revoke_coupon(coupon.code)
        self.assertIs(CouponStatus.REVOKED, coupon.status)
        with self.assertRaisesRegex(ValueError, "REVOKED"):
            self.service.reserve_coupon(coupon.code, "u1", self.context())

    def test_distribution_and_redemption_audit_history(self) -> None:
        campaign = self.create_campaign()
        coupon = self.service.claim_coupon(campaign.campaign_id, "u1")
        context = self.context()
        self.service.reserve_coupon(coupon.code, "u1", context)
        redemption = self.service.redeem_coupon(coupon.code, "u1", context)
        self.assertEqual([coupon], self.service.get_user_coupons("u1"))
        self.assertEqual([redemption], self.service.get_user_redemptions("u1"))
        record = next(iter(self.service.distributions.values()))
        self.assertIs(DistributionChannel.CLAIM, record.channel)


if __name__ == "__main__":
    unittest.main()
