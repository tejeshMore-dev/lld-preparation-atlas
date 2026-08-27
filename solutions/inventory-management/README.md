# Inventory Management Low-Level Design

Track on-hand and reserved stock by SKU and warehouse, prevent oversell, and make every receipt, reservation, release, shipment, or adjustment auditable.

## Understanding the Problem

Track on-hand and reserved stock by SKU and warehouse, prevent oversell, and make every receipt, reservation, release, shipment, or adjustment auditable.

The design starts with the business invariant and the critical workflow. Named patterns come later, only where a requirement creates a real variation or boundary.

## Requirements

### Clarifying Questions

- Is stock tracked per warehouse?
- Can an order split across locations?
- Are partial reservations allowed?
- Do lots or serial numbers matter?
- Must multi-SKU reservation be all-or-nothing?

### Final Requirements

1. Receive stock into a SKU/location balance.
2. Reserve available units for an order.
3. Release or expire reservations.
4. Ship reserved units and reduce physical stock.
5. Record adjustments and an immutable movement history.

The detailed reference below records additional assumptions, exclusions, validation rules, and edge cases.

## Core Entities and Relationships

| Entity | Responsibility |
|---|---|
| SKU | Stable product identity. |
| Warehouse | Stock location. |
| StockItem | Owns on-hand, reserved, version, and quantity invariants. |
| Reservation | Owns allocated lines, expiry, and lifecycle. |
| AllocationPolicy | Builds a feasible location plan. |
| StockMovement | Append-only audit fact. |
| InventoryService | Coordinates transactional workflows. |

The object that owns mutable state also owns the invariant protecting that state. Coordinating services load collaborators and sequence the use case; they do not bypass entity behavior.

## Class Design

### Good Solution

Store on-hand and reserved; derive available instead of persisting it.

### Great Solution

Use conditional quantity updates, atomic multi-line reservation, idempotent commands, reservation expiry, and ledger/balance reconciliation.

### Final Class Design

The critical collaboration is: load candidates -> allocation plan -> atomically revalidate and increment reserved -> create reservation/movements -> ship, release, or expire.

The full class map, state transitions, method contracts, and design rationale are preserved in the detailed reference below.

## Implementation

Implement one vertical slice before filling every class:

    load candidates -> allocation plan -> atomically revalidate and increment reserved -> create reservation/movements -> ship, release, or expire

### Complete Code Implementation

This repository currently treats this problem as a Markdown design exercise. The contracts, algorithms, atomic boundaries, pseudocode, and complete verification plan are in the detailed reference below. Implement the entity that owns the main invariant first, then the coordinating service.

## Verification

Verify the happy path, the highest-risk rejection, and state after failure. Then force two competing operations at the atomic boundary and assert the invariant, not thread timing.

The detailed reference lists problem-specific test cases and complexity.

## Extensibility

- Lots, batches, serials, and FEFO
- Backorders, safety stock, and transfers
- Replenishment and cycle-count reconciliation

Each extension should enter through a named policy, boundary, or lifecycle change rather than a new conditional inside the main workflow.

## What Is Expected at Each Level?

### Junior

Deliver the agreed core workflow with coherent entities, valid state changes, and straightforward failure handling.

### Mid-level

Make invariants explicit, isolate real variations, cover failure paths with tests, and discuss the relevant concurrency boundary.

### Senior

Explain oversell prevention, multi-SKU transactions, optimistic versus conditional updates, expiry races, idempotency, and ledger reconciliation.

## Interview Walkthrough

1. Clarify the version-one scope and exclusions.
2. State the invariants before drawing classes.
3. Introduce the core entities and walk: load candidates -> allocation plan -> atomically revalidate and increment reserved -> create reservation/movements -> ship, release, or expire.
4. Compare the good and great solution based on the stated requirements.
5. Implement a complete vertical slice and one failure test.
6. Handle a realistic follow-up through an explicit extension seam.

## Detailed Design Reference

<details>
<summary>Open the implementation-specific deep dive</summary>
Design warehouse stock tracking with receipt, reservation, release, shipment, adjustment, and an auditable movement history.

## 1. Understanding the problem

Inventory is not one quantity.

For each SKU and location, distinguish:

- on_hand: physically present units;
- reserved: promised to open orders;
- available: on_hand minus reserved;
- in_transit: moving but not yet received;
- damaged or quarantined: present but not sellable.

Version one models on_hand and reserved. The key challenge is preventing oversell while keeping every quantity change explainable.

## 2. Clarifying questions

- Is inventory tracked per warehouse?
- Can one order split across warehouses?
- Are partial reservations allowed?
- Are products identified by SKU?
- Do lots, batches, serial numbers, or expiry dates matter?
- Can stock go negative for backorders?
- When does shipment reduce stock?
- Do reservations expire?
- Are adjustments audited?
- Must multi-SKU reservations be all-or-nothing?
- Will several service instances update the same SKU?

## 3. Final requirements

Version one supports:

1. Products identified by SKU.
2. Multiple warehouses.
3. One StockItem per SKU and warehouse.
4. Receiving stock.
5. Reserving stock for an order.
6. Releasing or expiring a reservation.
7. Shipping reserved stock.
8. Audited positive or negative adjustments.
9. Single-warehouse and split allocation policies.
10. Exact, non-negative integer quantities.
11. Thread-safe or transactional updates.

Procurement, demand forecasting, and carrier tracking are outside the core.

## 4. Invariants

For every StockItem:

    available = on_hand - reserved
    on_hand >= 0
    reserved >= 0
    reserved <= on_hand

Additional rules:

1. Do not persist available independently.
2. A reservation line has a positive quantity.
3. Active reservations may be released or shipped exactly once.
4. Shipment reduces both on_hand and reserved.
5. Release reduces reserved only.
6. Receipt increases on_hand only.
7. Every successful quantity change creates a StockMovement.
8. Failed multi-line operations leave all quantities unchanged.
9. SKU and warehouse identities are stable.

## 5. Core model

| Type | Important state | Responsibility |
|---|---|---|
| Product/SKU | identity and descriptive data | catalog identity |
| Warehouse | ID and location | stock location |
| StockItem | SKU, warehouse, on_hand, reserved, version | protects quantity invariants |
| Reservation | order, lines, expiry, state | temporary promise of inventory |
| ReservationLine | stock item/location and quantity | immutable allocation |
| StockMovement | type, quantity, reason, reference, time | append-only audit fact |
| AllocationPolicy | configuration | builds a feasible allocation plan |
| InventoryService | repositories, clock, transaction | coordinates workflows |

Relationships:

    Warehouse o-- StockItem
    Product --> StockItem
    Reservation *-- ReservationLine
    ReservationLine --> StockItem
    StockItem o-- StockMovement
    InventoryService --> AllocationPolicy

## 6. Quantity value

Use an integer Quantity value or validate integers at every boundary.

Do not use float. Units such as weight require a separate measured-quantity type with unit and scale.

Useful operations reject negative results:

    quantity.add(delta)
    quantity.subtract(delta)
    quantity.is_at_least(required)

## 7. StockItem design

StockItem owns local quantity changes:

    receive(quantity)
    reserve(quantity)
    release(quantity)
    ship_reserved(quantity)
    adjust(delta, reason)

reserve() checks available before incrementing reserved.

ship_reserved() checks the requested units are reserved, then decrements reserved and on_hand together.

Each method can return a movement description; the application transaction persists the state and movement atomically.

## 8. Reservation design

Reservation state:

    PENDING -> ACTIVE -> FULFILLED
                       \-> RELEASED
                       \-> EXPIRED
                       \-> CANCELLED

Reservation owns its lines and legal transitions. It does not directly locate stock; AllocationPolicy creates the plan before activation.

Expose:

    activate(lines, expires_at)
    release(now)
    expire(now)
    fulfill(shipment_id)

Repeated terminal commands should be idempotent or return a stable conflict.

## 9. Allocation policy

Input:

    requested SKU quantities
    candidate StockItems with available quantities

Output:

    allocation plan: list of (stock_item_id, quantity)

Policies:

- SingleWarehousePolicy: one warehouse must fulfill every line.
- SplitWarehousePolicy: quantities may be divided.
- NearestWarehousePolicy: prefer a distance/rank.
- FEFO policy: for expiring lots, first-expire-first-out.

A policy proposes a plan from a snapshot. The service must revalidate and claim it atomically because availability can change.

## 10. Receive workflow

1. Validate SKU, warehouse, and positive quantity.
2. Load or create StockItem.
3. Call receive().
4. Append a RECEIPT movement with supplier/reference.
5. Save item and movement in one transaction.
6. Publish StockReceived after commit.

An idempotency key prevents a retried receiving message from adding stock twice.

## 11. Reserve workflow

    Order -> InventoryService: reserve(orderId, requestedLines)
    InventoryService -> AllocationPolicy: plan(candidates, request)
    AllocationPolicy -> InventoryService: allocations
    InventoryService -> StockItems: reserve quantities
    InventoryService -> Reservation: activate(lines, expiry)
    InventoryService -> Repository: commit state + movements
    InventoryService -> Order: reservationId

Detailed flow:

1. Reject duplicate order/idempotency key.
2. Load candidate stock.
3. Build a feasible plan.
4. Begin the atomic boundary.
5. Revalidate available quantity for every chosen item.
6. Increase reserved quantities.
7. Create the ACTIVE reservation.
8. Append RESERVATION movements.
9. Commit or roll back all lines.

## 12. Release and expiry

Release:

- transition ACTIVE to RELEASED;
- decrement reserved for each line;
- append RELEASE movements.

Expiry uses the same quantity behavior but a different reason/state. A scheduled worker queries due active reservations and issues idempotent expire commands.

Expiry racing shipment must use a conditional reservation-state transition. Exactly one wins.

## 13. Shipment

1. Load ACTIVE reservation.
2. Validate shipment lines against reserved lines.
3. For each line, call ship_reserved().
4. Mark reservation FULFILLED.
5. Append SHIPMENT movements.
6. Commit atomically.

Partial shipment requires remaining quantities per reservation line and a PARTIALLY_FULFILLED state. Do not add it unless required.

## 14. Adjustments

Adjustment corrects recorded stock after count, damage, or loss.

Require:

- signed delta;
- reason code;
- actor;
- reference/evidence;
- timestamp.

A negative adjustment cannot make on_hand smaller than reserved unless the business explicitly supports shortage resolution. Options are reject, cancel reservations, or mark an exception workflow.

## 15. Error model

| Error | Meaning |
|---|---|
| UnknownSKU | product does not exist |
| UnknownWarehouse | location does not exist |
| InvalidQuantity | zero, negative, or wrong unit |
| InsufficientStock | allocation cannot satisfy the request |
| ReservationConflict | state/version changed |
| InvalidTransition | command does not apply to current state |
| DuplicateCommand | idempotency key reused incompatibly |
| ReconciliationRequired | physical and recorded stock disagree |

Return shortage detail by SKU when useful, but do not leak repository records.

## 16. Patterns and principles

| Technique | Purpose |
|---|---|
| Strategy | warehouse/lot allocation |
| Aggregate | StockItem and Reservation consistency boundaries |
| Repository | persisted aggregate access |
| Unit of work | multi-item atomic commit |
| Domain event | replenishment and downstream notification |
| Ledger | immutable movement audit |
| Clock | reservation expiry |
| Idempotency | repeated messages and API calls |

Do not model Receive, Reserve, and Ship as subclasses; they are operations and movement facts.

## 17. Concurrency

The vulnerable operation is:

    if item.available >= requested:
        item.reserved += requested

It must be atomic.

Options:

- in-memory lock per StockItem;
- optimistic version update;
- conditional SQL update where on_hand - reserved >= requested;
- pessimistic row lock for high contention.

For multi-SKU all-or-nothing reservation, acquire/lock items in stable SKU/location order and transact every line. Retrying is safe only with an idempotency key.

## 18. Persistence

Suggested constraints:

- unique(sku_id, warehouse_id) for StockItem;
- unique(order_id) for active Reservation if one per order;
- non-negative check constraints;
- version column for optimistic locking;
- unique command/idempotency key;
- immutable StockMovement rows.

The movement ledger explains changes; the StockItem balance makes reads fast. Reconciliation can rebuild expected balances and compare them with stored state.

## 19. Complexity

For W candidate warehouses and I requested items:

- candidate scan: O(WI) in a simple implementation;
- reservation mutation: O(number of allocated lines);
- receive/adjust one item: O(1) after lookup;
- release/ship: O(reservation lines);
- ledger query: O(movements), normally indexed and paginated.

Indexes can optimize available-stock lookup by SKU and region.

## 20. Verification

Test:

- receipt increases on_hand;
- available is derived correctly;
- exact reservation succeeds;
- oversell is rejected without partial change;
- release restores availability;
- shipment reduces on_hand and reserved;
- expiry is idempotent;
- invalid transitions;
- positive and negative adjustment;
- adjustment cannot violate reserved <= on_hand;
- single and split allocation;
- concurrent reservations have bounded winners;
- multi-line failure rolls back all items;
- duplicate receive idempotency;
- every successful mutation creates one movement.

## 21. Extensibility

- **Lots and expiry:** StockLot becomes the allocatable item; use FEFO.
- **Serial numbers:** allocate individual serial entities rather than quantities.
- **Backorders:** represent unfulfilled demand separately; do not make available negative.
- **Safety stock:** allocation policy subtracts protected quantity.
- **Transfers:** paired outbound/in-transit/inbound movements.
- **Replenishment:** publish low-stock facts to procurement.
- **Reservations across regions:** saga/compensation when one transaction is impossible.
- **Cycle count:** explicit reconciliation workflow.

## 22. Trade-offs

- Balance plus ledger duplicates data but supports fast reads and audit.
- One transaction across many SKUs is correct but increases contention.
- Split fulfillment improves availability but adds shipping cost and more lines.
- Optimistic locking works for low conflict; conditional updates are efficient for hot stock.
- Reservation expiry recovers capacity but adds time and worker semantics.

## 23. Interview expectations

### Junior

Model Product, Warehouse, StockItem, receive, reserve, and ship with non-negative quantities.

### Mid-level

Separate reservation lifecycle, allocation policy, ledger, failure semantics, and tests.

### Senior

Discuss atomic multi-line reservation, optimistic/conditional updates, idempotency, audit reconciliation, expiry races, and distributed allocation trade-offs.

## 24. Interview walkthrough

1. Define on_hand, reserved, and derived available.
2. State reserved <= on_hand and no-oversell invariants.
3. Put quantity rules in StockItem.
4. Let AllocationPolicy propose and InventoryService atomically claim.
5. Walk reserve, release, and ship.
6. Test oversell and rollback.
7. Add ledger, persistence, and distributed concerns as explicit extensions.

</details>
