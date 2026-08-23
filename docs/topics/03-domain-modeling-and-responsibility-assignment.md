# Topic 3 - Domain Modeling and Responsibility Assignment

[Curriculum index](../README.md) | [Preparation roadmap](../roadmap.md) |
[Previous topic](./02-python-oop-foundations.md)

- **Category:** Object modeling
- **Difficulty:** Intermediate
- **Priority:** Essential
- **Prerequisites:** Topics 1-2
- **Running example:** Movie Ticket Booking
- **Output:** A responsibility-driven domain model with explicit identity,
  ownership, relationships, state, invariants, and collaborators

## Outcome

After completing this topic, you should be able to:

- Turn bounded requirements into a precise domain vocabulary.
- Discover candidate objects from behavior and rules, not nouns alone.
- Distinguish entities, value objects, records, policies, domain services,
  use-case coordinators, and external boundaries.
- Define identity and lifecycle deliberately.
- Assign every important behavior and invariant to an obvious owner.
- Model cardinality, relationship direction, ownership, and object lifetime.
- Separate a stable catalog object from its changing contextual state.
- Keep one authoritative owner for each mutable business fact.
- Replace contradictory booleans with explicit lifecycle states.
- Locate cross-object rules at the smallest boundary that can enforce them.
- Create behavior-rich domain objects without making one giant object graph.
- Review a model by tracing workflows and applying requirement changes.
- Explain and defend the model before writing implementation details.

## Core idea

A domain model is a deliberately simplified representation of the business
problem. It is not a database schema, API payload, collection of prompt nouns,
or diagram copied from a familiar solution.

```text
requirements
    -> shared vocabulary
    -> behaviors and invariants
    -> identity and state
    -> responsibility owners
    -> relationships and boundaries
    -> collaborations
    -> tests and change review
```

The central question is not:

> Which classes can I create?

It is:

> Which object has the information and authority to keep this rule true?

A useful first model gives every important fact one source of truth, every rule
one obvious enforcement point, and every workflow a small set of collaborators.

## Scope boundary

This topic focuses on conceptual object modeling and responsibility assignment.
It does not attempt to teach:

- UML notation or diagram mechanics; those belong to Topic 4.
- The formal SOLID, GRASP, and cohesion/coupling catalogues; Topic 5 deepens
  those design heuristics.
- Named Gang of Four patterns; Topics 6-8 cover them.
- Repository, unit-of-work, event-bus, and other application patterns; Topic 9
  covers reusable building blocks.
- Detailed API errors, thread synchronization, database transactions, or
  persistence mapping; Topics 10-12 cover those concerns.
- Strategic domain-driven design, bounded-context integration, or distributed
  service decomposition.

Terms such as *consistency boundary* are introduced only far enough to improve
an in-process LLD model. Do not turn every interview problem into a full DDD
exercise.

Code in this chapter uses Python 3.10+. Focused excerpts may rely on types shown
in an earlier fence. Production concerns such as locks and durable transactions
are called out but intentionally deferred.

## 1. Learn

### 1.1 Start with domain language

Domain language is the vocabulary used by the people and rules inside the
problem. Each important word should have one clear meaning.

For a movie booking system:

| Term | Precise meaning |
|---|---|
| Movie | Content that can be scheduled for screening |
| Theatre | A cinema venue |
| Screen | A physical auditorium within a theatre |
| Seat | A physical chair and its stable position/type |
| Show | One movie scheduled on one screen for a time interval |
| ShowSeat | The state and price context of one physical seat for one show |
| Hold | Temporary exclusive permission to pay for selected show seats |
| Booking | One user's checkout/ticket lifecycle for one show |
| Payment | One charge or refund record associated with a booking |

This vocabulary prevents several design errors before code exists. In
particular, a seat is not a show seat, a booking is not a payment, and a screen
is not a theatre.

Create a short glossary when:

- the same word is used with different meanings;
- two words may be mistaken for synonyms;
- an object has a stable form and a contextual form;
- the prompt uses an overloaded word such as `order`, `account`, `slot`, or
  `reservation`;
- an interviewer introduces a new term during a follow-up.

Use the vocabulary consistently in class names, methods, tests, and narration.
If the business says *hold*, a method called `temporarily_select()` creates
avoidable translation work.

### 1.2 Discover candidates from nouns, verbs, and rules

Nouns are candidates, not automatic classes.

From "a user holds seats for a show and confirms the booking after payment":

- Nouns suggest `User`, `Seat`, `Show`, `Booking`, and `Payment`.
- Verbs reveal `hold`, `confirm`, `pay`, and `expire` responsibilities.
- Rules reveal the most important boundaries: one seat cannot be held twice,
  only the hold owner can confirm it, and confirmation requires payment.

Use this discovery pass:

1. Extract domain terms.
2. Underline business verbs.
3. List "must", "only", "cannot", and "until" rules.
4. Identify facts that change over time.
5. Identify external systems and sources of time.
6. Classify candidates by role.
7. Merge duplicates and discard implementation-only nouns.

Do not create a domain class merely because the prompt contains words such as
`database`, `screen`, `button`, `list`, `manager`, or `system`. Some are UI or
infrastructure concerns; others are vague containers with no cohesive role.

Likewise, an important behavior may need a concept even when the prompt does
not provide a noun. A pricing rule can justify a `PricingPolicy`; an expiry rule
can justify an injected `Clock`.

### 1.3 Classify object roles

The following roles answer different design questions:

| Role | Defining property | Typical examples |
|---|---|---|
| Entity | Same business thing across changing state | `Booking`, `User`, `Show` |
| Value object | Defined entirely by its attributes | `Money`, `DateRange`, `Location` |
| Record/event | Historical fact that should not be rewritten casually | `PaymentAttempt`, `AuditEntry` |
| Policy | Named, replaceable business decision or calculation | `PricingPolicy`, `AllocationPolicy` |
| Domain service | Domain operation with no natural single-object owner | `FareCalculator`, `DebtSimplifier` |
| Use-case coordinator | Sequences a workflow across objects and boundaries | `BookingService` |
| External boundary | Narrow contract to time, payment, notification, etc. | `Clock`, `PaymentGateway` |

These are reasoning roles, not mandatory suffixes. A value object does not need
to be named `SomethingValue`, and an entity does not need to inherit from an
`Entity` base class.

Ask these questions in order:

1. Does the concept need continuity through change? If yes, it is likely an
   entity.
2. Is it interchangeable with any other instance having the same attributes?
   If yes, it is likely a value object.
3. Is it a historical fact whose original contents matter? It may be a record
   or event.
4. Is it a decision/calculation that varies? It may be a policy.
5. Does the operation span concepts but belong naturally to none? It may be a
   domain service.
6. Does it sequence a use case or call the outside world? It is likely a
   coordinator or boundary rather than a domain entity.

### 1.4 Entities: identity through change

An entity remains the same conceptual thing even when its attributes change.

A booking may move from pending to confirmed and later to cancelled. It is
still the booking identified by `booking_id`. Two bookings with identical
users, seats, totals, and timestamps are not interchangeable if their identities
differ.

Entity questions:

- What makes this the same thing tomorrow?
- When is its identity assigned?
- Is the identity unique within the relevant boundary?
- Which state may change without changing identity?
- When does its lifecycle begin and end?
- Should equality compare identity or every field?

Prefer an explicit, stable identity. Database row numbers are implementation
identifiers unless the domain intentionally exposes them. Natural identifiers
such as an ISBN or email may change, be reused, or have surprising uniqueness
rules; do not assume they are safe entity identity without clarifying scope.

Identity does not mean mutability is unrestricted. An entity should still
expose behaviors that preserve its rules:

```python
class Booking:
    def confirm(self) -> None:
        if self._status is not BookingStatus.PENDING_PAYMENT:
            raise ValueError("Only a pending booking can be confirmed")
        self._status = BookingStatus.CONFIRMED
```

The method says what happened in domain language and prevents callers from
inventing transitions with `booking.status = ...`.

### 1.5 Value objects: meaning through attributes

A value object has no separate business identity. Two values with the same
validated attributes mean the same thing.

Good value objects are usually:

- immutable;
- validated at construction;
- compared structurally;
- safe to share;
- behavior-bearing rather than passive tuples;
- replaced as a whole when a value changes.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class SeatPosition:
    row: str
    number: int

    def __post_init__(self) -> None:
        normalized_row = self.row.strip().upper()
        if not normalized_row:
            raise ValueError("Seat row is required")
        if self.number <= 0:
            raise ValueError("Seat number must be positive")
        object.__setattr__(self, "row", normalized_row)

    @property
    def label(self) -> str:
        return f"{self.row}{self.number}"
```

`SeatPosition("a", 1)` and `SeatPosition("A", 1)` both represent A1 after
normalization. There is no reason to track which instance came first.

Strong value-object candidates include:

- `Money(amount, currency)` rather than a bare float;
- `DateRange(start, end)` rather than unrelated dates;
- `Location(latitude, longitude)` rather than two loose numbers;
- `Percentage` rather than a decimal with unclear bounds;
- `EmailAddress` when normalization and validation matter;
- `SeatPosition(row, number)` when the pair has rules and behavior.

Do not wrap every primitive. Create a value object when it protects a rule,
improves vocabulary, prevents parameter confusion, or centralizes meaningful
behavior.

### 1.6 Records and historical facts

Some objects describe something that happened: a payment attempt, status
change, notification delivery, scan, or ledger entry.

A historical record commonly has an identifier and is therefore technically
identity-bearing, but its important semantic is append-only history. Treating it
as a separate role prevents code from overwriting a failed payment with a
successful retry.

```text
Booking B1
  PaymentAttempt P1: CARD, FAILED, 10:03
  PaymentAttempt P2: UPI, COMPLETED, 10:04
```

This preserves the truth that two attempts occurred. A single mutable field
such as `booking.payment_status = SUCCESS` loses that information.

Questions for a record:

- Must retries create new records?
- Can the fact be corrected, or only superseded?
- Which timestamp and actor are required?
- Is the record part of an invariant or only an audit trail?

Detailed event-driven design is outside this topic. The immediate lesson is to
recognize history rather than accidentally model it as current mutable state.

### 1.7 Assign responsibilities deliberately

A responsibility is either:

- **knowing** something, such as a booking knowing its selected seat IDs;
- **doing** something, such as a booking validating its state transition;
- **deciding** something, such as a pricing policy calculating a total;
- **coordinating** something, such as a service charging and confirming;
- **protecting** something, such as a show-seat boundary preventing a second
  hold.

Use these heuristics:

#### Put behavior beside the state it protects

If `Booking.status` changes only through booking lifecycle rules, `Booking`
should expose `confirm()`, `cancel()`, and `expire()` rather than letting a
service edit the field directly.

#### Give one object one coherent reason to change

`Seat` should change for physical-seat metadata rules. It should not also know
payment processing, email formatting, and database queries.

#### Prefer the information expert

The object with the required information is often a good owner. A `DateRange`
can answer whether it overlaps another range because it owns both endpoints.
A `ScreenSchedule` may reject overlapping shows because it knows the shows on
that screen.

Information alone is not enough if the object lacks authority. A UI may know a
selected seat ID but must not be the source of truth for availability.

#### Keep orchestration thin but meaningful

A use-case coordinator may legitimately:

- resolve entities from IDs;
- ask objects to validate or transition;
- call a policy;
- invoke a payment/notification boundary;
- control operation ordering;
- return a result.

It should not become the only place where every object rule lives.

#### Avoid vague role names

Names such as `Manager`, `Helper`, `Utils`, `Processor`, and `Common` often hide
unrelated responsibilities. Prefer a role that states its decision or workflow:
`PricingPolicy`, `SeatHoldService`, `BookingCancellationService`, or
`PaymentGateway`.

### 1.8 Model relationships beyond "has a"

For each relationship, decide four things:

1. **Cardinality:** one-to-one, one-to-many, or many-to-many.
2. **Direction:** which side needs to navigate to the other?
3. **Ownership:** which object controls changes to the relationship?
4. **Lifecycle:** can either object exist independently?

Example:

| Relationship | Cardinality | Navigation | Lifecycle/ownership decision |
|---|---|---|---|
| Theatre to Screen | 1 to many | Theatre -> Screens | Theatre controls membership in this scope |
| Screen to Seat | 1 to many | Screen -> Seats | Seat belongs to a screen layout |
| Movie to Show | 1 to many | Show -> Movie by ID | Movie and show have separate lifecycles |
| Show to ShowSeat | 1 to many | Show -> ShowSeats | Show inventory exists only for that show |
| Booking to Payment | 1 to many | Booking -> payment IDs | Retries create multiple records |
| User to Booking | 1 to many | Query by user ID | Neither needs a bidirectional object graph |

Do not automatically store references in both directions. Bidirectional
relationships create synchronization work: adding a screen to a theatre must
also update the screen's theatre reference, and every removal must update both.
Use one navigational direction unless a use case genuinely needs both.

#### Object reference or identifier?

Use an object reference when:

- both objects share a small lifecycle/consistency boundary;
- callers repeatedly need the collaborator's behavior;
- the reference does not create an unwieldy graph.

Use an identifier when:

- objects have independent lifecycles;
- a repository or catalog resolves them;
- direct references would create cycles or deep mutable graphs;
- the relationship may cross a persistence or external boundary.

Neither choice is universally superior. State the reason and keep it
consistent. An ID is not a substitute for a missing domain concept, while an
object reference is not proof of good object orientation.

### 1.9 Establish one source of truth

Each mutable business fact needs one authoritative owner.

Bad model:

```text
Seat.is_available
Show.available_seat_ids
Booking.reserved_seat_ids
Screen.available_count
```

Four locations appear to describe the same availability. A failed update can
make them disagree.

Better model:

```text
ShowSeat.status = AVAILABLE | HELD | BOOKED   <- authoritative fact
available seats                              <- derived query
available count                              <- derived query or explicit cache
Booking.seat_ids                             <- which seats this booking selected
```

Duplication is acceptable only when it has a declared synchronization rule,
such as an intentional cache or immutable snapshot. In an interview model,
prefer derivation until performance requirements justify duplication.

For every field, ask:

- Is this authoritative, derived, cached, or historical?
- Who may change it?
- Which other facts must change with it?
- Can it be calculated from existing state?

### 1.10 Model lifecycle as states and transitions

If rules depend on an object's current phase, model a lifecycle explicitly.

Booleans invite impossible combinations:

```text
is_paid = True
is_cancelled = True
is_expired = True
```

An enum narrows the legal state space:

```python
from enum import Enum, auto


class BookingStatus(Enum):
    PENDING_PAYMENT = auto()
    CONFIRMED = auto()
    CANCELLED = auto()
    EXPIRED = auto()
```

Then list transitions before implementing them:

```text
PENDING_PAYMENT --successful payment--> CONFIRMED
PENDING_PAYMENT --user cancellation---> CANCELLED
PENDING_PAYMENT --hold timeout---------> EXPIRED
CONFIRMED       --eligible cancellation-> CANCELLED
```

For each transition, define:

- source state;
- triggering behavior;
- guards and required collaborators;
- state changed together;
- result or failure;
- terminal states;
- idempotency decision.

State machines do not require a State design pattern. An enum and guarded
methods are often enough. Use a named pattern later only when state-specific
behavior becomes complex enough to justify it.

### 1.11 Separate a stable object from contextual state

Many LLD prompts contain a subtle pair:

```text
stable/catalog object + occurrence/context object
```

Examples:

| Stable concept | Contextual concept | Context-specific facts |
|---|---|---|
| `Seat` | `ShowSeat` | Available, held, booked, price |
| `Book` | `BookCopy` / `BookItem` | Barcode, shelf, borrower, status |
| `Room` | `RoomNight` or reservation allocation | Availability for a date |
| `AircraftSeat` | `FlightSeat` | Passenger and status for one flight |
| `Product` | `InventoryItem` | Warehouse, quantity, reorder state |
| `Doctor` | `AppointmentSlot` | Date/time and reservation state |

The test is:

> Can the stable object be in different states in two contexts at the same
> time?

Physical A1 can be booked for the 3 PM show and available for the 7 PM show.
Therefore availability cannot live on the physical seat.

An explicit contextual object also gives identity to the relationship. A
`ShowSeat` is not merely a many-to-many join-table accident; it owns important
behavior and state for the pairing of a show and a seat.

### 1.12 Place invariants at a consistency boundary

An invariant is a rule that must remain true after every completed operation.

Some invariants belong to one object:

- a date range ends after it starts;
- a money amount uses a supported currency;
- a booking contains at least one unique seat ID.

Some span several objects:

- selected show seats must belong to the same show;
- every selected show seat must be available before a hold begins;
- all selected seats are held for the same booking;
- a confirmed booking has a successful payment record;
- two shows on one screen do not overlap.

Place a cross-object rule at the smallest boundary that has both the information
and authority to enforce it atomically in the current design.

```text
single-value rule       -> value object constructor/method
single-entity lifecycle -> entity method
screen schedule rule    -> schedule/catalog boundary
multi-seat hold rule    -> show inventory / seat-hold boundary
payment workflow rule   -> booking use-case coordinator
```

This boundary is sometimes called aggregate-like because one entry point
protects a cluster of related state. For interview LLD, the useful questions are:

- Which objects must be consistent immediately?
- Which object or service is the entry point for changes?
- What can be referenced by ID outside the boundary?
- How large is the state that must change together?

Avoid both extremes:

- independent objects that callers can mutate into contradiction;
- one giant root that owns the entire application and serializes every change.

Concurrency and durable transaction mechanisms come later. Topic 3 identifies
the boundary that those mechanisms must protect.

### 1.13 Distinguish domain service, policy, coordinator, and boundary

These roles are commonly collapsed into one `SomethingService`.

#### Domain behavior on an entity/value

Use when one object naturally owns the rule:

```text
booking.confirm()
date_range.overlaps(other)
money.add(other)
```

#### Policy

Use when the domain contains a named decision or calculation that varies:

```text
pricing_policy.total_for(show, selected_seats)
driver_matching_policy.choose(available_drivers, request)
```

#### Domain service

Use when a domain operation spans multiple concepts and no single entity is a
natural owner:

```text
debt_simplifier.simplify(balances)
fare_calculator.calculate(route, vehicle_type, demand)
```

Keep it stateless where practical. A service is not a place to hide data that
belongs to an entity.

#### Use-case coordinator

Use for application workflow and ordering:

```text
resolve booking
verify hold
ask payment gateway to charge
record attempt
ask seats and booking to confirm
```

#### External boundary

Use a narrow contract for an outside capability:

```text
Clock.now()
PaymentGateway.charge(...)
Notifier.send_confirmation(...)
```

The coordinator depends on the boundary; domain entities should not construct
an SDK client, read a global clock, or send email directly.

### 1.14 Use a repeatable modeling workflow

Use this sequence after the requirements brief is bounded:

1. Write the domain glossary.
2. List primary use cases and failure paths.
3. Extract business verbs and invariants.
4. Identify mutable facts and lifecycle states.
5. Generate candidate concepts.
6. Classify each candidate's role.
7. Choose entity identities and value semantics.
8. Assign behavior and invariant owners.
9. Add cardinality, direction, ownership, and lifecycle to relationships.
10. Identify contextual objects and authoritative state.
11. Mark multi-object consistency boundaries.
12. Narrate critical workflows using object responsibilities.
13. Walk failure paths and verify no partial valid-looking state remains.
14. Apply at least two plausible requirement changes.
15. Remove speculative objects, duplicate facts, and vague services.

The model is ready for the next stage when you can narrate a critical workflow
without saying "then the system updates everything." Name the collaborator and
the responsibility at every meaningful step.

## 2. Recognize

Requirement language often signals a modeling decision:

| Signal in the problem | Likely modeling implication |
|---|---|
| "the same booking later" | Identity-bearing entity |
| "two amounts are equal when..." | Value object |
| "copy", "unit", "instance", "barcode" | Separate physical/instance entity |
| "for this show/date/flight/warehouse" | Contextual association object |
| "must always", "cannot", "only if" | Invariant and enforcement owner |
| "pending, approved, cancelled" | Lifecycle enum and guarded transitions |
| "retry" or "history" | Separate append-only attempt/record |
| "several items succeed together" | Consistency boundary/coordinator |
| "calculate using one of several rules" | Policy/behavior boundary |
| "payment, email, clock, map provider" | External boundary |
| "find/list/search" | Query responsibility, not necessarily an entity method |
| "available count" | Possibly derived state; identify source of truth |
| "different rule by type" | Polymorphic behavior candidate; do not force it yet |

### Warning signals in a proposed model

- Every noun became a class, but important verbs have no owner.
- All domain classes contain only fields and setters.
- One `SystemManager` performs every rule and edits every object.
- Several objects store the same mutable fact.
- Availability is stored on a context-independent catalog object.
- Entity equality compares every mutable field.
- A value object has a generated identity and public setters.
- Status is represented by several booleans with impossible combinations.
- Callers can assign any status directly.
- Every relationship is bidirectional.
- The object graph requires navigating five levels to perform a simple use case.
- A domain object calls a payment SDK, global clock, or database directly.
- A service exists only to forward a call that belongs naturally to an object.
- A single object owns the entire system for the sake of "consistency."
- The model mirrors request JSON or database tables without explaining rules.
- The model contains patterns whose variation requirement has not appeared.

### Decision questions

When unsure about a candidate, ask:

1. What behavior or rule justifies this concept?
2. Does it have identity, value semantics, or historical semantics?
3. What state does it authoritatively own?
4. What is derived rather than stored?
5. Which lifecycle creates and removes it?
6. Which use case needs to navigate this relationship?
7. Can the concept be in different states in different contexts?
8. Which state must change together?
9. Could the responsibility move beside the information it protects?
10. What likely change would affect this object and no unrelated object?

## 3. Model

### 3.1 Running example: bounded Movie Ticket Booking scope

Use this Topic 1-style brief:

> A user searches shows, selects one or more seats for one show, receives a
> five-minute hold, pays, and obtains a confirmed booking. A failed payment may
> be retried before expiry. A pending hold or eligible confirmed booking may be
> cancelled. The same physical seat has independent availability for every
> show. Two users cannot successfully hold the same show seat.

In scope:

- movies, theatres, screens, and physical seats;
- show scheduling and per-show seat inventory;
- booking, hold expiry, payment attempts, confirmation, and cancellation;
- exact monetary values and a supplied source of time.

Out of scope for this topic:

- database schema and durable transactions;
- distributed locking;
- provider webhook reconciliation;
- taxes, coupons, loyalty, food orders, and ticket scanning;
- UML notation.

### 3.2 Vocabulary and candidate classification

| Candidate | Role | Identity/value | Why it exists |
|---|---|---|---|
| `Movie` | Entity/catalog record | `movie_id` | Same content across scheduled shows |
| `Theatre` | Entity | `theatre_id` | Venue with a screen membership lifecycle |
| `Screen` | Entity | `screen_id` within theatre | Owns physical layout/schedule boundary |
| `Seat` | Entity or immutable identified member | `seat_id` within screen | Stable physical chair metadata |
| `SeatPosition` | Value object | row + number | Validated structural position |
| `Show` | Entity/occurrence | `show_id` | One scheduled movie-screen interval |
| `ShowSeat` | Contextual entity | show ID + seat ID | Per-show availability/hold ownership |
| `Booking` | Entity | `booking_id` | User checkout/ticket lifecycle |
| `PaymentAttempt` | Historical entity/record | `payment_id` | Preserve each charge/refund outcome |
| `Money` | Value object | amount + currency | Exact calculation and currency rule |
| `PricingPolicy` | Policy | no business identity | Calculate price under a selected rule |
| `BookingService` | Use-case coordinator | application lifetime only | Sequence multi-object/payment workflow |
| `PaymentGateway` | External boundary | none | Charge/refund without provider coupling |
| `Clock` | External boundary | none | Deterministic current time |

Potential candidates to reject or postpone:

| Candidate | Decision | Reason |
|---|---|---|
| `MovieBookingSystem` | Reject as domain owner | Too broad; hides separate responsibilities |
| `Database` | Keep outside domain model | Persistence mechanism, not domain vocabulary |
| `SeatManager` | Reject | `ShowSeat` and hold coordinator have clearer roles |
| `SearchResult` | Add only if output has behavior/metadata | A list may be enough in this scope |
| `Ticket` | Postpone | Confirmation can return booking details until ticket rules differ |
| `Coupon` | Out of scope | No current rule requires it |
| `Admin` | Treat as actor unless behavior/state is required | Actors do not automatically become classes |

### 3.3 The pivotal split: Seat versus ShowSeat

```text
Screen S1
  Seat A1: physical, regular
      |
      +-- Show 3 PM / A1: BOOKED by B10
      +-- Show 7 PM / A1: AVAILABLE
      `-- Show 10 PM / A1: HELD by B42 until 21:45
```

`Seat` owns stable facts:

- screen membership;
- position;
- seat category;
- accessibility metadata.

`ShowSeat` owns contextual facts:

- which show and physical seat the state describes;
- availability state;
- current hold owner;
- hold expiry;
- optionally show-specific price.

This prevents a booking for one show from affecting every other show on the
same screen.

### 3.4 Responsibility assignment

| Behavior/rule | Owner | Reason |
|---|---|---|
| Validate a seat position | `SeatPosition` | It owns row and number |
| Prevent duplicate positions on a screen | `Screen` | It owns the physical layout |
| Validate show time range | `Show` / `DateRange` | It owns the interval |
| Reject overlapping shows on one screen | Screen schedule/catalog boundary | It knows that screen's scheduled intervals |
| Expose one show seat's lifecycle | `ShowSeat` | It owns status, hold owner, and expiry |
| Reject empty/duplicate booking selection | `Booking` construction | It owns selected seat IDs |
| Validate booking state transition | `Booking` | It owns booking lifecycle |
| Calculate selected-seat total | `PricingPolicy` | Calculation may vary independently |
| Check and hold several seats together | Show-inventory/hold coordinator | Rule spans selected show seats |
| Charge/refund provider | `PaymentGateway` | External capability boundary |
| Preserve each attempt | `PaymentAttempt` plus booking reference | Retry history must not be overwritten |
| Order hold, payment, and confirmation | `BookingService` | Multi-object use case |
| Supply current time | `Clock` | Avoid hidden nondeterministic dependency |

The coordinator may ask a booking and its show seats to transition. It should
not assign their internal fields directly.

### 3.5 Relationships and cardinality

```text
Theatre 1 -------- * Screen
Screen  1 -------- * Seat
Movie   1 -------- * Show
Screen  1 -------- * Show
Show    1 -------- * ShowSeat
Seat    1 -------- * ShowSeat
User    1 -------- * Booking
Show    1 -------- * Booking
Booking 1 -------- * PaymentAttempt
```

Navigation choices for this scope:

- `Theatre` can own its screens because venue use cases navigate that way.
- `Screen` can own physical seats and scheduling membership.
- `Show` can own or resolve its show-seat inventory.
- `Show` may store `movie_id`, `screen_id`, and `theatre_id` rather than deep
  references because those catalog entities have independent lifecycles.
- `Booking` stores user/show/seat IDs and payment IDs; a coordinator resolves
  required objects.
- `User` need not hold a mutable booking list if bookings can be queried by
  `user_id`. That avoids two sources for membership.

The exact reference-versus-ID choice may change with persistence later. The
conceptual relationships and responsibility owners should remain clear.

### 3.6 Identity and authoritative state

| Concept | Identity | Authoritative mutable state |
|---|---|---|
| Seat | `(screen_id, seat_id)` or scoped seat ID | Stable metadata/layout membership |
| Show | `show_id` | Schedule metadata and inventory membership |
| ShowSeat | `(show_id, seat_id)` | Availability, hold owner, expiry |
| Booking | `booking_id` | Lifecycle, selected seats, payment references |
| PaymentAttempt | `payment_id` | Recorded outcome; preferably append-only |

Derived facts:

- available seats are the show seats whose state is `AVAILABLE`;
- available count is the size of that result;
- whether a hold is expired is determined by `held_until` and current time;
- booking history is a query over bookings by `user_id`;
- a booking's successful payment is located from its attempt records.

Do not add mutable `Show.available_count` or `User.booking_ids` unless a
demonstrated requirement justifies the duplicated state and synchronization.

### 3.7 Lifecycle models

Show-seat lifecycle:

```text
AVAILABLE --hold(booking, deadline)--> HELD
HELD      --confirm(owner)-----------> BOOKED
HELD      --cancel/expire(owner)-----> AVAILABLE
BOOKED    --eligible cancel(owner)---> AVAILABLE
```

Booking lifecycle:

```text
PENDING_PAYMENT --successful payment--> CONFIRMED
PENDING_PAYMENT --cancel--------------> CANCELLED
PENDING_PAYMENT --hold timeout--------> EXPIRED
CONFIRMED       --cancel + refund-----> CANCELLED
```

Payment-attempt lifecycle can be modeled as an immutable outcome in this
bounded version:

```text
new charge call -> one COMPLETED or FAILED PaymentAttempt
completed charge -> optional separate refund fact or REFUNDED transition
```

The choice between updating a payment to `REFUNDED` and appending a refund
record is a deliberate audit-model decision, not an automatic answer.

### 3.8 Invariant catalogue

Construction invariants:

- movie duration is positive;
- a screen has no duplicate seat identity or position;
- show end is after start;
- a booking selects at least one unique seat;
- monetary amount and currency are valid.

Relationship invariants:

- a show references an existing movie and screen;
- each physical screen seat appears exactly once in a show's inventory;
- selected show seats belong to one show;
- a booking belongs to one user and one show.

Lifecycle invariants:

- only an available show seat can be held;
- a held/booked show seat has an owning booking ID;
- only the owning booking can confirm or release it;
- a hold deadline is after creation and no later than show start;
- a pending booking can expire; a confirmed booking cannot;
- confirmation requires every selected seat to be held by that booking;
- confirmation follows a successful payment;
- cancellation after show start is rejected in this scope.

Multi-object invariants:

- all selected seats are validated before any is held;
- either every selected seat is held or none is;
- confirmed booking, booked seats, and successful payment agree;
- cancellation/refund ordering cannot report a cancelled booking if the
  required refund failed.

The last group tells Topics 11-12 where synchronization and transaction
boundaries will matter.

### 3.9 Critical interaction narrative

Create a booking:

1. `BookingService` resolves the user, show, and selected show seats.
2. It asks the clock for one `now` value and calculates a hold deadline.
3. The hold boundary releases or rejects expired state according to policy.
4. It validates the entire unique selection before changing any seat.
5. `PricingPolicy` calculates the exact total.
6. A valid pending `Booking` is created.
7. Each `ShowSeat` accepts a hold owned by that booking.
8. The booking is registered and returned.

Confirm a booking:

1. The coordinator resolves the pending booking and selected show seats.
2. It verifies the hold has not expired and every seat is held by this booking.
3. It asks `PaymentGateway` to charge the booking total.
4. It records the payment attempt whether it fails or succeeds.
5. On success, each show seat confirms ownership and becomes booked.
6. The booking becomes confirmed.
7. On a failed charge, the booking and holds remain pending until expiry so the
   user may retry.

Notice the model names who knows, decides, records, and transitions at each
step. Topics 4, 11, and 12 will express the interaction, locking, and durable
atomicity in more detail.

### 3.10 Model review with requirement changes

Apply these changes before accepting the model:

#### Add accessible companion-seat rules

- Stable accessibility metadata belongs to `Seat`.
- The rule that certain positions must be selected together belongs to a seat
  selection/hold policy with access to the selected show seats.
- Availability still belongs to `ShowSeat`.

#### Add weekend and promotional pricing

- Keep base show/seat-type prices with show pricing context.
- Put the varying calculation behind `PricingPolicy`.
- Do not add price-condition branches to `Booking` or `Seat`.

#### Add multiple payment retries

- Preserve each `PaymentAttempt`.
- `Booking` references several attempts.
- A failed attempt does not automatically end a still-valid booking.

#### Add waitlisting when a show is sold out

- Add a `WaitlistEntry` only after clarifying ordering, expiry, and promotion
  rules.
- Do not overload `BookingStatus` with a waitlist phase if a waitlisted request
  does not yet own seats or have the same lifecycle as a booking.

The original responsibility boundaries absorb these changes locally. That is a
better signal than the number of classes or patterns in the design.

## 4. Implement

The following reference model demonstrates ownership and transitions. It is
intentionally in-memory and single-threaded. The boundary is explicit so Topic
11 can later add synchronization without relocating the domain rules.

### 4.1 Value object and lifecycle types

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto


@dataclass(frozen=True, order=True)
class ShowSeatId:
    show_id: str
    seat_id: str

    def __post_init__(self) -> None:
        if not self.show_id.strip() or not self.seat_id.strip():
            raise ValueError("Show and seat IDs are required")


class ShowSeatStatus(Enum):
    AVAILABLE = auto()
    HELD = auto()
    BOOKED = auto()


class BookingStatus(Enum):
    PENDING_PAYMENT = auto()
    CONFIRMED = auto()
    CANCELLED = auto()
    EXPIRED = auto()
```

`ShowSeatId` is a value: the pairing defines it. `ShowSeat` and `Booking` below
are identity-bearing objects whose state changes.

### 4.2 ShowSeat owns contextual availability

```python
@dataclass(eq=False)
class ShowSeat:
    identity: ShowSeatId
    _status: ShowSeatStatus = field(
        default=ShowSeatStatus.AVAILABLE,
        init=False,
        repr=False,
    )
    _owner_booking_id: str | None = field(default=None, init=False, repr=False)
    _held_until: datetime | None = field(default=None, init=False, repr=False)

    @property
    def status(self) -> ShowSeatStatus:
        return self._status

    @property
    def owner_booking_id(self) -> str | None:
        return self._owner_booking_id

    @property
    def held_until(self) -> datetime | None:
        return self._held_until

    def is_expired_at(self, now: datetime) -> bool:
        return (
            self._status is ShowSeatStatus.HELD
            and self._held_until is not None
            and now >= self._held_until
        )

    def release_if_expired(self, now: datetime) -> bool:
        if not self.is_expired_at(now):
            return False
        self._make_available()
        return True

    def ensure_available(self, now: datetime) -> None:
        self.release_if_expired(now)
        if self._status is not ShowSeatStatus.AVAILABLE:
            raise ValueError(f"Seat {self.identity.seat_id} is not available")

    def hold(self, booking_id: str, until: datetime, now: datetime) -> None:
        if not booking_id.strip():
            raise ValueError("Booking ID is required")
        if until <= now:
            raise ValueError("Hold deadline must be in the future")
        self.ensure_available(now)
        self._status = ShowSeatStatus.HELD
        self._owner_booking_id = booking_id
        self._held_until = until

    def ensure_confirmable_by(self, booking_id: str, now: datetime) -> None:
        if self.is_expired_at(now):
            raise ValueError(f"Hold for seat {self.identity.seat_id} expired")
        if self._status is not ShowSeatStatus.HELD:
            raise ValueError(f"Seat {self.identity.seat_id} is not held")
        if self._owner_booking_id != booking_id:
            raise ValueError("Only the hold owner can confirm this seat")

    def confirm(self, booking_id: str, now: datetime) -> None:
        self.ensure_confirmable_by(booking_id, now)
        self._status = ShowSeatStatus.BOOKED
        self._held_until = None

    def release(self, booking_id: str) -> None:
        if self._status is ShowSeatStatus.AVAILABLE:
            return
        if self._owner_booking_id != booking_id:
            raise ValueError("Only the owning booking can release this seat")
        self._make_available()

    def _make_available(self) -> None:
        self._status = ShowSeatStatus.AVAILABLE
        self._owner_booking_id = None
        self._held_until = None
```

The three related fields cannot be edited independently by callers. Every
public transition preserves these rules:

```text
AVAILABLE -> no owner, no deadline
HELD      -> owner and future deadline
BOOKED    -> owner, no hold deadline
```

Keeping the owner after confirmation allows a cancellation workflow to prove
which booking may release the booked seat.

### 4.3 Booking owns selection and booking lifecycle

```python
@dataclass(eq=False)
class Booking:
    booking_id: str
    user_id: str
    show_id: str
    seat_ids: tuple[str, ...]
    created_at: datetime
    hold_expires_at: datetime
    _status: BookingStatus = field(
        default=BookingStatus.PENDING_PAYMENT,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not self.booking_id.strip() or not self.user_id.strip():
            raise ValueError("Booking and user IDs are required")
        if not self.show_id.strip():
            raise ValueError("Show ID is required")
        if not self.seat_ids:
            raise ValueError("A booking requires at least one seat")
        if len(set(self.seat_ids)) != len(self.seat_ids):
            raise ValueError("A booking cannot contain duplicate seats")
        if self.hold_expires_at <= self.created_at:
            raise ValueError("Hold expiry must be after booking creation")

    @property
    def status(self) -> BookingStatus:
        return self._status

    def ensure_pending(self) -> None:
        if self._status is not BookingStatus.PENDING_PAYMENT:
            raise ValueError("Booking is not pending payment")

    def confirm(self) -> None:
        self.ensure_pending()
        self._status = BookingStatus.CONFIRMED

    def cancel(self) -> None:
        if self._status not in {
            BookingStatus.PENDING_PAYMENT,
            BookingStatus.CONFIRMED,
        }:
            raise ValueError("Booking cannot be cancelled from its current state")
        self._status = BookingStatus.CANCELLED

    def expire(self, now: datetime) -> None:
        self.ensure_pending()
        if now < self.hold_expires_at:
            raise ValueError("A live booking cannot expire")
        self._status = BookingStatus.EXPIRED
```

Construction rejects an invalid selection once. Lifecycle methods reject
illegal transitions wherever the booking is used. `eq=False` is deliberate for
both entities: Python object identity is used instead of generated field-wise
equality. A repository may enforce unique domain IDs; alternatively, an entity
can implement equality by an immutable identity explicitly.

### 4.4 A boundary coordinates a multi-seat invariant

```python
class SeatHoldService:
    """Single-threaded reference boundary; synchronization is Topic 11."""

    def __init__(self, inventory: dict[ShowSeatId, ShowSeat]) -> None:
        self._inventory = dict(inventory)

    def hold(
        self,
        booking_id: str,
        show_id: str,
        seat_ids: tuple[str, ...],
        now: datetime,
        until: datetime,
    ) -> tuple[ShowSeat, ...]:
        if not seat_ids:
            raise ValueError("Select at least one seat")
        if len(set(seat_ids)) != len(seat_ids):
            raise ValueError("Seat selection contains duplicates")

        selected = tuple(
            self._seat(ShowSeatId(show_id, seat_id)) for seat_id in seat_ids
        )

        # Validate the complete selection before the first business mutation.
        for show_seat in selected:
            show_seat.ensure_available(now)

        for show_seat in selected:
            show_seat.hold(booking_id, until, now)
        return selected

    def confirm(
        self,
        booking_id: str,
        show_id: str,
        seat_ids: tuple[str, ...],
        now: datetime,
    ) -> None:
        selected = tuple(
            self._seat(ShowSeatId(show_id, seat_id)) for seat_id in seat_ids
        )

        # Again, validate every participant before changing any participant.
        for show_seat in selected:
            show_seat.ensure_confirmable_by(booking_id, now)
        for show_seat in selected:
            show_seat.confirm(booking_id, now)

    def release(
        self,
        booking_id: str,
        show_id: str,
        seat_ids: tuple[str, ...],
    ) -> None:
        selected = tuple(
            self._seat(ShowSeatId(show_id, seat_id)) for seat_id in seat_ids
        )
        for show_seat in selected:
            if (
                show_seat.status is not ShowSeatStatus.AVAILABLE
                and show_seat.owner_booking_id != booking_id
            ):
                raise ValueError("Booking does not own the complete selection")
        for show_seat in selected:
            show_seat.release(booking_id)

    def _seat(self, identity: ShowSeatId) -> ShowSeat:
        try:
            return self._inventory[identity]
        except KeyError as error:
            raise ValueError(f"Unknown show seat: {identity}") from error
```

`SeatHoldService` exists because the all-selected-seats rule belongs to no one
`ShowSeat`. Its responsibility is narrow: coordinate the inventory boundary.
It does not calculate price, charge cards, or send notifications.

Calling `ensure_available()` may release an individually expired hold. In this
single-threaded model that normalization happens before new holds. A durable,
concurrent implementation must protect the full selection with an appropriate
lock or transaction; recognizing this boundary is the Topic 3 outcome.

### 4.5 Use-case coordination should delegate domain decisions

The outer booking workflow can now read like domain language:

```python
class BookingCheckout:
    def confirm(self, booking_id: str, payment_method: str) -> None:
        booking = self._bookings.get(booking_id)
        booking.ensure_pending()
        now = self._clock.now()

        self._holds.ensure_live(booking, now)
        payment = self._payment_gateway.charge(
            booking.booking_id,
            booking.total,
            payment_method,
        )
        self._payments.add(payment)

        if payment.succeeded:
            self._holds.confirm_for(booking, now)
            booking.confirm()
```

This is a focused sketch, not a standalone implementation. The coordinator
controls ordering, but each collaborator owns its decision:

- booking validates its lifecycle;
- hold boundary validates seat ownership/expiry;
- gateway performs the external charge;
- payment store preserves the attempt;
- hold boundary confirms selected seats;
- booking transitions itself.

If a failed payment remains retryable, the final `if` intentionally leaves the
booking pending. That rule should be explicit in the requirements and tests.

## 5. Test

Domain-model tests prove more than field values. They prove construction rules,
identity/value semantics, allowed transitions, rejected transitions, ownership,
and multi-object consistency.

### 5.1 Test valid and invalid construction

```python
def test_show_seat_id_requires_both_parts(self) -> None:
    with self.assertRaises(ValueError):
        ShowSeatId("show-1", "")


def test_booking_requires_unique_non_empty_selection(self) -> None:
    with self.assertRaisesRegex(ValueError, "at least one"):
        Booking("b1", "u1", "show-1", (), self.now, self.until)

    with self.assertRaisesRegex(ValueError, "duplicate"):
        Booking("b1", "u1", "show-1", ("A1", "A1"), self.now, self.until)
```

### 5.2 Test contextual independence

```python
def test_same_physical_seat_has_independent_state_per_show(self) -> None:
    afternoon = ShowSeat(ShowSeatId("3-pm", "A1"))
    evening = ShowSeat(ShowSeatId("7-pm", "A1"))

    afternoon.hold("b1", self.until, self.now)

    self.assertIs(ShowSeatStatus.HELD, afternoon.status)
    self.assertIs(ShowSeatStatus.AVAILABLE, evening.status)
```

This test catches the most important modeling error: availability placed on the
physical seat.

### 5.3 Test transition guards and ownership

```python
def test_only_hold_owner_can_confirm(self) -> None:
    seat = ShowSeat(ShowSeatId("show-1", "A1"))
    seat.hold("owner-booking", self.until, self.now)

    with self.assertRaisesRegex(ValueError, "hold owner"):
        seat.confirm("another-booking", self.now)

    self.assertIs(ShowSeatStatus.HELD, seat.status)
    self.assertEqual("owner-booking", seat.owner_booking_id)


def test_expired_hold_cannot_be_confirmed(self) -> None:
    seat = ShowSeat(ShowSeatId("show-1", "A1"))
    seat.hold("b1", self.until, self.now)

    with self.assertRaisesRegex(ValueError, "expired"):
        seat.confirm("b1", self.until)

    self.assertIs(ShowSeatStatus.HELD, seat.status)
```

The failed operation must preserve the prior valid state. A separate expiry
workflow may then release the expired hold.

### 5.4 Test all-or-none validation

```python
def test_failed_multi_seat_hold_changes_no_available_seat(self) -> None:
    first = ShowSeat(ShowSeatId("show-1", "A1"))
    second = ShowSeat(ShowSeatId("show-1", "A2"))
    service = SeatHoldService(
        {first.identity: first, second.identity: second}
    )
    second.hold("existing", self.until, self.now)

    with self.assertRaisesRegex(ValueError, "not available"):
        service.hold(
            "new-booking",
            "show-1",
            ("A1", "A2"),
            self.now,
            self.until,
        )

    self.assertIs(ShowSeatStatus.AVAILABLE, first.status)
    self.assertIs(ShowSeatStatus.HELD, second.status)
    self.assertEqual("existing", second.owner_booking_id)
```

If A1 changed before A2 failed, responsibility assignment or mutation ordering
would be wrong even in a single-threaded implementation.

### 5.5 Test booking lifecycle

```python
def test_booking_cannot_confirm_after_cancellation(self) -> None:
    booking = Booking(
        "b1",
        "u1",
        "show-1",
        ("A1",),
        self.now,
        self.until,
    )
    booking.cancel()

    with self.assertRaisesRegex(ValueError, "not pending"):
        booking.confirm()

    self.assertIs(BookingStatus.CANCELLED, booking.status)
```

### Domain-model test checklist

- [ ] Every value object accepts valid boundary values and rejects invalid ones.
- [ ] Equal values compare equally and hash safely when hashable.
- [ ] Entities remain identifiable as state changes.
- [ ] Every constructor establishes its invariants.
- [ ] Every allowed state transition has a positive test.
- [ ] Every forbidden transition has a negative test.
- [ ] Failed operations leave prior state valid.
- [ ] Only the owning object/booking may change protected state.
- [ ] Contextual states are independent across contexts.
- [ ] Derived state agrees with its source of truth.
- [ ] Duplicate selections and relationships are rejected.
- [ ] Multi-object validation happens before mutation.
- [ ] Retry/history behavior preserves separate records.
- [ ] Time-dependent behavior uses a controlled clock.
- [ ] At least one change request is implemented without unrelated rewrites.

## 6. Adapt

A model is not judged only by its first happy path. Apply a realistic change
and observe where it travels.

### Adaptation A: seat-specific accessibility rules

Requirement:

> A wheelchair space and its companion seat must be booked together unless the
> companion seat has already been sold independently under an allowed policy.

Likely impact:

- add stable grouping/accessibility metadata to the physical layout;
- introduce or extend a selection policy used by the multi-seat hold boundary;
- add scenario tests for valid pairs, incomplete pairs, and unavailable pairs;
- do not put the rule in payment or user classes.

### Adaptation B: different prices for every show seat

Requirement:

> The same physical seat category may have a different base price for each
> show.

Likely impact:

- price context belongs to `ShowSeat` or a show-owned price table;
- physical `Seat` retains its category, not a final sale price;
- `PricingPolicy` consumes contextual prices;
- existing availability ownership remains unchanged.

### Adaptation C: group booking with maximum ten seats

Requirement:

> A single booking can contain up to ten unique seats, and the selection must
> succeed or fail as one unit.

Likely impact:

- booking construction protects the size/uniqueness rule;
- the hold boundary protects all-or-none availability;
- concurrency/transaction protection covers the complete selection;
- no `GroupBooking` subclass is needed unless its lifecycle truly differs.

### Adaptation D: partial refund for one attendee

This change challenges the original model:

- Can one booking seat be cancelled independently?
- Does a booking line need its own lifecycle and price snapshot?
- Is the original `seat_ids` tuple sufficient?
- Does one refund record reference a booking or booking item?
- What happens to booking status after some but not all seats are cancelled?

The likely new concept is a `BookingItem` or `Ticket` with per-seat price and
status. This is a justified new object because responsibility and lifecycle have
changed, not because every booking system must begin with one.

### Adaptation E: a waitlist

Clarify before adding classes:

- Is waitlisting per show, seat category, or exact seat?
- Is ordering first-come-first-served or priority based?
- How long does a promoted offer remain valid?
- Does promotion create a booking or a separate offer?
- Can one user hold several waitlist positions?

Only after those answers can `WaitlistEntry`, `PromotionOffer`, and an ordering
policy receive precise responsibilities.

### Adaptation review

For every change, state:

1. Which domain term is new or redefined?
2. Which invariant changes?
3. Which object owns the new state?
4. Which behavior owns the new rule?
5. Which consistency boundary changes?
6. Which existing collaborators remain untouched?
7. Which tests prove the change and protect old behavior?

If a small change edits nearly every class, the model probably grouped
responsibilities by technical layer or prompt nouns rather than reasons to
change.

## Common mistakes

### Turning every noun into a class

Prompt nouns produce candidates, not a final model. Retain a class only when it
has identity, value semantics, behavior, owned state, or a meaningful boundary.

### Starting from a database schema

Tables can reveal data but rarely reveal behavior ownership. Model invariants
and workflows first; persistence mapping comes later.

### Copying request/response DTOs into the domain

Transport payloads optimize serialization and client contracts. Domain objects
optimize valid behavior. They may share fields without being the same model.

### Anemic entities and a god service

If every entity exposes setters and `BookingManager` contains every rule, the
model has state containers but no responsibility ownership. Move lifecycle and
single-object invariants beside their state.

### Putting availability on the stable object

`Seat.is_available`, `Room.is_booked`, or `Book.is_borrowed` is wrong when state
varies by show, date range, or physical copy. Introduce the contextual or
instance concept.

### Confusing entity and value equality

Two equal money values are interchangeable. Two bookings with identical fields
are not. State the semantics before relying on generated dataclass equality.

### Duplicating the source of truth

Mutable availability lists, counts, booleans, and booking fields drift apart.
Choose one authoritative fact and derive other views unless a synchronization
contract is explicit.

### Exposing public mutable state

Direct `status` assignment allows illegal transitions. Encapsulate state and
provide domain-named methods with guards.

### Boolean explosion

Several lifecycle booleans permit contradictory combinations. Use one explicit
state and a documented transition map.

### Relationships in both directions by default

Bidirectional collections create update and lifecycle complexity. Store only
the navigation required by use cases.

### Mixing identifiers and references randomly

Inconsistent choices create deep graphs in some paths and repeated resolution
in others. Define boundary and navigation reasons, then use a consistent model.

### Making the consistency boundary too large

One root owning users, shows, bookings, payments, and every theatre is hard to
reason about and later hard to lock or persist. Group only state that must be
consistent together.

### Creating a service for every method

`BookingConfirmationService` is not automatically better than
`booking.confirm()`. Use a service when responsibility spans objects or an
external workflow and has no natural single-object owner.

### Letting domain entities call infrastructure

A booking should not construct a payment SDK, issue SQL, call `datetime.now()`,
or send email. Use explicit boundaries and coordinate them outside the entity.

### Modeling category variation with inheritance too early

`PremiumSeat`, `RegularSeat`, and `ReclinerSeat` subclasses add little when only
category and price differ. An enum/value plus policy may be enough. Add
polymorphism when behavior genuinely differs.

### Forcing design patterns

Pattern names do not repair unclear responsibilities. First identify variation,
ownership, and collaboration; later topics name structures that solve repeated
forces.

### Ignoring time, failure, and retries

Expiry, payment failure, cancellation, and retry often reveal missing states
and records. Walk them before accepting the happy-path model.

### Over-modeling possible futures

Do not create `Coupon`, `LoyaltyTier`, `FoodOrder`, `TicketScanner`, and event
hierarchies without a requirement. Preserve clear extension points through
cohesive responsibilities, not speculative classes.

## Existing repository examples

Use these implementations to compare modeling choices with working behavior.

### Primary example: Movie Ticket Booking

- The [solution guide](../../solutions/movie-ticket-booking/README.md) explains
  vocabulary, `Seat` versus `ShowSeat`, responsibilities, relationships, state
  machines, and critical workflows.
- [`seat.py`](../../solutions/movie-ticket-booking/models/seat.py) models stable
  physical-seat metadata as an immutable dataclass.
- [`show.py`](../../solutions/movie-ticket-booking/models/show.py) stores
  per-show `ShowSeat` availability, owner, and deadline.
- [`booking.py`](../../solutions/movie-ticket-booking/models/booking.py) keeps
  booking identity, selected IDs, total, expiry, and payment references.
- [`booking_service.py`](../../solutions/movie-ticket-booking/services/booking_service.py)
  coordinates multi-object rules, time, pricing, payment, and locking.
- [The tests](../../solutions/movie-ticket-booking/tests/test_movie_ticket_booking.py)
  prove contextual independence, hold expiry, retry, cancellation, and one
  winner under contention.

Review critically: the working implementation uses public mutable dataclass
fields for some state transitions because it is intentionally compact. Refactor
`ShowSeat` and `Booking` transitions behind guarded methods as a Topic 3
exercise, while preserving all tests. The service should continue coordinating
cross-object workflow rather than absorbing the guards again.

### Catalog object versus physical instance

- [`Book`](../../solutions/library-management/models/book.py) describes a title
  and ISBN.
- [`BookItem`](../../solutions/library-management/models/book_item.py) describes
  a barcoded physical copy with shelf and circulation state.
- [`Loan`](../../solutions/library-management/models/loan.py) records one
  member's borrowing interval for one copy.

Ask whether status changes should move behind `BookItem` and `Loan` methods and
whether direct object references or IDs best fit the solution's current
boundary.

### Stable room versus dated reservation

- [`Room`](../../solutions/hotel-management/models/room.py) holds stable room
  metadata and service status.
- [`Booking`](../../solutions/hotel-management/models/booking.py) owns date
  range, selected room IDs, hold deadline, financial state, and stay lifecycle.

Notice that `Room.status` means whether the room is in service, not whether it
is free for every possible date. Availability for an interval must be derived
from room service state and overlapping bookings.

### Values, records, and derived balances

- [`Expense`](../../solutions/splitwise/models/expense.py) is an immutable
  recorded expense with a stable ID.
- [`Split`](../../solutions/splitwise/models/split.py) is an immutable
  per-user value within that expense.
- [`Balance`](../../solutions/splitwise/models/balance.py) represents a directed
  debtor-creditor amount that can be derived/updated from the expense ledger.

Identify which facts are historical source records and which are projections.
Do not let both become independently editable sources of truth.

### Value object inside an entity

- [`Location`](../../solutions/cab-booking/models/location.py) is immutable,
  structurally equal, and validates coordinates.
- [`Ride`](../../solutions/cab-booking/models/ride.py) is identity-bearing and
  changes through a request/assignment/trip lifecycle.

This is a clean entity/value contrast. A useful refactoring exercise is to hide
the ride's transition fields behind lifecycle methods.

## Practice exercises

Complete the core exercises without copying an existing solution. Each has an
objective result or scoring key.

### Exercise 1 - Core: fixed role-classification gate

Classify each concept using exactly one primary role:

`entity`, `value`, `record`, `policy`, `domain service`, `coordinator`, or
`external boundary`.

1. A booking tracked by `booking_id` as its status changes.
2. Latitude and longitude validated and compared by coordinates.
3. One failed card charge that must remain in history after a UPI retry.
4. A rule selecting the cheapest eligible shipping method.
5. An operation simplifying debts across many user balances.
6. An object sequencing seat hold, payment, confirmation, and notification.
7. A contract that supplies current time.
8. A physical library copy identified by barcode.
9. A date interval compared by start and end.
10. A contract that charges an external provider.
11. A show identified over rescheduling and cancellation.
12. A record of a status change with actor and timestamp.

Scoring key:

1. entity;
2. value;
3. record;
4. policy;
5. domain service;
6. coordinator;
7. external boundary;
8. entity;
9. value;
10. external boundary;
11. entity;
12. record.

Score one point each. Questions 1, 2, 6, 7, 8, and 10 are critical.

### Exercise 2 - Core: Book, BookCopy, and Loan

Requirements:

- A title is identified by ISBN and has title/author metadata.
- A library owns several physical copies of one title.
- Each copy has a unique barcode and shelf location.
- Only an available copy can be checked out.
- A loan belongs to one member and one copy, has a due date, and may be returned
  once.
- Two titles with the same metadata but different ISBNs are distinct.

Produce:

1. glossary;
2. role classification;
3. identities and value semantics;
4. cardinalities/directions;
5. invariant owners;
6. copy and loan state transitions;
7. one interaction narrative;
8. eight tests.

Ten-point scoring key:

- 1 point: separate title from physical copy.
- 1 point: copy identity is barcode; title identity is ISBN in this scope.
- 1 point: loan is a separate identity-bearing/history concept.
- 1 point: title 1-to-many copies and copy 1-to-many loans over time.
- 1 point: current availability is not stored independently on title.
- 1 point: copy/checkout boundary prevents two active loans.
- 1 point: loan protects due/return lifecycle.
- 1 point: one source of truth for active borrowing state is declared.
- 1 point: failure paths preserve state.
- 1 point: tests cover duplicate checkout, return, and invalid dates.

Required decisions: title/copy separation, barcode identity, and no
title-level borrowed flag.

### Exercise 3 - Core: Meeting Room Scheduler model

Requirements:

- An office has rooms with capacity and equipment.
- An employee reserves one room for a time interval.
- Confirmed reservations for the same room cannot overlap.
- A reservation can be cancelled before it begins.
- Searches filter rooms by capacity, equipment, and interval.
- Room maintenance blocks availability for an interval.

Without code, produce a one-page model containing:

- glossary and scope;
- candidates classified by role;
- entity identity and value objects;
- relationship cardinality/direction;
- reservation lifecycle;
- invariant/responsibility table;
- booking and cancellation narratives;
- ten test scenarios.

Twelve-point rubric:

- 2: `TimeRange` value validates endpoints and owns overlap behavior.
- 2: room, reservation, employee, and maintenance identities are explicit.
- 2: overlap is checked at a room schedule/reservation boundary.
- 1: capacity/equipment are stable room facts.
- 1: availability is derived for an interval, not one room boolean.
- 1: cancellation is a guarded transition.
- 1: search is separated from reservation mutation.
- 1: relationship navigation is justified.
- 1: failure tests preserve the prior schedule.

Critical requirements: no room-level `is_available` boolean, `TimeRange`
overlap ownership, and same-room overlap enforcement.

### Exercise 4 - Core: Splitwise responsibility audit

Model these facts:

- An immutable expense record says who paid, total amount, split type, and
  each participant's owed share.
- The sum of shares must equal the expense total.
- A settlement reduces debt but does not rewrite old expenses.
- Pairwise balances are query projections from expenses and settlements.

Answer:

1. Which concepts have identity?
2. Which concepts are values or historical records?
3. Who validates split totals?
4. Which facts are sources and which are projections?
5. Where does settlement behavior belong?
6. What must never be updated when a settlement occurs?
7. What six tests prove the ownership decisions?

Expected core decisions:

- expense and settlement histories are preserved;
- money/split amounts have value semantics;
- the expense creation boundary validates participant and total invariants;
- balances are not an independently editable competing ledger;
- settlement appends a fact rather than rewriting prior expenses.

### Exercise 5 - Core: contextual-state recognition

For each pair, identify the stable concept, contextual/instance concept, and the
state that must not live on the stable concept:

1. aircraft seat / seat on flight;
2. hotel room / room availability for date range;
3. product / stock in warehouse;
4. course / semester offering;
5. doctor / appointment slot;
6. vehicle model / rentable vehicle;

Expected answer:

| Stable | Contextual/instance | Misplaced state to move |
|---|---|---|
| Aircraft seat/layout | FlightSeat | passenger/availability for flight |
| Room | Reservation or RoomNight | booked status for date |
| Product | InventoryItem/StockPosition | quantity for warehouse |
| Course | CourseOffering | term, instructor, enrollment |
| Doctor | AppointmentSlot | dated availability/reservation |
| Vehicle model | Vehicle | condition, location, rental state |

Score one point per complete row. Rows 1-3 are critical.

### Exercise 6 - Core: refactor a god coordinator

Given a `BookingManager` that:

- validates money;
- directly sets booking and seat status;
- computes weekend price;
- calls `datetime.now()`;
- constructs a payment SDK;
- sends email;
- stores all users, theatres, shows, and bookings;

produce a responsibility refactoring. For every moved responsibility, name:

1. its new owner;
2. the state/information that justifies that owner;
3. the contract between coordinator and owner;
4. the test that becomes possible or simpler.

Required moves:

- money validation/calculation to value/policy roles;
- lifecycle guards to domain objects;
- seat selection invariant to the show inventory/hold boundary;
- time, payment, and notification to injected external boundaries;
- catalog/query concerns away from checkout orchestration.

Do not create one replacement service per line. The result should contain
cohesive responsibilities, not more suffixes.

### Exercise 7 - Core and timed: Vending Machine

In 40 minutes, model and implement the core of a vending machine:

- The machine has slots; a slot refers to a product and owns stock quantity.
- A customer selects a slot and inserts supported denominations.
- Exact product price is charged and change is returned when possible.
- Purchase fails without changing stock or retained money when funds or change
  are insufficient.
- An operator can refill a slot.
- One active purchase session exists in this bounded version.
- Cancellation returns inserted money.

Deliver:

- first 8 minutes: glossary, invariants, roles, state, relationships;
- next 25 minutes: runnable domain core;
- final 7 minutes: tests and narration.

Fifteen-point rubric:

- 2: `Money`/denomination uses exact validated values.
- 2: product catalog data is separate from slot stock.
- 2: session/machine lifecycle prevents invalid ordering.
- 2: stock and retained-money facts each have one owner.
- 2: purchase validates funds/change/stock before mutation.
- 1: change calculation has a cohesive owner.
- 1: cancellation preserves conservation of money.
- 1: no payment/stock state is represented by contradictory booleans.
- 1: external display/input concerns remain outside domain rules.
- 1: tests cover success and three failures with unchanged state.

Pass at 12/15 with full points on product/slot separation and validate-before-
mutate.

### Exercise 8 - Core: reference-model implementation

Put the Topic 3 `ShowSeatId`, `ShowSeat`, `Booking`, and `SeatHoldService` in one
module. Write a `unittest` suite that covers:

1. value equality and hashing for `ShowSeatId`;
2. invalid ID construction;
3. empty/duplicate booking selection;
4. available -> held -> booked;
5. expired hold rejection and release;
6. wrong owner confirmation/release;
7. contextual independence across shows;
8. all-or-none two-seat hold failure;
9. invalid booking transitions;
10. successful cancellation/expiry paths.

Required result: all tests pass, domain fields cannot be assigned through the
public interface, and failed operations preserve prior valid state.

### Exercise 9 - Timed change-pressure drill

Take your Meeting Room model from Exercise 3. In 15 minutes, adapt it to:

> Recurring weekly reservations may create at most eight occurrences. If any
> occurrence conflicts, the entire recurring request fails without adding any
> reservation.

Expected impact:

- recurrence request/rule is distinct from one confirmed reservation;
- a recurrence expander produces intervals;
- the room schedule boundary validates all occurrences before mutation;
- existing `TimeRange.overlaps()` remains unchanged;
- failure leaves no partial recurrence;
- tests cover conflict on first, middle, and final occurrence.

Pass when the change is localized and all original tests still pass.

## Interview self-check

Answer without notes. Give one point per complete answer.

1. What makes a model a domain model rather than a class list?
2. Why are nouns only candidates?
3. What is the difference between identity and structural equality?
4. Give two entity examples and their identities.
5. Give two value-object examples and their validation rules.
6. Why are value objects usually immutable?
7. When should a historical attempt be a separate record?
8. What are knowing, doing, deciding, coordinating, and protecting
   responsibilities?
9. What does "put behavior beside state" mean?
10. When is an information expert not authorized to change state?
11. What four decisions define a relationship?
12. When would you store an ID rather than an object reference?
13. Why are bidirectional references costly?
14. What is a source of truth?
15. Distinguish authoritative, derived, cached, and historical state.
16. Why are several lifecycle booleans dangerous?
17. What belongs in a state-transition definition?
18. Why must `Seat` and `ShowSeat` be separate?
19. Give two other stable/contextual pairs.
20. What is a single-object invariant?
21. What is a cross-object invariant?
22. What is the smallest consistency boundary for a multi-seat hold?
23. How does a policy differ from an entity method?
24. How does a domain service differ from a use-case coordinator?
25. What belongs behind an external boundary?
26. Why validate a complete selection before mutation?
27. How can failure flows reveal missing concepts?
28. How do change requests evaluate a model?
29. Name three signs of a god service.
30. When should you reject a candidate class?

Core questions: 3, 9, 14, 16, 18, 21, 22, 24, and 26.

Expected answer points:

1. It represents relevant vocabulary, identity, state, behavior, rules, and
   collaboration for a bounded problem.
2. Nouns do not prove identity, behavior, or owned rules; verbs/invariants
   reveal responsibility.
3. Identity preserves the same entity through change; structural equality
   makes equal-attribute values interchangeable.
4. Any two valid examples with explicit stable identities.
5. Any two validated values with complete construction rules.
6. Immutability makes sharing/equality/hashing predictable and preserves value
   meaning.
7. When retry/audit/history must not be overwritten.
8. Respectively: own facts, perform behavior, choose rule, sequence workflow,
   preserve invariants.
9. The object that owns protected state exposes guarded behavior to change it.
10. Knowing a fact does not grant authority; UI/cache/read model examples are
   acceptable.
11. Cardinality, direction, ownership, lifecycle.
12. Independent lifecycle/boundary, cycle avoidance, or later resolution.
13. Both sides must remain synchronized and can form cycles/deep graphs.
14. The one authoritative owner from which competing representations derive.
15. Source, computation, synchronized optimization, and past fact.
16. They permit contradictory combinations and obscure legal transitions.
17. Source, trigger, guard, joint changes, result/failure, terminal/idempotency.
18. Physical seat state is stable while availability differs by show.
19. Any correct stable/context pair.
20. A rule one object can enforce from its own state.
21. A rule requiring coordinated knowledge/change across objects.
22. The selected show inventory/seat-hold boundary, protected as one operation.
23. Policy represents a varying decision; an entity method protects behavior
   naturally owned by that entity.
24. Domain service performs a domain operation with no natural object owner;
   coordinator sequences use case and external interactions.
25. Time, payment, notification, storage/provider or similar outside capability.
26. To prevent partial state if a later participant fails.
27. Expiry/retry/cancellation exposes lifecycle, ownership, or history needs.
28. A good model localizes the new rule and preserves unrelated collaborators.
29. Any three: all rules, all stores, direct field edits, external calls,
   unrelated calculations, vague name.
30. When it has no necessary identity, value, behavior, state, record, or
   boundary in current scope.

Score at least 26/30 and answer every core question correctly.

## Quick review checklist

- [ ] I begin from bounded requirements and consistent domain vocabulary.
- [ ] I discover responsibilities from verbs, rules, state, and failures.
- [ ] Every candidate has a justified role or is removed/postponed.
- [ ] Entity identity remains stable through state changes.
- [ ] Value objects are validated, immutable where practical, and structural.
- [ ] Retry/audit facts are preserved as history when required.
- [ ] Each mutable fact has one authoritative owner.
- [ ] Derived facts are not competing mutable sources of truth.
- [ ] Behavior is placed beside the state/invariant it protects.
- [ ] Coordinators delegate domain decisions to cohesive collaborators.
- [ ] Vague manager/helper classes have been removed or renamed by role.
- [ ] Every relationship states cardinality, direction, ownership, and lifetime.
- [ ] Identifier/reference choices are deliberate and consistent.
- [ ] Bidirectional navigation exists only for a demonstrated use case.
- [ ] Lifecycle states and legal transitions are explicit.
- [ ] Failed transitions preserve the prior valid state.
- [ ] Stable/catalog objects are separated from contextual/instance state.
- [ ] Cross-object invariants have a clear consistency boundary.
- [ ] External time, payment, and notification capabilities use narrow contracts.
- [ ] Critical happy, alternate, and failure workflows can be narrated by owner.
- [ ] The model survives at least two plausible changes without broad rewrites.
- [ ] Speculative classes and premature patterns are absent.
- [ ] Tests prove ownership, transitions, contextual independence, and
  all-or-none behavior.

## Mastery gate

Topic 3 is complete only when all of the following are true:

- [ ] I score at least 26 out of 30 on the self-check without notes and answer
  every designated core question correctly.
- [ ] I score at least 10 out of 12 on the fixed classification gate, including
  all six critical cases.
- [ ] I score at least 9 out of 10 on the Book/BookCopy/Loan exercise, including
  all required decisions.
- [ ] I score at least 10 out of 12 on the Meeting Room model, including all
  three critical requirements.
- [ ] I correctly complete all six rows of the contextual-state exercise.
- [ ] My reference Movie Ticket model passes every required test.
- [ ] My public model prevents arbitrary lifecycle-state assignment.
- [ ] My multi-object failures leave all previously valid state unchanged.
- [ ] I complete Vending Machine in 40 minutes and score at least 12 out of 15.
- [ ] I adapt Meeting Room recurrence in 15 minutes without breaking original
  tests or creating partial reservations.
- [ ] I independently model at least three domains from different families:
  inventory/booking, workflow/state machine, and financial/ledger.
- [ ] For each model, I can explain vocabulary, identities, value semantics,
  authoritative state, relationships, invariant owners, consistency boundaries,
  failure paths, and one change impact.
- [ ] None of my reviewed models contains a stable/contextual state error,
  duplicated mutable source of truth, unexplained bidirectional graph, boolean
  lifecycle explosion, or god coordinator.

The readiness sentence for this topic is:

> I can turn requirements into a responsibility-driven object model, place
> identity, state, invariants, and collaboration deliberately, prove the model
> with failure tests, and adapt it without unrelated rewrites.

## Next topic

[**Topic 4 - UML and Interaction Modeling**](./04-uml-and-interaction-modeling.md)
expresses the object structure, cardinality, lifecycle, and critical workflows
from Topic 3 through readable class, sequence, activity, and state diagrams.
