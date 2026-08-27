# Cab Booking

Match an available driver to a rider, track the trip, calculate fare, and settle payment.

## Scope

Support rider requests, nearby-driver matching, fare estimates, assignment, trip lifecycle, payment, and rating. Mapping, messaging, and live location transport are external.

## Model

| Type | Responsibility |
|---|---|
| Rider | customer identity |
| Driver | availability, location, vehicle, and rating |
| Ride | route, assignment, fare, and lifecycle |
| MatchingStrategy | chooses an eligible driver |
| DistanceStrategy | calculates distance |
| FareStrategy | calculates quote or final fare |
| RideService | request, accept, start, complete, cancel |
| PaymentGateway | payment boundary |

Driver availability and Ride status are related but distinct state.

## Dispatch flow

1. Validate pickup and destination.
2. Find eligible available drivers.
3. Ask MatchingStrategy to rank them.
4. Atomically claim one driver and create the ride.
5. Return estimate and assignment.

Completion calculates final fare, charges payment, closes the ride, and makes the driver available according to the failure policy.

## Design choices

- Matching, distance, and fare are separate strategies because they change independently.
- Surge pricing decorates base fare.
- Ride owns legal transitions.
- RideService coordinates driver and ride changes.
- External maps and payments sit behind narrow interfaces.

## Correctness

Checking driver availability and claiming the driver must be atomic. A production system uses a conditional status/version update and an idempotent ride request key.

## Run

    python "solutions/cab-booking/main.py"
    python -m unittest discover -s "solutions/cab-booking/tests" -t "solutions/cab-booking" -v

## Follow-ups

Add driver offers with timeout, pooling, scheduled rides, cancellation fees, geospatial indexing, and location-event processing.
