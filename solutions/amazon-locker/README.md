# Amazon Locker

Design a last-mile locker system that assigns a fitting compartment and secures pickup with an expiring code.

## Scope

Support package deposit, customer pickup, return initiation, and expired allocation release. Assume one process and an in-memory repository. Routing trucks, notifications, and physical hardware protocols are outside the core design.

## Model

| Type | Responsibility |
|---|---|
| Package | identity, size, owner, and delivery state |
| Locker | size and current allocation |
| LockerLocation | owns lockers and selects available capacity |
| Allocation | package-to-locker assignment, code, expiry, and lifecycle |
| AllocationPolicy | chooses a fitting locker |
| LockerService | coordinates deposit, pickup, return, and expiry |

Key invariant: one locker and one package can each have at most one active allocation.

    Package -> Allocation -> Locker
    LockerLocation -> many Locker
    LockerService -> AllocationPolicy + repositories + Clock

## Critical flow: deposit

1. Load the package and location.
2. Ask the policy for the smallest available locker that fits.
3. Allocate the locker and create an expiring pickup code.
4. Save both changes atomically.
5. Return the locker reference and code-delivery result.

Pickup validates the code and expiry, marks the package collected, closes the allocation, and releases the locker.

## Design decisions

- PackageSize is ordered, so fit is a comparison rather than subtype logic.
- Allocation owns code attempts and expiry because those rules belong to the assignment.
- A policy isolates locker selection; first-fit is enough initially.
- A Clock is injected so expiry tests are deterministic.
- Codes should be stored as hashes in a real system.

## Correctness

The availability check and allocation must be one atomic operation. A per-location lock is simple; a database can instead use a conditional update or unique active-allocation constraint.

Do not release the locker before the pickup state change commits. Repeated pickup with the same completed allocation should return a stable outcome or a clear conflict.

## Follow-ups

- Reserve adjacent lockers for multi-package orders.
- Add failed-code lockout and staff override.
- Select among nearby locations.
- Integrate hardware through a LockerController adapter.
- Publish deposited, collected, and expired events after commit.

## Interview finish

Implement PackageSize, Locker, Allocation, a first-fit policy, and deposit/pickup tests. Discuss persistence and hardware as boundaries, not as core domain classes.
