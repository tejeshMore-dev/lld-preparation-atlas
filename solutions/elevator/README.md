# Elevator System

Schedule hall and car requests while each elevator car preserves a valid movement and door state.

## Scope

Support multiple floors and cars, external direction requests, internal destination requests, scheduling, movement ticks, and events. Hardware control and emergency regulation are boundaries.

## Model

| Type | Responsibility |
|---|---|
| ElevatorCar | floor, direction, door state, and pending stops |
| HallRequest | floor and desired direction |
| CarRequest | destination chosen inside a car |
| SchedulingStrategy | selects a car for a hall request |
| ElevatorSystem | accepts requests and advances cars |
| ElevatorEvent | observable state change |

Invariants: a car moves only with doors closed; it serves valid floors; a stop is not lost; direction reflects remaining work.

## Critical flow

A hall request is validated and passed to the scheduler. The chosen car records the pickup. Each tick closes doors if needed, moves one floor toward work, opens at a requested stop, emits an event, and chooses the next direction.

The scheduler chooses a car; it does not mutate car internals.

## Design choices

- ElevatorCar owns its state machine.
- SchedulingStrategy supports direction-aware-nearest and least-stops policies.
- Requests are values; events expose changes without leaking mutable cars.
- A discrete tick keeps the simulation deterministic.
- An enum with guarded methods is clearer than a large State hierarchy here.

## Correctness

Request acceptance and stop-set mutation must be serialized per car. A central dispatcher is simple; actors or per-car queues are a natural production evolution. Never hold a scheduler-wide lock while operating doors or hardware.

## Run

    python "solutions/elevator/main.py"
    python -m unittest discover -s "solutions/elevator/tests" -t "solutions/elevator" -v

## Follow-ups

Add capacity, zoning, destination dispatch, maintenance mode, emergency behavior, request aging, and energy-aware scheduling.
