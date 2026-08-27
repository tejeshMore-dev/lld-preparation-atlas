# Movie Ticket Booking

Search shows, hold specific seats, take payment, and confirm a booking without double-selling inventory.

## Scope

Support theatres, screens, movies, shows, seat selection, temporary holds, booking, and payment. Recommendations and content ingestion are outside the core.

## Model

| Type | Responsibility |
|---|---|
| Seat | physical seat metadata |
| Show | show-specific seat inventory and hold rules |
| Booking | selected seats and lifecycle |
| Payment | payment outcome |
| PricingStrategy | quote calculation |
| BookingService | hold, pay, confirm, cancel |
| CatalogService | search theatres, movies, and shows |

The important distinction is physical Seat versus availability for that Seat in one Show.

Invariant: a show seat belongs to at most one active hold or confirmed booking.

## Critical flow

1. Lock the requested show inventory.
2. Reject unavailable seats; otherwise create an expiring hold.
3. Calculate and freeze the quote.
4. Charge using an idempotency reference.
5. Confirm the booking and convert held seats to booked.
6. On payment failure, keep or release the hold according to the stated policy.

An injected Clock makes hold expiry deterministic.

## Design choices

- Show owns show-seat availability.
- Booking owns lifecycle; status is not freely assignable.
- Pricing is a strategy with an optional weekend decorator.
- PaymentGateway isolates the external provider.
- BookingService coordinates the multi-object workflow.

## Correctness

Seat check and hold creation are atomic. Production storage would use conditional updates, versions, or unique active-seat constraints. Payment success followed by confirmation failure requires retry or compensation.

## Run

    python "solutions/movie-ticket-booking/main.py"
    python -m unittest discover -s "solutions/movie-ticket-booking/tests" -t "solutions/movie-ticket-booking" -v

## Follow-ups

Add seat categories, cancellation windows, partial refunds, waitlists, dynamic pricing, and multi-cinema search.
