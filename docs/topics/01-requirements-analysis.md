# 1. Requirements and Scope

## Outcome

Turn an open-ended prompt into a small contract you can design in 45 minutes.

## Start with behavior

Ask for examples, not every possible feature.

| Question | Why it matters |
|---|---|
| Who uses the system? | Finds actors and permissions |
| What are the top three actions? | Defines the critical workflows |
| What rules may never be broken? | Reveals invariants |
| What can fail? | Shapes results and recovery |
| Is state shared? | Exposes concurrency risks |
| What is out of scope? | Prevents speculative design |

For a parking lot, a useful scope might be: park a vehicle, issue a ticket, calculate a fee, and release the spot. Reservations, payments, and multiple entrances can wait.

## Write a tiny contract

Capture four things before classes:

- **Use cases:** actions the system performs.
- **Inputs and outputs:** what callers provide and receive.
- **Invariants:** rules that must always hold.
- **Constraints:** scale, time, persistence, and concurrency assumptions.

Example invariant: one parking spot can have at most one active ticket.

## Separate needs from guesses

Label uncertain statements as assumptions:

- confirmed: cars and motorcycles are supported;
- assumed: one process owns the lot;
- deferred: pricing changes by time of day.

This makes follow-up changes cheap and shows the interviewer where your design boundary came from.

## Prioritize a vertical slice

A good first slice crosses the whole design:

    request -> validation -> domain change -> result

Implement the common path and one important failure. Do not begin with every enum, factory, or database interface.

## Common traps

- Turning nouns in the prompt directly into classes.
- Designing features that were never requested.
- Ignoring failure cases until the end.
- Mixing distributed-system concerns into an in-process LLD.
- Saying “thread-safe” without naming the shared invariant.

## Readiness check

You are ready when you can reduce a new prompt to five use cases, three invariants, and a clear out-of-scope list in five minutes.

Next: [Python and OOP](./02-python-oop-foundations.md).
