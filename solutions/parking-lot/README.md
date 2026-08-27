# Parking Lot Low-Level Design

Design a parking lot that assigns a compatible spot, tracks the parking session, collects payment, and releases the spot safely.

This guide is interview-first: agree on scope, identify invariants, assign responsibilities, walk the workflows, and only then discuss patterns or production extensions.

## 1. Understanding the problem

The system manages a scarce resource: parking spots.

The difficult part is not creating Vehicle and ParkingSpot classes. It is preserving these rules while several actions happen:

- a vehicle receives one suitable free spot;
- the same spot is never assigned twice;
- the same vehicle does not receive two active tickets;
- the exit fee uses the correct duration and rate;
- a spot is released only after successful payment.

A useful version one can run in one process and keep state in memory. Persistence, gates, cameras, and distributed coordination are boundaries that can be added later.

## 2. Clarifying questions

Ask enough questions to select a coherent version one.

### Parking structure

- Is this one lot or several locations?
- Does the lot contain multiple floors?
- Are spot identifiers unique across the entire lot?
- Does distance mean distance from one entrance or a chosen entrance?

### Vehicles and spots

- Which vehicle types are supported?
- Which spot types exist?
- Can a smaller vehicle use a larger spot?
- Should allocation prefer the nearest spot or preserve larger spots?

### Entry and exit

- Can the same vehicle enter twice?
- Is a ticket physical, digital, or simply an identifier?
- What happens when a ticket is missing?
- Is payment required before the spot is released?

### Pricing and payment

- Are charges hourly, daily, or slab based?
- Are partial hours rounded up?
- Do prices vary by vehicle, day, or floor?
- Which payment methods are supported?
- What should happen when payment fails?

### Correctness

- Can multiple gates submit requests concurrently?
- Is state stored in memory or a database?
- Must retries be idempotent?

Do not design every answer. State assumptions and continue.

## 3. Final requirements

This implementation chooses the following scope.

### Functional requirements

1. Add floors and spots to a parking lot.
2. Support motorcycle, car, and truck vehicles.
3. Support regular, compact, and large spots.
4. Allocate a compatible available spot.
5. Issue an active ticket when entry succeeds.
6. Reject a duplicate active vehicle.
7. Calculate a fee when the vehicle exits.
8. Process payment through an injected payment processor.
9. Vacate the spot only after successful payment.
10. Support replaceable allocation and pricing policies.

### Compatibility rule

| Vehicle | Minimum spot | May use |
|---|---|---|
| Motorcycle | Regular | Regular, Compact, Large |
| Car | Compact | Compact, Large |
| Truck | Large | Large |

A smaller vehicle may use a larger spot. The BestFitStrategy preserves large spots where possible; NearestFirstStrategy optimizes walking distance.

### Pricing assumptions

- Hourly and daily pricing are supported.
- A started hour or day is billed as a complete unit.
- The minimum charge is one unit.
- Rates vary by vehicle type.
- A decorator can add a weekend percentage surcharge.
- The current sample uses float amounts for simplicity. Production money should use Decimal or integer minor units.

### Out of scope

- advance reservations;
- lost-ticket pricing;
- electric charging;
- display boards;
- automated gates and number-plate recognition;
- persistent or distributed storage;
- refunds and payment reconciliation.

## 4. Invariants

An invariant is a rule that must remain true after every public operation.

1. A spot contains at most one vehicle.
2. An active vehicle has at most one active ticket.
3. A ticket refers to the spot occupied by its vehicle.
4. Only a compatible vehicle can occupy a spot.
5. An inactive ticket cannot be paid again.
6. Failed payment leaves the ticket active and the spot occupied.
7. Floor identifiers and lot-wide spot identifiers are unique.
8. Fee calculation requires an exit time.

The implementation protects the first seven entry/exit rules with one ParkingLot lock.

## 5. Core model

| Type | Important state | Responsibility |
|---|---|---|
| Vehicle | license plate, vehicle type | identifies the arriving vehicle |
| ParkingSpot | ID, type, floor, distance, occupancy | decides fit; assigns and vacates a vehicle |
| ParkingFloor | floor ID, spots | validates and groups spots |
| Ticket | ID, vehicle, spot, entry/exit time, status | records one parking session |
| Receipt | payment result and amount | immutable-style payment evidence |
| ParkingLot | floors, active/history tickets, policies | coordinates entry and exit |
| SpotAllocationStrategy | none | chooses one spot from candidates |
| PricingStrategy | pricing configuration | calculates the fee |
| PaymentProcessor | provider dependency | attempts payment |

### Relationships

    classDiagram
      ParkingLot "1" *-- "*" ParkingFloor
      ParkingFloor "1" *-- "*" ParkingSpot
      Ticket --> Vehicle
      Ticket --> ParkingSpot
      ParkingLot --> SpotAllocationStrategy
      ParkingLot --> PricingStrategy
      ParkingLot --> PaymentProcessor
      PaymentProcessor --> Receipt

ParkingLot composes floors. A Ticket associates one Vehicle with one ParkingSpot for a time interval. Strategies and the payment processor are injected collaborators.

## 6. Class design

### Vehicle

Vehicle is a small data object. Its license plate provides business identity; vehicle_type drives compatibility and price selection.

For production code, normalize and validate the plate at construction so CAR-123 and car-123 cannot create separate active sessions accidentally.

### ParkingSpot

ParkingSpot owns the occupancy state, so it also owns the rules that protect that state:

- can_fit_vehicle(vehicle)
- is_available()
- assign(vehicle)
- vacate(vehicle)

Callers cannot correctly reproduce these checks by setting is_occupied themselves. assign() validates availability and compatibility before mutation. vacate() verifies the same vehicle is leaving.

### ParkingFloor

ParkingFloor groups spots and rejects:

- a spot whose floor_number disagrees with the floor;
- a duplicate spot ID inside that floor.

Its find_spot() method can delegate to an allocation strategy. ParkingLot flattens all floor spots when selection must be global.

### Ticket

Ticket is the record of one parking session:

    ACTIVE -> PAID

EXPIRED exists in the enum for a possible timeout or abandoned-ticket policy, but the current workflow does not transition to it.

A richer model would expose mark_paid(exit_time) rather than allowing direct field mutation. The current dataclass keeps the interview implementation small.

### ParkingLot

ParkingLot is the application service and aggregate coordinator.

It owns:

- lot-wide uniqueness checks;
- the active-ticket lookup;
- the atomic entry workflow;
- the atomic exit workflow;
- delegation to allocation, pricing, and payment collaborators.

It should not contain vehicle-to-spot mapping tables or pricing branches; those decisions belong to the relevant object or strategy.

### Allocation strategies

SpotAllocationStrategy defines:

    select(spots, vehicle) -> ParkingSpot | None

NearestFirstStrategy filters available compatible spots and chooses the smallest distance.

BestFitStrategy chooses the smallest compatible spot type, then the nearest spot. This avoids filling a large spot with a motorcycle when a regular spot is available.

### Pricing strategies

PricingStrategy defines:

    compute_fee(ticket) -> amount

HourlySlabStrategy and DailySlabStrategy share the same contract. WeekendSurchargeDecorator wraps another pricing strategy and adds a percentage only for weekend exits.

### Payment processor

PaymentProcessor isolates the external payment capability. ParkingLot knows only pay(amount, method), not provider-specific request or response fields.

UPIPaymentProcessor is a deterministic sample implementation. A real adapter would use an idempotency key and translate provider failures into stable domain errors.

## 7. Entry workflow

    sequenceDiagram
      Client->>ParkingLot: park_vehicle(vehicle)
      ParkingLot->>ParkingLot: reject duplicate active vehicle
      ParkingLot->>SpotAllocationStrategy: select(all spots, vehicle)
      SpotAllocationStrategy-->>ParkingLot: compatible spot or none
      ParkingLot->>ParkingSpot: assign(vehicle)
      ParkingLot->>ParkingLot: create and store active ticket
      ParkingLot-->>Client: Ticket

Step by step:

1. Acquire the lot lock.
2. Search tickets for the same plate with ACTIVE status.
3. Build the lot-wide candidate spot list.
4. Ask the allocation strategy to choose a spot.
5. Fail without mutation if none is available.
6. Ask the spot to assign the vehicle.
7. Create and store the ticket.
8. Return the ticket and release the lock.

The availability check, spot assignment, and ticket creation occur inside one critical section. No other entry can claim the same spot between those steps.

## 8. Exit workflow

    sequenceDiagram
      Client->>ParkingLot: exit_vehicle(ticketId, method)
      ParkingLot->>ParkingLot: validate active ticket
      ParkingLot->>PricingStrategy: compute_fee(ticket)
      PricingStrategy-->>ParkingLot: amount
      ParkingLot->>PaymentProcessor: pay(amount, method)
      PaymentProcessor-->>ParkingLot: Receipt
      alt payment completed
        ParkingLot->>ParkingSpot: vacate(vehicle)
        ParkingLot->>ParkingLot: mark ticket paid
        ParkingLot-->>Client: Receipt
      else payment failed
        ParkingLot->>ParkingLot: clear tentative exit time
        ParkingLot-->>Client: payment failure
      end

The ordering is deliberate: payment happens before the spot is released. If payment fails, the vehicle remains parked and a later retry can use the same ticket.

The current lock is held during payment for simple in-process correctness. That would be undesirable with a real network call. A production design would introduce states such as PAYMENT_PENDING and use an idempotent, retryable workflow.

## 9. Why these patterns are used

| Pattern or principle | Where | Requirement it addresses |
|---|---|---|
| Strategy | spot allocation | nearest and best-fit policies vary |
| Strategy | fee calculation | hourly and daily rules vary |
| Decorator | weekend surcharge | optional price adjustment composes with base pricing |
| Dependency inversion | payment processor | domain flow should not depend on one provider |
| Composition | lot, floor, and spot | structure has clear ownership |
| Encapsulation | ParkingSpot | occupancy rules stay beside occupancy state |

A factory, singleton, observer, or inheritance tree is not required for this scope.

## 10. Complexity

Let F be the number of floors, S the total number of spots, and T the number of stored tickets.

| Operation | Current complexity | Reason |
|---|---:|---|
| add_floor | O(F + S) | checks existing floor and spot IDs |
| park_vehicle duplicate check | O(T) | scans active/history tickets |
| choose spot | O(S) | filters and selects candidates |
| ticket lookup on exit | O(1) average | dictionary by ticket ID |
| assign or vacate | O(1) | one spot mutation |

Production improvements could maintain:

- active_ticket_by_plate for O(1) duplicate detection;
- availability indexes by spot type and entrance;
- persistent unique constraints as the final correctness guard.

Do not add those indexes until scale or latency requires them.

## 11. Concurrency and consistency

### Current implementation

One threading.Lock serializes:

- floor changes;
- duplicate-vehicle checks;
- spot selection and assignment;
- ticket creation;
- fee/payment/exit updates.

This is correct for one process but limits throughput and holds the lock during payment.

### Multiple entrances

For several gates in one process, the same lock still prevents double allocation.

For several application instances:

1. Store spots and active tickets in a shared database.
2. Claim a spot with a conditional update or row lock.
3. Add a unique constraint for one active assignment per spot.
4. Add a unique constraint/index for one active ticket per normalized plate.
5. Use a transaction for spot claim and ticket creation.
6. Give entry and exit commands idempotency keys.
7. Move payment I/O outside database locks and model an explicit payment state.

Per-floor locks improve concurrency only if allocation does not need a global nearest decision. Otherwise lock ordering and revalidation become necessary.

## 12. Failure handling

| Failure | Required result |
|---|---|
| duplicate active vehicle | reject; existing session is unchanged |
| no compatible spot | reject; no ticket is created |
| incompatible direct assignment | reject; spot stays free |
| unknown/inactive ticket | reject; no payment attempt |
| unsupported payment method | reject; ticket and spot stay active |
| failed payment | clear tentative exit; keep vehicle parked |
| repeated successful exit | reject inactive ticket |

For a real payment provider, an unknown timeout result is different from a confirmed failure. Reconcile by idempotency key before attempting another charge.

## 13. Verification

Run the demonstration:

    python "solutions/parking-lot/main.py"

Run the tests:

    python -m unittest discover -s "solutions/parking-lot/tests" -t "solutions/parking-lot" -v

The test suite verifies:

- nearest selection across floors;
- best-fit preservation of large spots;
- duplicate vehicle rejection;
- full-lot rejection;
- compatibility enforcement;
- successful payment and spot release;
- repeated-exit rejection;
- failed-payment rollback;
- hourly, daily, and weekend pricing;
- duplicate floor and spot ID rejection.

A useful additional concurrency test would start two threads against one available spot and assert exactly one ticket is created.

## 14. Code map

| Concern | File |
|---|---|
| enums | models/enums.py |
| vehicle | models/vehicle.py |
| spot behavior | models/parking_spots.py |
| floor grouping | models/parking_floor.py |
| ticket and receipt | models/ticket.py, models/receipt.py |
| entry and exit orchestration | services/parking_lot.py |
| payment boundary | services/payment_processor.py |
| allocation policies | strategies/allocation.py |
| pricing policies | strategies/pricing.py |
| price decorators | strategies/decorators.py |
| executable examples | main.py |
| behavioral verification | tests/test_parking_lot.py |

## 15. Extensibility

### Multi-floor display boards

Maintain availability counts as a projection updated after successful assign/vacate events. Do not make the display board the source of truth.

### Vehicle-specific pricing

Already supported by the rate maps in the pricing strategies. More complex rules can use a configured rate card rather than adding subclasses per vehicle.

### Multiple entrances

Give each entrance a distance/rank per spot and pass entrance_id into the allocation policy. Distributed entrances also require shared atomic persistence.

### Reservations

Introduce a time-bounded SpotReservation or reserve capacity by spot type. Define precedence between reservations and drive-in allocation.

### Electric charging

Add capabilities to spots instead of building a deep ElectricCar/ElectricSpot hierarchy. Allocation filters by required capabilities; charging has its own session and pricing policy.

### Lost tickets

Use plate lookup and a LostTicketPricingPolicy. Staff authorization should be a separate boundary, and the audit record should remain immutable.

### Dynamic pricing

Compose pricing policies from rate card, occupancy multiplier, vehicle rate, and promotional adjustment. Freeze or clearly define which rate applies to an already-issued ticket.

## 16. Trade-offs in the current code

- A global lock is simple and correct but coarse.
- Holding the lock during payment is acceptable only for the deterministic sample adapter.
- Ticket is a mutable dataclass rather than a behavior-rich state machine.
- Float keeps the demo small but is not suitable for production money.
- Ticket history grows indefinitely and duplicate-plate detection scans it.
- datetime.now() is not injected, so time-dependent tests construct tickets directly.
- Exceptions are generic; stable domain-specific errors would improve an API boundary.

These are conscious version-one compromises, not patterns to copy blindly.

## 17. Interview expectations

### Junior

A solid answer includes:

- Vehicle, ParkingSpot, Ticket, and ParkingLot;
- correct vehicle/spot compatibility;
- entry and exit workflows;
- basic fee calculation;
- prevention of obvious double assignment.

### Mid-level

Also expect:

- explicit invariants and lifecycle;
- allocation and pricing policies separated from orchestration;
- failure behavior for full capacity and payment;
- focused tests;
- a clear multi-floor model.

### Senior

Also discuss:

- atomicity across multiple entrances;
- idempotent entry, exit, and payment;
- lock granularity and contention;
- indexes and database constraints;
- failure ordering and payment reconciliation;
- trade-offs instead of unnecessary pattern names.

## 18. Interview walkthrough

A concise explanation can sound like this:

1. “I will support multi-floor, drive-in parking for three vehicle and spot sizes.”
2. “The main invariant is one active ticket per vehicle and one vehicle per spot.”
3. “ParkingSpot owns compatibility and occupancy because it has the required state.”
4. “ParkingLot coordinates the atomic entry and exit use cases.”
5. “Allocation and pricing are strategies because those are stated variations.”
6. “I will implement entry first, then successful and failed exit.”
7. “For multiple processes, I would replace the in-memory lock with conditional persistence and unique active-assignment constraints.”

That is enough structure to begin coding while leaving room for follow-up requirements.
