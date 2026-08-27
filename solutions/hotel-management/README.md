# Hotel Management

Search room availability by date range, create a booking, take payment, check guests in and out, and maintain a folio.

## Scope

Support hotels, room types, rooms, date-range bookings, pricing, payment, check-in/out, charges, and cancellation. Housekeeping and channel distribution are follow-ups.

## Model

| Type | Responsibility |
|---|---|
| Room | physical room and operational state |
| Booking | guest, dates, assigned room, and lifecycle |
| Hotel | rooms and date-range availability |
| RoomQuote | frozen price for a stay |
| Charge | folio entry |
| Payment | settlement result |
| PricingStrategy | nightly calculation |
| BookingService | reserve, pay, check in/out, cancel |

Room operational state—clean, occupied, maintenance—is different from future booking availability.

## Availability rule

Two half-open stays overlap when:

    requested_start < existing_end
    and existing_start < requested_end

Using checkout as an exclusive boundary allows one guest to leave on the day another arrives.

## Critical flow

Search returns candidates and quotes. Booking atomically rechecks the date range and claims a room. Payment confirms the booking. Check-in validates time and room readiness; checkout totals room price plus folio charges and closes the stay.

## Design choices

- Hotel owns inventory lookup; Booking owns transitions.
- Pricing strategy plus decorator handles weekend variation.
- Money is exact.
- PaymentGateway and Clock are injected.
- Quotes separate display-time calculation from booked price.

## Correctness

Availability recheck and booking creation share an atomic boundary. A production database can use range constraints, locks, or versioned inventory depending on the model.

## Run

    python "solutions/hotel-management/main.py"
    python -m unittest discover -s "solutions/hotel-management/tests" -t "solutions/hotel-management" -v

## Follow-ups

Add room-type inventory, overbooking, housekeeping, deposits, no-shows, corporate rates, and multi-room reservations.
