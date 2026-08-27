# Parking Lot

Allocate a compatible spot, track a parking session, calculate its fee, and release capacity safely.

## Scope

Support cars, motorcycles, and trucks across multiple floors. Issue tickets on entry, accept payment on exit, and allow allocation and pricing policies to vary. Reservations and physical gate hardware are outside the core.

## Model

| Type | Responsibility |
|---|---|
| Vehicle | plate and vehicle type |
| ParkingSpot | compatibility and occupancy |
| ParkingFloor | owns spots and floor availability |
| Ticket | active parking session and lifecycle |
| Receipt | immutable exit result |
| AllocationStrategy | chooses a compatible free spot |
| PricingStrategy | calculates a Money amount |
| ParkingLot | coordinates entry and exit |

Invariant: one spot has at most one active ticket, and one vehicle cannot have two active tickets.

## Critical flow

Entry validates the vehicle, selects a spot, occupies it, then issues a ticket. Those steps share one atomic boundary.

Exit loads the active ticket, calculates the fee from timestamps, charges through the payment boundary, closes the ticket, and releases the spot. A failed payment leaves the ticket active and the spot occupied.

## Design choices

- Spot owns fit and occupancy rules.
- Allocation and pricing are strategies because both are explicit variations.
- Pricing decorators add weekend or surcharge behavior without changing base pricing.
- ParkingLot is an application service, not the owner of spot state.
- Decimal-backed Money avoids binary floating-point errors.

## Correctness

The implementation protects active-ticket and occupancy changes with a lock. A production version would use conditional persistence or a unique active assignment constraint and idempotent exit/payment handling.

## Run

    python "solutions/parking-lot/main.py"
    python -m unittest discover -s "solutions/parking-lot/tests" -t "solutions/parking-lot" -v

Tests cover compatible allocation, full capacity, fee calculation, payment failure, repeated exit, and concurrent entry.

## Follow-ups

Add reservations, electric charging spots, display boards, lost tickets, or several entrances. Each should extend a named policy or boundary rather than add branching to ParkingLot.
