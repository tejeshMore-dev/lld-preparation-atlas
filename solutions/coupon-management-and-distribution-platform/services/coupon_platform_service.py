from datetime import datetime, timedelta
from decimal import Decimal
from threading import RLock
from uuid import uuid4

from models.campaign import Campaign
from models.coupon import Coupon
from models.coupon_quote import CouponQuote
from models.distribution_record import DistributionRecord
from models.enums import CampaignStatus, CouponStatus, DistributionChannel
from models.money import MoneyInput, to_money
from models.redemption import Redemption
from models.redemption_context import RedemptionContext
from services.catalog_service import CatalogService
from services.clock import Clock, SystemClock
from strategies.all_users_distribution_strategy import AllUsersDistributionStrategy
from strategies.discount_strategy import DiscountStrategy
from strategies.distribution_strategy import DistributionStrategy
from strategies.eligibility_rule import EligibilityRule
from strategies.everyone_eligibility_rule import EveryoneEligibilityRule


class CouponPlatformService:
    """Coordinates campaign lifecycle, issuance, reservation, and redemption."""

    def __init__(
        self,
        catalog: CatalogService,
        clock: Clock | None = None,
        reservation_duration: timedelta = timedelta(minutes=10),
    ) -> None:
        if reservation_duration <= timedelta(0):
            raise ValueError("Reservation duration must be positive")
        self._catalog = catalog
        self._clock = clock or SystemClock()
        self._reservation_duration = reservation_duration
        self._lock = RLock()
        self.campaigns: dict[str, Campaign] = {}
        self.coupons: dict[str, Coupon] = {}
        self.coupons_by_code: dict[str, Coupon] = {}
        self.distributions: dict[str, DistributionRecord] = {}
        self.redemptions: dict[str, Redemption] = {}
        self._discount_strategies: dict[str, DiscountStrategy] = {}
        self._eligibility_rules: dict[str, EligibilityRule] = {}
        self._distribution_strategies: dict[str, DistributionStrategy] = {}

    def create_campaign(
        self,
        campaign_id: str,
        merchant_id: str,
        name: str,
        code_prefix: str,
        start_time: datetime,
        end_time: datetime,
        total_supply: int,
        per_user_limit: int,
        minimum_order_value: MoneyInput,
        discount_strategy: DiscountStrategy,
        eligibility_rule: EligibilityRule | None = None,
        distribution_strategy: DistributionStrategy | None = None,
        applicable_categories: set[str] | frozenset[str] | None = None,
    ) -> Campaign:
        with self._lock:
            if campaign_id in self.campaigns:
                raise ValueError(f"Campaign '{campaign_id}' already exists")
            self._catalog.get_merchant(merchant_id)
            if end_time <= start_time:
                raise ValueError("Campaign end time must be after start time")
            if total_supply <= 0 or per_user_limit <= 0:
                raise ValueError("Supply and per-user limit must be positive")
            if per_user_limit > total_supply:
                raise ValueError("Per-user limit cannot exceed total supply")
            prefix = code_prefix.strip().upper()
            if not prefix or not prefix.isalnum():
                raise ValueError("Code prefix must contain only letters and numbers")
            minimum = to_money(minimum_order_value)
            if minimum < 0:
                raise ValueError("Minimum order value cannot be negative")
            categories = frozenset(
                category.strip().casefold()
                for category in (applicable_categories or set())
                if category.strip()
            )
            campaign = Campaign(
                campaign_id=campaign_id,
                merchant_id=merchant_id,
                name=name,
                code_prefix=prefix,
                start_time=start_time,
                end_time=end_time,
                total_supply=total_supply,
                per_user_limit=per_user_limit,
                minimum_order_value=minimum,
                applicable_categories=categories,
            )
            self.campaigns[campaign_id] = campaign
            self._discount_strategies[campaign_id] = discount_strategy
            self._eligibility_rules[campaign_id] = eligibility_rule or EveryoneEligibilityRule()
            self._distribution_strategies[campaign_id] = (
                distribution_strategy or AllUsersDistributionStrategy()
            )
            return campaign

    def activate_campaign(self, campaign_id: str) -> Campaign:
        with self._lock:
            campaign = self.get_campaign(campaign_id)
            self._sync_campaign(campaign, self._clock.now())
            if campaign.status is CampaignStatus.ACTIVE:
                return campaign
            if campaign.status is CampaignStatus.ENDED:
                raise ValueError("An ended campaign cannot be activated")
            campaign.status = CampaignStatus.ACTIVE
            return campaign

    def pause_campaign(self, campaign_id: str) -> Campaign:
        with self._lock:
            campaign = self.get_campaign(campaign_id)
            self._sync_campaign(campaign, self._clock.now())
            if campaign.status is CampaignStatus.PAUSED:
                return campaign
            if campaign.status is not CampaignStatus.ACTIVE:
                raise ValueError("Only an active campaign can be paused")
            campaign.status = CampaignStatus.PAUSED
            return campaign

    def resume_campaign(self, campaign_id: str) -> Campaign:
        with self._lock:
            campaign = self.get_campaign(campaign_id)
            self._sync_campaign(campaign, self._clock.now())
            if campaign.status is CampaignStatus.ACTIVE:
                return campaign
            if campaign.status is not CampaignStatus.PAUSED:
                raise ValueError("Only a paused campaign can be resumed")
            campaign.status = CampaignStatus.ACTIVE
            return campaign

    def end_campaign(self, campaign_id: str) -> Campaign:
        with self._lock:
            campaign = self.get_campaign(campaign_id)
            if campaign.status is CampaignStatus.ENDED:
                return campaign
            campaign.status = CampaignStatus.ENDED
            self._expire_campaign_coupons(campaign)
            return campaign

    def distribute_campaign(
        self,
        campaign_id: str,
        channel: DistributionChannel,
        limit: int | None = None,
    ) -> list[Coupon]:
        with self._lock:
            campaign = self.get_campaign(campaign_id)
            now = self._clock.now()
            self._ensure_live(campaign, now)
            remaining = campaign.total_supply - campaign.issued_count
            if remaining <= 0:
                return []
            if limit is not None and limit <= 0:
                raise ValueError("Distribution limit must be positive")
            requested_limit = remaining if limit is None else limit
            issue_limit = min(remaining, requested_limit)
            if issue_limit <= 0:
                return []

            eligible_users = [
                user
                for user in self._catalog.users.values()
                if self._eligibility_rules[campaign_id].is_eligible(user, campaign)
                and self._issued_to_user(campaign_id, user.user_id)
                < campaign.per_user_limit
            ]
            selected = self._distribution_strategies[campaign_id].select_recipients(
                eligible_users,
                issue_limit,
            )
            eligible_by_id = {user.user_id: user for user in eligible_users}
            issued = []
            seen = set()
            for selected_user in selected:
                if len(issued) >= issue_limit:
                    break
                if selected_user.user_id in seen or selected_user.user_id not in eligible_by_id:
                    continue
                seen.add(selected_user.user_id)
                issued.append(self._issue_coupon(campaign, selected_user.user_id, channel, now))
            return issued

    def claim_coupon(self, campaign_id: str, user_id: str) -> Coupon:
        with self._lock:
            campaign = self.get_campaign(campaign_id)
            user = self._catalog.get_user(user_id)
            now = self._clock.now()
            self._ensure_live(campaign, now)
            if campaign.issued_count >= campaign.total_supply:
                raise ValueError("Campaign coupon supply is exhausted")
            if self._issued_to_user(campaign_id, user_id) >= campaign.per_user_limit:
                raise ValueError("User has reached the campaign coupon limit")
            if not self._eligibility_rules[campaign_id].is_eligible(user, campaign):
                raise ValueError("User is not eligible for this campaign")
            return self._issue_coupon(
                campaign,
                user_id,
                DistributionChannel.CLAIM,
                now,
            )

    def reserve_coupon(
        self,
        code: str,
        user_id: str,
        context: RedemptionContext,
    ) -> CouponQuote:
        with self._lock:
            coupon = self.get_coupon_by_code(code)
            campaign = self.get_campaign(coupon.campaign_id)
            now = self._clock.now()
            self._sync_campaign(campaign, now)
            self._refresh_coupon(coupon, campaign, now)
            self._validate_redemption(coupon, campaign, user_id, context, now)
            if coupon.status is CouponStatus.RESERVED:
                if coupon.reserved_order_id != context.order_id:
                    raise ValueError("Coupon is reserved for another order")
                return self._quote(coupon, campaign, context)
            if coupon.status is not CouponStatus.AVAILABLE:
                raise ValueError(f"Coupon cannot be reserved in {coupon.status.name} state")
            coupon.status = CouponStatus.RESERVED
            coupon.reserved_order_id = context.order_id
            coupon.reserved_at = now
            coupon.reserved_until = min(now + self._reservation_duration, campaign.end_time)
            return self._quote(coupon, campaign, context)

    def release_coupon(self, code: str, user_id: str, order_id: str) -> Coupon:
        with self._lock:
            coupon = self.get_coupon_by_code(code)
            campaign = self.get_campaign(coupon.campaign_id)
            now = self._clock.now()
            self._sync_campaign(campaign, now)
            self._refresh_coupon(coupon, campaign, now)
            if coupon.user_id != user_id:
                raise ValueError("Coupon does not belong to this user")
            if coupon.status is CouponStatus.AVAILABLE:
                return coupon
            if coupon.status is not CouponStatus.RESERVED:
                raise ValueError(f"Coupon cannot be released in {coupon.status.name} state")
            if coupon.reserved_order_id != order_id:
                raise ValueError("Coupon is reserved for another order")
            self._clear_reservation(coupon)
            coupon.status = CouponStatus.AVAILABLE
            return coupon

    def redeem_coupon(
        self,
        code: str,
        user_id: str,
        context: RedemptionContext,
    ) -> Redemption:
        with self._lock:
            coupon = self.get_coupon_by_code(code)
            if coupon.status is CouponStatus.REDEEMED:
                if coupon.redeemed_order_id != context.order_id or coupon.user_id != user_id:
                    raise ValueError("Coupon has already been redeemed")
                return self._redemption_for_coupon(coupon.coupon_id)
            campaign = self.get_campaign(coupon.campaign_id)
            now = self._clock.now()
            self._sync_campaign(campaign, now)
            self._refresh_coupon(coupon, campaign, now)
            self._validate_redemption(coupon, campaign, user_id, context, now)
            if coupon.status is not CouponStatus.RESERVED:
                raise ValueError("Coupon must be reserved before redemption")
            if coupon.reserved_order_id != context.order_id:
                raise ValueError("Coupon is reserved for another order")
            quote = self._quote(coupon, campaign, context)
            coupon.status = CouponStatus.REDEEMED
            coupon.redeemed_order_id = context.order_id
            coupon.redeemed_at = now
            coupon.reserved_order_id = None
            coupon.reserved_at = None
            coupon.reserved_until = None
            campaign.redeemed_count += 1
            redemption = Redemption(
                redemption_id=str(uuid4()),
                coupon_id=coupon.coupon_id,
                campaign_id=campaign.campaign_id,
                user_id=user_id,
                order_id=context.order_id,
                order_amount=quote.order_amount,
                discount_amount=quote.discount_amount,
                payable_amount=quote.payable_amount,
                redeemed_at=now,
            )
            self.redemptions[redemption.redemption_id] = redemption
            return redemption

    def revoke_coupon(self, code: str) -> Coupon:
        with self._lock:
            coupon = self.get_coupon_by_code(code)
            if coupon.status is CouponStatus.REVOKED:
                return coupon
            if coupon.status is CouponStatus.REDEEMED:
                raise ValueError("A redeemed coupon cannot be revoked")
            coupon.status = CouponStatus.REVOKED
            coupon.revoked_at = self._clock.now()
            self._clear_reservation(coupon)
            return coupon

    def expire_stale_coupons(self) -> list[Coupon]:
        with self._lock:
            now = self._clock.now()
            previous_statuses = {
                coupon.coupon_id: coupon.status for coupon in self.coupons.values()
            }
            for campaign in self.campaigns.values():
                self._sync_campaign(campaign, now)
            for coupon in self.coupons.values():
                campaign = self.campaigns[coupon.campaign_id]
                self._refresh_coupon(coupon, campaign, now)
            return [
                coupon
                for coupon in self.coupons.values()
                if previous_statuses[coupon.coupon_id] is not coupon.status
            ]

    def get_campaign(self, campaign_id: str) -> Campaign:
        try:
            return self.campaigns[campaign_id]
        except KeyError as error:
            raise ValueError(f"Campaign '{campaign_id}' does not exist") from error

    def get_coupon_by_code(self, code: str) -> Coupon:
        normalized = code.strip().upper()
        try:
            return self.coupons_by_code[normalized]
        except KeyError as error:
            raise ValueError(f"Coupon code '{normalized}' does not exist") from error

    def get_user_coupons(self, user_id: str) -> list[Coupon]:
        with self._lock:
            self._catalog.get_user(user_id)
            now = self._clock.now()
            result = []
            for coupon in self.coupons.values():
                if coupon.user_id != user_id:
                    continue
                campaign = self.campaigns[coupon.campaign_id]
                self._sync_campaign(campaign, now)
                self._refresh_coupon(coupon, campaign, now)
                result.append(coupon)
            return sorted(result, key=lambda coupon: coupon.issued_at, reverse=True)

    def get_campaign_coupons(self, campaign_id: str) -> list[Coupon]:
        self.get_campaign(campaign_id)
        return [
            coupon
            for coupon in self.coupons.values()
            if coupon.campaign_id == campaign_id
        ]

    def get_user_redemptions(self, user_id: str) -> list[Redemption]:
        self._catalog.get_user(user_id)
        return sorted(
            (
                redemption
                for redemption in self.redemptions.values()
                if redemption.user_id == user_id
            ),
            key=lambda redemption: redemption.redeemed_at,
            reverse=True,
        )

    def _issue_coupon(
        self,
        campaign: Campaign,
        user_id: str,
        channel: DistributionChannel,
        now: datetime,
    ) -> Coupon:
        code = self._generate_code(campaign.code_prefix)
        coupon = Coupon(
            coupon_id=str(uuid4()),
            code=code,
            campaign_id=campaign.campaign_id,
            user_id=user_id,
            issued_at=now,
        )
        self.coupons[coupon.coupon_id] = coupon
        self.coupons_by_code[code] = coupon
        campaign.issued_count += 1
        record = DistributionRecord(
            distribution_id=str(uuid4()),
            campaign_id=campaign.campaign_id,
            coupon_id=coupon.coupon_id,
            user_id=user_id,
            channel=channel,
            distributed_at=now,
        )
        self.distributions[record.distribution_id] = record
        return coupon

    def _validate_redemption(
        self,
        coupon: Coupon,
        campaign: Campaign,
        user_id: str,
        context: RedemptionContext,
        now: datetime,
    ) -> None:
        user = self._catalog.get_user(user_id)
        self._ensure_live(campaign, now)
        if coupon.user_id != user_id:
            raise ValueError("Coupon does not belong to this user")
        if not context.order_id.strip():
            raise ValueError("Order ID is required")
        order_amount = to_money(context.order_amount)
        if order_amount <= 0:
            raise ValueError("Order amount must be positive")
        if order_amount < campaign.minimum_order_value:
            raise ValueError("Order does not meet the campaign minimum value")
        if not self._eligibility_rules[campaign.campaign_id].is_eligible(user, campaign):
            raise ValueError("User is no longer eligible for this campaign")
        order_categories = {category.strip().casefold() for category in context.categories}
        if campaign.applicable_categories and not (
            campaign.applicable_categories & order_categories
        ):
            raise ValueError("Coupon is not applicable to the order categories")

    def _quote(
        self,
        coupon: Coupon,
        campaign: Campaign,
        context: RedemptionContext,
    ) -> CouponQuote:
        if coupon.reserved_until is None:
            raise RuntimeError("Reserved coupon has no reservation deadline")
        order_amount = to_money(context.order_amount)
        discount = self._discount_strategies[campaign.campaign_id].calculate_discount(
            order_amount
        )
        return CouponQuote(
            coupon_code=coupon.code,
            order_id=context.order_id,
            order_amount=order_amount,
            discount_amount=discount,
            payable_amount=to_money(order_amount - discount),
            reserved_until=coupon.reserved_until,
        )

    def _ensure_live(self, campaign: Campaign, now: datetime) -> None:
        self._sync_campaign(campaign, now)
        if campaign.status is not CampaignStatus.ACTIVE:
            raise ValueError(f"Campaign is not active ({campaign.status.name})")
        if now < campaign.start_time:
            raise ValueError("Campaign has not started")
        if now >= campaign.end_time:
            raise ValueError("Campaign has ended")

    def _sync_campaign(self, campaign: Campaign, now: datetime) -> None:
        if now >= campaign.end_time and campaign.status is not CampaignStatus.ENDED:
            campaign.status = CampaignStatus.ENDED
            self._expire_campaign_coupons(campaign)

    def _refresh_coupon(self, coupon: Coupon, campaign: Campaign, now: datetime) -> None:
        if coupon.status is CouponStatus.RESERVED and coupon.reserved_until is not None:
            if coupon.reserved_until <= now:
                self._clear_reservation(coupon)
                coupon.status = CouponStatus.AVAILABLE
        if (
            campaign.status is CampaignStatus.ENDED
            and coupon.status in {CouponStatus.AVAILABLE, CouponStatus.RESERVED}
        ):
            self._clear_reservation(coupon)
            coupon.status = CouponStatus.EXPIRED

    def _expire_campaign_coupons(self, campaign: Campaign) -> None:
        for coupon in self.coupons.values():
            if (
                coupon.campaign_id == campaign.campaign_id
                and coupon.status in {CouponStatus.AVAILABLE, CouponStatus.RESERVED}
            ):
                self._clear_reservation(coupon)
                coupon.status = CouponStatus.EXPIRED

    def _issued_to_user(self, campaign_id: str, user_id: str) -> int:
        return sum(
            1
            for coupon in self.coupons.values()
            if coupon.campaign_id == campaign_id and coupon.user_id == user_id
        )

    def _generate_code(self, prefix: str) -> str:
        while True:
            code = f"{prefix}-{uuid4().hex[:10].upper()}"
            if code not in self.coupons_by_code:
                return code

    def _redemption_for_coupon(self, coupon_id: str) -> Redemption:
        for redemption in self.redemptions.values():
            if redemption.coupon_id == coupon_id:
                return redemption
        raise RuntimeError("Redeemed coupon has no redemption record")

    @staticmethod
    def _clear_reservation(coupon: Coupon) -> None:
        coupon.reserved_order_id = None
        coupon.reserved_at = None
        coupon.reserved_until = None
