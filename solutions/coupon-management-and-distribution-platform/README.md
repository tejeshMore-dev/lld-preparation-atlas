# Coupon Management and Distribution Platform

Create campaigns, distribute coupon codes, validate eligibility, reserve supply, and redeem discounts exactly once.

## Scope

Support campaigns, fixed and percentage discounts, user eligibility, targeted distribution, claims, checkout reservation, expiry, release, and redemption. Marketing analytics and checkout ownership are external.

## Model

| Type | Responsibility |
|---|---|
| Campaign | budget, validity, supply, and status |
| Coupon | code, ownership, and lifecycle |
| EligibilityRule | decides whether a user/context qualifies |
| DiscountStrategy | calculates exact discount |
| DistributionStrategy | selects recipients |
| Redemption | immutable successful use |
| CouponPlatformService | coordinates claim, reserve, release, redeem |

Invariant: issued supply never exceeds the campaign limit; a coupon is redeemed at most once; per-user limits are preserved.

## Checkout flow

1. Load coupon, campaign, user, and cart context.
2. Validate dates, status, ownership, eligibility, and applicability.
3. Calculate a quote without mutating supply.
4. Atomically reserve the coupon for the checkout.
5. Redeem after order success or release/expire the reservation after failure.

Reservation separates validation from final redemption and prevents simultaneous checkouts from using one coupon.

## Design choices

- Eligibility rules compose with all-of logic.
- Discount and distribution are independent strategies.
- Money uses Decimal and caps discount at eligible subtotal.
- Coupon owns its lifecycle; Campaign owns campaign supply.
- Clock makes expiry deterministic.

## Correctness

Supply counters, per-user counts, and coupon state must update together. Production storage should use unique code and redemption constraints plus versions or conditional updates. Release and redeem commands should be idempotent.

## Run

    python "solutions/coupon-management-and-distribution-platform/main.py"
    python -m unittest discover -s "solutions/coupon-management-and-distribution-platform/tests" -t "solutions/coupon-management-and-distribution-platform" -v

## Follow-ups

Add campaign budgets, stackability, referral coupons, fraud scoring, category exclusions, and event-based audit/reporting.
