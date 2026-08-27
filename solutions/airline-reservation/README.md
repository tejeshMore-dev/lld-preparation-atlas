# Airline Reservation

Search scheduled flights, quote a seat, book it, take payment, check in, and issue a boarding pass.

## Scope

Support airlines, airports, aircraft, flights, per-flight seats, passengers, bookings, payments, check-in, and boarding. Crew, route planning, and loyalty programs are outside the core.

## Model

| Type | Responsibility |
|---|---|
| Aircraft | reusable physical seat layout |
| Flight | schedule and seat inventory for one departure |
| FlightSeat | bookable seat state for one flight |
| Booking | passenger, quote, and lifecycle |
| Payment | charge result |
| BoardingPass | successful check-in result |
| ReservationService | booking, cancellation, check-in |
| PricingStrategy | fare calculation |

The central distinction is aircraft Seat versus FlightSeat. Availability belongs to the scheduled flight, not the aircraft definition.

## Critical flow

Quote reads current seat and pricing data. Booking atomically claims the FlightSeat, creates a pending booking, charges through PaymentGateway, then confirms. Failure releases the seat. Check-in validates booking status and the allowed time window before issuing one boarding pass.

## Design choices

- Flight owns per-departure inventory.
- Booking owns booking transitions.
- Pricing strategy plus decorator handles fare variation.
- Clock makes time-window rules testable.
- PaymentGateway keeps provider details outside the domain.

## Correctness

Seat claim and active booking creation must be atomic. Production payment uses idempotency keys; a successful charge followed by save failure needs retryable confirmation or compensation.

## Run

    python "solutions/airline-reservation/main.py"
    python -m unittest discover -s "solutions/airline-reservation/tests" -t "solutions/airline-reservation" -v

## Follow-ups

Add connecting itineraries, fare classes, seat holds, baggage, upgrades, waitlists, and schedule disruption handling.
