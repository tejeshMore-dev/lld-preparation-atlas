# Amazon Locker Low-Level Design

Assign a fitting locker to a package, secure pickup with an expiring credential, and release capacity after pickup, return, or expiry.

## Understanding the Problem

Assign a fitting locker to a package, secure pickup with an expiring credential, and release capacity after pickup, return, or expiry.

The design starts with the business invariant and the critical workflow. Named patterns come later, only where a requirement creates a real variation or boundary.

## Requirements

### Clarifying Questions

- Is assignment made before or during delivery?
- Which package and locker sizes exist?
- How long is a pickup code valid?
- Are customer returns supported?
- How are hardware failures confirmed or reconciled?

### Final Requirements

1. Allocate the smallest fitting available locker.
2. Deposit a package and activate a pickup credential.
3. Validate code and expiry during pickup.
4. Release expired or completed allocations exactly once.
5. Exclude lockers that are occupied or out of service.

The detailed reference below records additional assumptions, exclusions, validation rules, and edge cases.

## Core Entities and Relationships

| Entity | Responsibility |
|---|---|
| Package | Tracks shipment identity, size, owner, and state. |
| Locker | Protects compartment fit and availability. |
| LockerLocation | Groups lockers and provides the allocation boundary. |
| Allocation | Owns package-locker assignment, code, expiry, and lifecycle. |
| AllocationPolicy | Chooses a fitting locker. |
| AccessController | Adapts physical locker hardware. |

The object that owns mutable state also owns the invariant protecting that state. Coordinating services load collaborators and sequence the use case; they do not bypass entity behavior.

## Class Design

### Good Solution

Let Locker own occupancy and Allocation own code and expiry rules.

### Great Solution

Use an atomic package-and-locker claim, hashed credentials, injected time/code generation, and hardware confirmation with reconciliation.

### Final Class Design

The critical collaboration is: select fitting locker -> claim locker and create allocation -> open for deposit -> activate -> validate code -> open for pickup -> complete and release.

The full class map, state transitions, method contracts, and design rationale are preserved in the detailed reference below.

## Implementation

Implement one vertical slice before filling every class:

    select fitting locker -> claim locker and create allocation -> open for deposit -> activate -> validate code -> open for pickup -> complete and release

### Complete Code Implementation

This repository currently treats this problem as a Markdown design exercise. The contracts, algorithms, atomic boundaries, pseudocode, and complete verification plan are in the detailed reference below. Implement the entity that owns the main invariant first, then the coordinating service.

## Verification

Verify the happy path, the highest-risk rejection, and state after failure. Then force two competing operations at the atomic boundary and assert the invariant, not thread timing.

The detailed reference lists problem-specific test cases and complexity.

## Extensibility

- Nearby-location selection
- Multi-package orders and returns
- Sensors, staff override, and failed-attempt lockout

Each extension should enter through a named policy, boundary, or lifecycle change rather than a new conditional inside the main workflow.

## What Is Expected at Each Level?

### Junior

Deliver the agreed core workflow with coherent entities, valid state changes, and straightforward failure handling.

### Mid-level

Make invariants explicit, isolate real variations, cover failure paths with tests, and discuss the relevant concurrency boundary.

### Senior

Explain pickup-versus-expiry races, hardware/database failure ordering, credential security, and conditional allocation.

## Interview Walkthrough

1. Clarify the version-one scope and exclusions.
2. State the invariants before drawing classes.
3. Introduce the core entities and walk: select fitting locker -> claim locker and create allocation -> open for deposit -> activate -> validate code -> open for pickup -> complete and release.
4. Compare the good and great solution based on the stated requirements.
5. Implement a complete vertical slice and one failure test.
6. Handle a realistic follow-up through an explicit extension seam.

## Detailed Design Reference

<details>
<summary>Open the implementation-specific deep dive</summary>
Design a last-mile locker system that assigns a fitting compartment, supports secure deposit and pickup, and releases expired allocations.

## 1. Understanding the problem

A locker system connects three parties:

- a delivery agent deposits a package;
- a customer collects it using a pickup code;
- an operator manages locations and unavailable lockers.

The central resource is a locker compartment. The design must prevent two packages from owning the same locker and must release capacity after pickup or expiry.

## 2. Clarifying questions

### Network and capacity

- Are there several locker locations?
- Which locker sizes exist?
- Can a smaller package use a larger locker?
- Should allocation minimize wasted capacity or customer distance?

### Delivery and pickup

- Is a package assigned before the driver arrives or at deposit time?
- Who receives the pickup code?
- Does a code expire?
- How many failed attempts are allowed?
- Can staff override a blocked allocation?

### Returns

- Can a customer deposit a return?
- Does a return use a new code and lifecycle?
- When is the carrier expected to collect it?

### Correctness

- Can several drivers deposit concurrently?
- Is hardware controlled synchronously?
- What happens if the door opens but the database update fails?

## 3. Final requirements

Version one supports:

1. Several locations, each with many lockers.
2. Small, medium, and large packages and lockers.
3. Smallest-fitting-locker allocation.
4. Delivery deposit with an expiring pickup code.
5. Customer pickup with code validation.
6. Return initiation using an available locker.
7. Expired allocation release.
8. Locker maintenance state.
9. Deterministic time through an injected Clock.

Routing, notifications, and hardware protocols remain external boundaries.

## 4. Invariants

1. A locker has at most one active allocation.
2. A package has at most one active allocation.
3. The chosen locker is large enough for the package.
4. Only a valid, unexpired code opens the allocation.
5. A completed or expired allocation cannot be completed again.
6. Releasing an allocation releases its locker exactly once.
7. A locker under maintenance cannot be allocated.
8. Package and allocation lifecycles move only through legal transitions.

## 5. Core model

| Type | Important state | Responsibility |
|---|---|---|
| Package | ID, owner, size, state | shipment being deposited or returned |
| Locker | ID, size, state, active allocation | protects compartment availability |
| LockerLocation | ID, address, lockers | location capacity and search boundary |
| Allocation | package, locker, code hash, expiry, state | secures one temporary assignment |
| AllocationPolicy | none/configuration | selects the best fitting locker |
| LockerService | repositories and collaborators | coordinates deposit, pickup, return, expiry |
| AccessController | hardware port | opens a physical locker |
| Clock | current time | deterministic expiry decisions |

Relationships:

    LockerLocation *-- Locker
    Allocation --> Package
    Allocation --> Locker
    LockerService --> AllocationPolicy
    LockerService --> AccessController
    LockerService --> Clock

## 6. State models

Package:

    EXPECTED -> DEPOSITED -> COLLECTED
                         \-> EXPIRED
    EXPECTED -> RETURN_DEPOSITED -> RETURN_COLLECTED

Locker:

    AVAILABLE -> OCCUPIED -> AVAILABLE
    AVAILABLE -> OUT_OF_SERVICE -> AVAILABLE

Allocation:

    CREATED -> ACTIVE -> COMPLETED
                     \-> EXPIRED
                     \-> CANCELLED

Keep package, locker, and allocation state separate. They describe different facts even though their transitions are coordinated.

## 7. Class design

### Package

Package is an entity identified by package_id. PackageSize is an ordered value so fit is a comparison rather than subtype logic.

Package should expose deposit(), collect(), expire(), and return transitions rather than unrestricted status assignment.

### Locker

Locker owns availability because it owns compartment state.

Useful behavior:

    can_fit(package_size) -> bool
    allocate(allocation_id)
    release(allocation_id)
    mark_out_of_service()
    restore()

allocate() rejects an occupied, too-small, or unavailable locker. release() verifies allocation ownership so an old command cannot release a newer package.

### Allocation

Allocation owns:

- pickup credential hash;
- expiry timestamp;
- failed-attempt count;
- active/completed state;
- validation and completion behavior.

The plaintext code should be returned once for notification and never stored in production.

### LockerLocation

The location groups lockers and is the natural lock or transaction scope for simple allocation. It may maintain availability indexes by size when scanning becomes expensive.

### AllocationPolicy

The default SmallestFitPolicy:

1. filters available lockers that fit;
2. sorts by size and optional distance;
3. returns the smallest candidate.

A policy selects; Locker performs the state change.

### LockerService

LockerService coordinates repository access, policy selection, hardware, and entity transitions. It should read like deposit_package(), pickup_package(), initiate_return(), and expire_allocations().

## 8. Deposit workflow

    DeliveryAgent -> LockerService: deposit(package, location)
    LockerService -> AllocationPolicy: choose(lockers, package.size)
    AllocationPolicy -> LockerService: locker
    LockerService -> Locker: allocate(allocationId)
    LockerService -> Allocation: activate(codeHash, expiry)
    LockerService -> AccessController: open(lockerId)
    LockerService -> DeliveryAgent: deposit result

Recommended ordering depends on hardware guarantees. A safe conceptual workflow is:

1. Validate package eligibility.
2. Atomically claim a fitting locker and create an allocation.
3. Ask hardware to open the door.
4. Confirm deposit using a sensor or driver action.
5. Mark package deposited and allocation active.
6. Publish a notification event after commit.

If hardware fails before deposit confirmation, cancel the allocation and release the locker.

## 9. Pickup workflow

1. Load the active allocation by package or pickup reference.
2. Reject expired or blocked allocation.
3. Compare the submitted code with the stored hash.
4. Increment failed attempts atomically on mismatch.
5. Open the locker through AccessController.
6. Confirm the door/package event.
7. Mark allocation complete and package collected.
8. Release the locker.
9. Publish PackageCollected.

Repeated pickup should return a stable completed result or a clear conflict; it must not open a locker now assigned to someone else.

## 10. Return workflow

A return is not just a reversed pickup. It creates a new allocation whose authorized depositor is the customer and whose collector is the carrier.

Reuse locker allocation and access behavior, but keep return state explicit so notifications and expiry rules can differ.

## 11. Patterns and principles

| Technique | Purpose |
|---|---|
| Strategy | smallest-fit, nearest, or capacity-balancing allocation |
| Repository | persisted packages, lockers, and allocations |
| Adapter | physical locker controller |
| Domain event | optional notifications and operational projections |
| Value object | size, address, access code metadata |
| Dependency injection | clock, code generator, repositories, hardware |

Do not make SmallLocker, MediumLocker, and LargeLocker subclasses when their behavior is identical.

## 12. Concurrency

The select-and-allocate sequence is atomic.

In memory, use a per-location lock:

    with location.lock:
        locker = policy.choose(location.available_lockers(), package.size)
        locker.allocate(allocation_id)
        allocations.add(allocation)

In a database, use a conditional locker update or row lock plus unique active-allocation constraints for locker_id and package_id.

Expiry and pickup can race. Both must conditionally transition only an ACTIVE allocation; exactly one wins.

## 13. Failure handling

| Failure | Result |
|---|---|
| no fitting locker | no allocation; package remains expected |
| duplicate deposit | reject existing active allocation |
| wrong code | record attempt; do not open |
| expired code | expire allocation and release safely |
| hardware open failure | retry or cancel before deposit confirmation |
| notification failure | allocation remains valid; retry notification |
| repeated expiry job | no additional state change |
| maintenance during occupancy | block new use; preserve active pickup path |

## 14. Complexity

With L lockers at a location:

- naive smallest-fit selection: O(L);
- allocate/release after selection: O(1);
- allocation lookup by ID: O(1) average;
- expiry sweep: O(A) for A active allocations.

Queues or sets by locker size reduce selection toward O(1) or O(log L), but introduce index-consistency work.

## 15. Verification plan

Test:

- exact-size and larger-size fit;
- smallest fitting locker selection;
- full location;
- duplicate active package;
- successful deposit and pickup;
- wrong and expired codes;
- failed-attempt lockout;
- return deposit and carrier collection;
- maintenance exclusion;
- concurrent deposits with one locker;
- pickup racing expiry;
- idempotent release and expiry.

Inject Clock and CodeGenerator so tests never sleep and never depend on random values.

## 16. Extensibility

- **Nearby locations:** add a LocationSelectionPolicy above per-location allocation.
- **Multi-package orders:** coordinate several allocations and define all-or-nothing behavior.
- **Dynamic expiry:** inject an ExpiryPolicy based on shipment type.
- **Staff override:** use an audited AuthorizationService, not a universal master code.
- **Sensors:** translate hardware events through AccessController.
- **Notifications:** publish events after commit and retry independently.
- **Reservations:** introduce a reservation expiry distinct from deposited-package expiry.

## 17. Trade-offs

- Per-location locking is simple but serializes unrelated lockers.
- Exact locker assignment makes pickup direct but can waste capacity.
- Hardware and database cannot share one transaction; confirmation and reconciliation are necessary.
- Hashing codes improves security but prevents code recovery.
- A ledger of allocation events improves auditability but adds persistence work.

## 18. Interview expectations

### Junior

Model Package, Locker, Allocation, deposit, and pickup with fit and availability checks.

### Mid-level

Add explicit lifecycles, replaceable allocation, expiry, failure behavior, and focused tests.

### Senior

Discuss atomic allocation, pickup-versus-expiry races, hardware failure, idempotency, code security, and database constraints.

## 19. Interview walkthrough

1. Fix the package and locker sizes and the pickup-code lifetime.
2. State one-active-allocation invariants.
3. Put compartment state inside Locker and credential state inside Allocation.
4. Walk deposit and pickup before coding.
5. Implement smallest-fit allocation plus success and expiry tests.
6. Extend toward hardware and multi-instance concurrency only after the core is coherent.

</details>
