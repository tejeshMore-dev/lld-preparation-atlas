# Topic 5 - Design Principles and Heuristics

[Curriculum index](../README.md) | [Preparation roadmap](../roadmap.md) |
[Previous topic](./04-uml-and-interaction-modeling.md)

- **Category:** Design quality and change management
- **Difficulty:** Intermediate to advanced
- **Priority:** Essential
- **Prerequisites:** Topics 1-4
- **Running example:** Movie Ticket Booking
- **Output:** A cohesive, loosely coupled, testable design whose abstractions
  are justified by real requirements and likely change

## Outcome

After completing this topic, you should be able to:

- Evaluate a design through its responsibilities and change axes.
- Distinguish high cohesion from merely having small classes.
- Distinguish necessary domain coupling from harmful or unstable coupling.
- Apply encapsulation and information hiding to protect design decisions.
- Apply all five SOLID principles behaviorally rather than by memorized slogans.
- Detect and test Liskov Substitution Principle violations.
- Separate dependency inversion from dependency injection.
- Use focused Python `Protocol`/`ABC` contracts at genuine boundaries.
- Apply practical GRASP-style responsibility heuristics.
- Choose composition or inheritance based on lifecycle and substitutability.
- Use Tell, Don't Ask and the Law of Demeter without turning them into rules
  about dot counts.
- Apply KISS, YAGNI, and DRY without creating premature abstractions.
- Balance extensibility, simplicity, performance, and delivery constraints.
- Refactor a working design safely using tests and small responsibility moves.
- Explain which principle addresses a concrete design force and what it costs.

## Core idea

Design principles are diagnostic tools for managing change. They are not a
score based on class count, interface count, or pattern vocabulary.

```text
requirements create reasons to change
    -> responsibilities group related rules
    -> boundaries isolate volatile decisions
    -> contracts protect important behavior
    -> tests verify substitution and invariants
    -> change feedback refines the design
```

Use this question before naming a principle:

> What requirement, actor, dependency, or failure mode is likely to change, and
> which part of the design should absorb that change?

A simpler design that handles known change safely is better than a framework of
unused abstractions that claims to handle every future.

## Scope boundary

This topic covers:

- cohesion, coupling, encapsulation, and information hiding;
- Single Responsibility, Open/Closed, Liskov Substitution, Interface
  Segregation, and Dependency Inversion;
- practical GRASP-style heuristics such as Information Expert, Creator,
  Controller, Low Coupling, High Cohesion, Polymorphism, Indirection, Pure
  Fabrication, and Protected Variations;
- composition versus inheritance;
- Tell, Don't Ask, Law of Demeter, KISS, YAGNI, DRY, and pragmatic trade-offs;
- safe principle-driven refactoring.

It does not deeply catalogue:

- creational, structural, or behavioral design patterns; Topics 6-8 do that;
- repository, unit-of-work, event-bus, and other application patterns; Topic 9
  covers those building blocks;
- API, concurrency, or persistence mechanisms; Topics 10-12 cover them;
- code-smell catalogues and large refactoring mechanics; Topic 13 deepens them.

Examples may use a policy object, decorator-like composition, factory function,
or gateway boundary because the principles require a concrete shape. The named
pattern, its alternatives, and its full applicability belong to later topics.

Code fences use Python 3.10+ and are focused excerpts. Some rely on domain types
or imports established by surrounding text. When combining excerpts into one
module, add those definitions/imports and use
`from __future__ import annotations` when forward references require it.

## 1. Learn

### 1.1 Design for reasons to change

Before splitting or abstracting code, list its change axes.

For Movie Ticket Booking:

| Change axis | Example changes | Natural boundary candidate |
|---|---|---|
| Pricing rules | Weekend surcharge, loyalty discount, taxes | Pricing policy |
| Payment provider | Fake gateway, bank provider, retry semantics | Payment boundary |
| Time | Real clock, deterministic test clock | Clock boundary |
| Seat inventory | Hold expiry, ownership, release rules | Show inventory/hold boundary |
| Search/catalog | New filters, schedule overlap | Catalog/query boundary |
| Booking lifecycle | Confirmation, cancellation, expiry | Booking behavior/use case |
| Notification | Email, SMS, delivery retry | Notification boundary |

Related rules that change together should usually stay together. Unrelated
rules that change for different reasons should not be forced into one unit.

Do not predict every future. Use evidence:

- current requirements already contain variants;
- tests need a controlled collaborator;
- external integration is known to vary/fail;
- a follow-up requirement targets one rule repeatedly;
- different business owners change different policies;
- the code already changes together or separately in practice.

### 1.2 Cohesion: keep related responsibility together

Cohesion describes how strongly the contents of a module/class/function belong
together.

High cohesion means:

- members support one clear purpose;
- methods operate on the state the class owns;
- invariants and transitions live close to protected state;
- the unit can be named specifically;
- most changes affect most of the unit for the same reason;
- unrelated consumers do not depend on unused behavior.

Low cohesion signals:

- a name such as `Utils`, `Manager`, `Processor`, or `Common`;
- unrelated fields that are never used together;
- methods serving different actors or business capabilities;
- a class that formats UI, calculates prices, persists records, and sends email;
- a coordinator accumulating every new use case;
- many methods depending on disjoint subsets of state.

Class size is evidence, not a verdict. A 200-line stateful workflow can be
cohesive if the rules form one lifecycle. A 20-line helper can be incohesive if
it contains unrelated conveniences.

Use the sentence test:

```text
This class is responsible for ____________________.
```

If the blank needs several unrelated clauses joined by *and*, review the
boundary. Do not split cohesive operations merely to avoid the word *and*.

### 1.3 Coupling: manage necessary knowledge

Coupling describes how one unit depends on another. Zero coupling is neither
possible nor desirable in a collaborating domain model.

Healthy coupling:

- `Booking` depends on `BookingStatus` because lifecycle vocabulary belongs
  together;
- checkout depends on a narrow `PaymentGateway` because payment is required;
- `ShowSeat` knows its owner booking ID because ownership protects availability.

Risky coupling:

- a domain entity imports a provider SDK;
- one service knows every concrete class and data representation;
- callers reach through several objects to edit deep state;
- modules rely on globals or initialization order;
- a small provider change forces changes across domain classes;
- a method accepts a giant object but uses one field.

Evaluate coupling along several dimensions:

| Dimension | Review question |
|---|---|
| Breadth | How many collaborators must this unit know? |
| Strength | Does it know a stable contract or concrete internals? |
| Direction | Does high-level policy point toward volatile detail? |
| Volatility | How often does the dependency change? |
| Temporal | Must calls occur in a fragile hidden order? |
| Data | Does it depend on a narrow value or an entire object graph? |
| Global | Is state hidden in globals/singletons? |

The goal is low *unnecessary* coupling and explicit *necessary* coupling.

### 1.4 Encapsulation and information hiding

Encapsulation groups state with behavior that preserves it. Information hiding
conceals decisions likely to change.

They overlap but are not identical:

```text
Encapsulation:
  Booking.confirm() protects status-transition rules.

Information hiding:
  PaymentGateway hides provider protocol and SDK details.
```

Good boundaries hide:

- mutable representation;
- validation and invariant mechanics;
- policy algorithms;
- external provider details;
- cache/index structure;
- clock acquisition;
- ordering required for a safe workflow.

They expose:

- domain-named commands and queries;
- stable values/results;
- explicit failures;
- narrow collaborator contracts.

Hiding everything behind getters and setters is not information hiding. A
setter such as `set_status(CONFIRMED)` exposes the decision that should be
protected.

### 1.5 Single Responsibility Principle

The Single Responsibility Principle (SRP) says a module should have one reason
to change. A practical interpretation is one cohesive responsibility for one
business capability or actor.

SRP does not mean:

- one method per class;
- one class per requirement sentence;
- services may never coordinate several objects;
- every field needs a wrapper;
- a file over a line-count threshold is automatically wrong.

Consider a checkout coordinator that:

- validates booking lifecycle;
- checks seat holds;
- calls a payment boundary;
- records the attempt;
- asks domain objects to confirm.

Those steps may form one cohesive *confirm booking* use case. The same class
also managing movie search, user registration, analytics formatting, and
provider-specific HTTP signatures would introduce separate reasons to change.

Use an SRP audit:

1. List public behaviors.
2. Name the actor/reason that changes each behavior.
3. Group behaviors that share state, invariants, and transaction ordering.
4. Separate groups that change independently.
5. Keep orchestration together when splitting would hide required ordering.
6. Re-evaluate after real changes, not only imagined ones.

### 1.6 SRP and responsibility migration

When a service becomes a god object, do not mechanically create many tiny
services. Move responsibilities to natural owners.

Before:

```python
class BookingManager:
    def confirm(self, booking: Booking) -> None:
        if booking.status != "PENDING":
            raise ValueError("Invalid status")
        booking.status = "CONFIRMED"
```

After:

```python
class Booking:
    def confirm(self) -> None:
        if self._status is not BookingStatus.PENDING_PAYMENT:
            raise ValueError("Only a pending booking can be confirmed")
        self._status = BookingStatus.CONFIRMED
```

The coordinator retains multi-object ordering. The entity gains the lifecycle
rule that protects its own state.

Useful destinations:

| Responsibility | Likely destination |
|---|---|
| Single-object invariant | Entity/value method |
| Varying calculation | Policy abstraction |
| External operation | Gateway/port |
| Search/query | Catalog/query service |
| Object construction rules | Constructor/factory boundary |
| Multi-object use-case ordering | Application coordinator |
| Persistence mechanics | Repository/adapter in later topics |

### 1.7 Open/Closed Principle

The Open/Closed Principle (OCP) says a software element should be open to
extension but closed to modification for a chosen kind of change.

The phrase is relative, not absolute:

```text
Closed against: adding another pricing calculation.
Open through: a PricingPolicy contract and injected implementation.
```

OCP does not require code that never changes. Requirements often change the
core model legitimately. The aim is to keep stable workflow untouched when a
known variation is added.

Bad variation handling:

```python
def price(kind: str, amount: Decimal) -> Decimal:
    if kind == "standard":
        return amount
    if kind == "weekend":
        return amount * Decimal("1.25")
    if kind == "member":
        return amount * Decimal("0.90")
    raise ValueError("Unknown pricing kind")
```

Every new rule edits the dispatcher. That may be acceptable for two stable
cases, but repeated changes and independently tested algorithms justify a
boundary.

```python
from typing import Protocol


class PricingPolicy(Protocol):
    def total(self, base_amount: Decimal) -> Decimal:
        ...


class StandardPricing:
    def total(self, base_amount: Decimal) -> Decimal:
        return base_amount


class WeekendPricing:
    def __init__(self, surcharge: Decimal) -> None:
        self._surcharge = surcharge

    def total(self, base_amount: Decimal) -> Decimal:
        return base_amount * (Decimal("1") + self._surcharge)
```

Now the checkout flow depends on the capability, not a variation tag.

### 1.8 Find the correct extension axis

An abstraction helps only when it matches the change.

Suppose pricing changes by:

- day of week;
- seat type;
- coupon;
- tax jurisdiction;
- loyalty tier;
- demand.

One subclass for every combination causes explosion:

```text
WeekendPremiumCouponMemberPricing
WeekdayRegularNoCouponGuestPricing
...
```

The real axis may be composable price adjustments rather than one monolithic
algorithm. Or a single policy may be simplest if rules always change together.

Ask:

1. Which variations coexist?
2. Are they selected independently?
3. Must they run in a defined order?
4. Do they share data/invariants?
5. Is configuration data sufficient instead of polymorphism?
6. How will combinations be tested?

Do not abstract at the first `if`. Abstract when the variation is meaningful,
repeated, independently changeable, or externally volatile.

### 1.9 Liskov Substitution Principle

The Liskov Substitution Principle (LSP) says objects of a subtype or contract
implementation must be usable wherever the declared abstraction is expected
without breaking client correctness.

Matching method names and types is not enough. Subtypes must honor the
behavioral contract.

An implementation must not unexpectedly:

- require stronger preconditions;
- provide weaker postconditions;
- violate invariants;
- change meaningful side effects;
- return a semantically incompatible result;
- raise new failures for valid contract inputs;
- break ordering, idempotency, or ownership guarantees;
- mutate inputs when the contract promises not to.

Contract example:

```python
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol


class ChargeStatus(Enum):
    COMPLETED = auto()
    DECLINED = auto()


@dataclass(frozen=True)
class ChargeResult:
    reference: str
    status: ChargeStatus


class PaymentGateway(Protocol):
    """Return a result for every valid positive amount; declines are data."""

    def charge(self, booking_id: str, amount_cents: int) -> ChargeResult:
        ...
```

A valid implementation may decline a charge by returning `DECLINED`. An
implementation that raises `ValueError` for every card amount above its own
undocumented limit strengthens the precondition and may violate substitution.

### 1.10 Test behavioral substitutability

Write contract tests once and run them against every implementation.

```python
def assert_gateway_contract(
    testcase: unittest.TestCase,
    gateway: PaymentGateway,
) -> None:
    result = gateway.charge("booking-1", 50000)
    testcase.assertIsInstance(result, ChargeResult)
    testcase.assertIn(result.status, set(ChargeStatus))
    testcase.assertTrue(result.reference)


class GatewayContractTest(unittest.TestCase):
    def test_fake_gateway(self) -> None:
        assert_gateway_contract(self, FakePaymentGateway())

    def test_sandbox_gateway(self) -> None:
        assert_gateway_contract(self, SandboxPaymentGateway())
```

Contract tests should cover:

- valid boundary inputs;
- result semantics;
- documented failures;
- mutation/side-effect promises;
- idempotency where required;
- ordering guarantees where observable.

Classic inheritance puzzles are less useful than testing the contracts your
design actually relies on.

### 1.11 LSP and inheritance

Inheritance is safe only when the subtype is a behavioral *is-a*, not merely a
convenient way to reuse code.

Warning example:

```python
class ReadOnlyAccount(Account):
    def withdraw(self, amount: Money) -> None:
        raise NotImplementedError
```

If `Account` promises withdrawal for valid balances, `ReadOnlyAccount` is not a
substitutable subtype. Better options include:

- a narrower read-only interface for read clients;
- composition around an account view;
- separate capabilities;
- changing the general contract if withdrawal was never universal.

Ask of every subtype:

- Can the parent contract describe it truthfully?
- Do all inherited operations make domain sense?
- Can client code remove type checks?
- Do parent invariants still hold?
- Do tests pass unchanged for every implementation?

### 1.12 Interface Segregation Principle

The Interface Segregation Principle (ISP) says clients should not depend on
methods they do not use.

Large contract:

```python
class CommerceProvider(Protocol):
    def charge(self, amount: Decimal) -> str: ...
    def refund(self, payment_id: str) -> None: ...
    def send_email(self, address: str, body: str) -> None: ...
    def search_movies(self, query: str) -> list[Movie]: ...
```

This groups unrelated clients and changes.

Focused capabilities:

```python
class ChargeGateway(Protocol):
    def charge(self, amount: Decimal) -> str:
        ...


class RefundGateway(Protocol):
    def refund(self, payment_id: str) -> None:
        ...


class Notifier(Protocol):
    def send(self, recipient: str, message: str) -> None:
        ...
```

Interface size is client-relative. Two methods that every payment workflow
needs may form one cohesive `PaymentGateway`. Split charge and refund only when
different clients/providers genuinely need different capabilities.

Python's structural `Protocol` makes client-owned narrow contracts practical.
An implementation can satisfy several protocols without inheriting a large
nominal interface.

### 1.13 Recognize interface pollution

ISP warning signals:

- implementations raise `NotImplementedError` for contract methods;
- test fakes implement many irrelevant methods;
- callers receive a broad service to invoke one operation;
- one method change forces unrelated implementations to update;
- authorization differs dramatically by method groups;
- remote operations and local calculations share one interface;
- optional methods depend on checking capabilities at runtime.

Do not split an interface only to reach one method per protocol. Cohesive client
needs and consistent implementations are stronger criteria.

### 1.14 Dependency Inversion Principle

The Dependency Inversion Principle (DIP) says:

- high-level policy should not depend directly on low-level detail;
- both should depend on an abstraction;
- the abstraction should express policy needs rather than provider details.

Without inversion:

```text
BookingCheckout -> StripeSDK -> HTTP details
```

With inversion:

```text
BookingCheckout -> PaymentGateway contract <- StripePaymentAdapter
```

Source-code dependency points toward the stable, high-level contract. Runtime
control may still flow from checkout to the adapter and external provider.

The abstraction should be owned near the consumer's need:

```python
class PaymentGateway(Protocol):
    def charge(
        self,
        booking_id: str,
        total: Money,
        method: PaymentMethod,
    ) -> PaymentAttempt:
        ...
```

Do not leak provider request objects, status codes, or SDK exceptions into this
contract unless they are real domain/application concepts.

### 1.15 Dependency inversion versus dependency injection

These ideas are related but different.

| Concept | Meaning |
|---|---|
| Dependency inversion | Policy depends on an abstraction instead of volatile detail |
| Dependency injection | A dependency is supplied from outside rather than constructed internally |
| Composition root | Boundary where concrete implementations are chosen and connected |

Injection without inversion:

```python
class Checkout:
    def __init__(self, stripe_client: StripeClient) -> None:
        self._stripe = stripe_client
```

The dependency is injected, but high-level code still depends on a concrete
provider API.

Inversion plus injection:

```python
class Checkout:
    def __init__(self, payment_gateway: PaymentGateway) -> None:
        self._payments = payment_gateway
```

Composition root:

```python
gateway = StripePaymentAdapter(api_key=settings.payment_api_key)
checkout = Checkout(payment_gateway=gateway)
```

The composition root is allowed to know concrete classes. Domain policy should
not construct them.

### 1.16 Do not create an interface for everything

DIP is most valuable at:

- external systems;
- volatile algorithms;
- time/random/ID sources needed for deterministic tests;
- persistence boundaries;
- different deployment implementations;
- important policy extension axes.

An interface may add little for:

- a stable value object such as `Money`;
- a domain entity directly owned by a use case;
- a tiny pure helper with no expected alternatives;
- a concrete collection internal to one object;
- speculative variants with no requirement or test need.

Every abstraction has costs:

- another name and navigation step;
- contract design and documentation;
- composition/configuration;
- more test combinations;
- risk of choosing the wrong generalization.

Pay that cost where volatility or control justifies it.

### 1.17 GRASP-style responsibility heuristics

GRASP is a set of responsibility-assignment patterns. Use the ideas as review
questions rather than ceremony.

#### Information Expert

Assign a responsibility to the object with the necessary information and
authority.

```text
DateRange knows endpoints -> DateRange.overlaps(other)
Screen owns layout        -> Screen.add_seat(seat)
Booking owns status       -> Booking.confirm()
```

Do not use Information Expert to make an entity call infrastructure merely
because it contains an email or payment ID.

#### Creator

A type is a good creation owner when it:

- contains or aggregates the created object;
- records it closely;
- uses it heavily;
- has the construction data;
- controls its lifecycle.

`Show` or a catalog boundary can create `ShowSeat` inventory. A booking use case
can create a `Booking` after validation. A dedicated factory becomes useful
when construction selection itself is complex; Topic 6 deepens that option.

#### Controller

A controller receives a system/use-case event and coordinates work:

```text
BookingCheckout.confirm_booking(...)
ATM.withdraw(...)
ElevatorSystem.request_elevator(...)
```

It should delegate domain decisions and avoid becoming the owner of every
entity's state.

#### High Cohesion and Low Coupling

Keep responsibilities focused while minimizing knowledge of volatile or
unrelated collaborators. These are balancing forces, not independent maxima.

Moving every method into a new class may reduce class size while increasing
navigation and coupling. Keeping every operation together may reduce wiring
while destroying cohesion. Judge the change boundary.

#### Polymorphism

When behavior varies by type/rule, let implementations honor one contract
instead of growing repeated conditionals:

```text
PricingPolicy.total(...)
SchedulingPolicy.select(...)
EligibilityRule.is_eligible(...)
```

Use it for behavioral variation, not simple labels with no differing behavior.

#### Pure Fabrication

Sometimes no domain entity naturally owns a responsibility. Create a
non-domain service to preserve cohesion and low coupling:

```text
PaymentGateway
BookingRepository
NotificationService
```

This is not permission to create arbitrary helpers. The fabricated type must
own a cohesive technical/application responsibility.

#### Indirection

An intermediate abstraction reduces direct coupling:

```text
Checkout -> PaymentGateway -> ProviderAdapter
```

Each layer costs complexity and latency of understanding. Add indirection when
it protects a meaningful boundary.

#### Protected Variations

Identify a likely variation point and place a stable interface around it:

```text
volatile provider protocol behind PaymentGateway
changing allocation algorithm behind AllocationPolicy
nondeterministic time behind Clock
```

This is the reasoning shared by OCP and DIP.

### 1.18 Composition over inheritance

Composition builds behavior from collaborators. Inheritance defines a subtype
relationship and reuses/overrides behavior.

Prefer composition when:

- behavior must change at runtime;
- several independent behaviors combine;
- the relationship is *has-a* or *uses-a*;
- subclasses would exist only for code reuse;
- the base class would expose protected internals;
- combinations would create a subclass explosion.

Inheritance is appropriate when:

- the subtype is meaningful in domain language;
- it preserves the complete base contract;
- shared invariants/behavior are genuinely universal;
- the hierarchy is shallow and stable;
- clients benefit from substitutability.

Example composition:

```python
class SurchargePricing:
    def __init__(
        self,
        base: PricingPolicy,
        surcharge_rate: Decimal,
    ) -> None:
        self._base = base
        self._rate = surcharge_rate

    def total(self, base_amount: Decimal) -> Decimal:
        subtotal = self._base.total(base_amount)
        return subtotal * (Decimal("1") + self._rate)
```

The object delegates to another policy and adds one concern. Topic 7 will name
and compare the structural pattern when appropriate.

### 1.19 Tell, Don't Ask

Tell, Don't Ask encourages callers to request domain behavior rather than query
state and make another object's decision.

Ask-and-edit:

```python
if booking.status is BookingStatus.PENDING_PAYMENT:
    booking.status = BookingStatus.CONFIRMED
```

Tell:

```python
booking.confirm()
```

Benefits:

- invariant stays with its owner;
- callers do not repeat transition conditions;
- representation can change;
- tests focus on domain behavior.

This is not a ban on queries. A pricing policy must ask for price inputs; a UI
must read a booking summary; a coordinator must inspect a result to choose a
workflow branch. The warning is asking for internal state in order to perform
the owner's business decision elsewhere.

### 1.20 Law of Demeter / least knowledge

The Law of Demeter suggests a method should collaborate with its direct
neighbors rather than navigate deep internals.

Fragile traversal:

```python
booking.show.screen.theatre.payment_config.provider.charge(...)
```

Problems:

- checkout knows a large object graph;
- intermediate representation becomes public;
- a topology change affects distant callers;
- testing requires constructing irrelevant objects.

Prefer a direct collaborator or intention-revealing operation:

```python
self._payment_gateway.charge(booking.booking_id, booking.total, method)
```

The law is not "only one dot." Fluent immutable APIs, local values, and
collection operations may use several dots safely. Measure leaked knowledge,
not punctuation.

### 1.21 Command-query separation

A command changes state; a query returns information without externally visible
mutation. Separating them improves reasoning:

```text
query:   show.available_seats(now)
command: holds.hold_all(booking, now, deadline)
```

A command may return an outcome or created entity; command-query separation is
not a ban on useful return values. Avoid methods whose name suggests a read but
silently performs surprising business mutation.

Time-dependent queries may normalize expired state in an educational design,
but that coupling should be explicit. A separate expiry command can make
behavior clearer when the distinction matters.

### 1.22 KISS: keep the design understandable

KISS means choose the simplest design that correctly handles current
requirements and credible near-term change.

Simplicity is not:

- putting everything in one function;
- ignoring failures;
- using raw dictionaries for every concept;
- refusing all abstractions;
- postponing invariants.

Essential complexity belongs in the model:

- booking and show-seat lifecycles;
- hold ownership and expiry;
- payment failure ordering;
- all-or-none selection.

Accidental complexity can be removed:

- three factories for one concrete implementation;
- interface/base/implementation triplets with no variation;
- event buses for local direct calls with no asynchronous requirement;
- generic rule engines for two fixed rules;
- configuration DSLs for constants.

### 1.23 YAGNI: do not build unrequested futures

YAGNI means *You Aren't Gonna Need It*: do not implement functionality before
it is required.

Examples to postpone in a bounded movie-booking interview:

- multi-currency tax engines;
- seat recommendation AI;
- waitlist promotion;
- event sourcing;
- ten payment providers;
- generic plugin discovery;
- distributed locks in an in-memory exercise.

YAGNI does not mean make future change impossible. Clear responsibilities,
encapsulation, and tests create change capacity without implementing the
feature.

### 1.24 DRY: remove duplicated knowledge

DRY means every piece of domain knowledge should have one authoritative
representation. It does not mean every similar-looking line must be shared.

Harmful duplication:

```text
hold duration validated in three services
money rounding copied across pricing implementations
allowed booking transitions repeated in controller and entity
seat compatibility rules duplicated in UI and domain
```

Acceptable duplication:

- two small functions happen to have similar syntax but different business
  reasons to change;
- tests repeat setup to keep scenarios readable;
- a transport DTO and domain object share fields but have different contracts;
- independent modules intentionally avoid coupling.

Use the rule of knowledge:

> Would one business decision require both copies to change together?

If yes, centralize the knowledge. If not, a shared abstraction may create false
coupling.

The Rule of Three is useful: tolerate a small duplication once, observe the
third real case, then extract the stable common concept. Critical invariants may
justify centralization immediately.

### 1.25 Design by contracts and invariants

Every public behavior has:

- preconditions the caller must satisfy;
- postconditions the operation promises on success;
- invariants that remain true;
- documented failure behavior;
- side effects and ordering.

Example `hold_all` contract:

```text
Preconditions:
  booking ID, show ID, unique non-empty seat selection, future deadline

Success postconditions:
  every selected show seat is HELD by the booking until the same deadline

Failure postconditions:
  no newly selected show seat changed ownership/state

Invariant:
  at most one booking owns a show seat
```

Contracts make SOLID testable. LSP is the requirement that every implementation
honor the declared contract.

### 1.26 Balance principles when they conflict

Principles often pull in different directions.

| Tension | Practical balance |
|---|---|
| SRP vs workflow visibility | Keep cohesive orchestration together; move owned rules outward |
| OCP vs YAGNI | Abstract proven variation, not imagined universes |
| DRY vs low coupling | Share business knowledge, not accidental syntax |
| ISP vs too many interfaces | Split by client needs, not one method mechanically |
| DIP vs simplicity | Invert volatile/external/test-controlled dependencies |
| Encapsulation vs query needs | Expose stable read models, hide mutation decisions |
| Composition vs object count | Compose when behavior/lifecycle justifies the collaborator |
| Performance vs clean boundaries | Measure first; optimize behind explicit contracts |

When explaining a decision, state both benefit and cost:

```text
"Injecting Clock adds one contract and constructor dependency, but it removes
hidden time coupling and makes expiry tests deterministic. That trade is worth
it because time directly controls booking validity."
```

### 1.27 Use a principle-driven review sequence

Review a working model in this order:

1. Trace requirements to responsibility owners.
2. List reasons/actors that change each class.
3. Find duplicated authoritative knowledge.
4. Find deep knowledge and hidden/global dependencies.
5. Mark real variation and external volatility.
6. Define behavioral contracts at those boundaries.
7. Check every subtype/implementation for substitutability.
8. Check interfaces from each client's perspective.
9. Verify dependency direction and composition root.
10. Remove speculative abstractions.
11. Apply one realistic change.
12. Compare code/tests changed with the predicted boundary.

Do not start by asking, "Where can I apply all five SOLID letters?"

## 2. Recognize

### 2.1 Change and design signals

| Signal | Likely principle/heuristic |
|---|---|
| Unrelated methods/actors in one class | Cohesion/SRP review |
| Same business rule copied | DRY/information expert |
| Repeated type/strategy branches | OCP/polymorphism candidate |
| Subclass rejects valid parent operation | LSP violation |
| Fake implements unused methods | ISP violation |
| Domain imports provider SDK | DIP/protected variation |
| Constructor creates clock/gateway | Dependency injection/testability issue |
| Caller edits another object's status | Encapsulation/Tell, Don't Ask |
| Long object navigation chain | Law of Demeter/knowledge coupling |
| Subclass only reuses code | Composition candidate |
| Interface exists with one implementation/no volatility | YAGNI review |
| Two similar blocks change independently | Do not force DRY |
| One change edits many unrelated modules | Boundary/coupling problem |
| Many classes change for every small feature | Wrong abstraction axis |
| Coordinator preserves required operation ordering | Cohesive Controller, not automatically SRP failure |

### 2.2 Smell-to-question mapping

Do not jump from a smell directly to a refactor.

| Smell | Ask first |
|---|---|
| Large class | Which responsibilities and change reasons are actually distinct? |
| Long method | Is it one readable workflow or several decisions mixed together? |
| Conditional | Is this lifecycle control, simple validation, or real polymorphic variation? |
| Duplicate code | Does it duplicate knowledge or only syntax? |
| Concrete dependency | Is it volatile/external, and do tests need control? |
| Inheritance | Does every subtype honor the complete base contract? |
| Many parameters | Is there a missing cohesive value/request object? |
| Pass-through service | Does it add policy, boundary, transaction, or indirection value? |
| Broad interface | Which clients use which coherent method groups? |
| Deep chain | Which internal topology is leaking? |

### 2.3 Principle misuse signals

- A separate interface exists for every class with no alternative or boundary.
- A factory creates one trivial object with no construction decision.
- Every `if` becomes a subtype.
- SRP is justified only by line count.
- OCP is claimed because "new classes can always be added" while central
  dispatch still changes.
- LSP is described only as matching function signatures.
- ISP produces dozens of one-method contracts with the same clients.
- DIP is claimed solely because constructor injection is used.
- DRY centralizes unrelated behaviors into a generic utility.
- YAGNI is used to reject required failure handling.
- KISS is used to permit public mutation and broken invariants.
- Composition creates a deeply layered call chain with no variation benefit.
- Principle names replace evidence about requirements, changes, and tests.

### 2.4 Decision questions

Before changing a design, ask:

1. What concrete pain or change does this solve?
2. Which responsibility owns the knowledge?
3. Which things change together and separately?
4. What coupling is necessary?
5. Is the dependency stable, volatile, or external?
6. What behavioral contract does the client require?
7. Can every implementation honor it?
8. Which clients need which operations?
9. Does the abstraction match the real variation axis?
10. Could a value/configuration/function be simpler than a class hierarchy?
11. What new complexity does the refactor add?
12. Which test proves the improvement?

## 3. Model

### 3.1 Running example: Movie Ticket Booking change map

Start from Topics 3-4 and review these likely changes:

| Change | Should mainly affect | Should largely remain stable |
|---|---|---|
| Weekend pricing | Pricing policy/wiring/tests | Booking lifecycle, gateway |
| New payment provider | Adapter/wiring/contract tests | Seat ownership, pricing |
| Hold duration | Configuration/hold use case | Movie, theatre layout |
| Failed payment retry | Payment history/confirmation workflow | Catalog search |
| New search filter | Catalog query | Booking confirmation |
| Accessible seat pairing | Selection policy/hold tests | Payment provider |
| SMS after confirmation | Notification boundary/workflow | Price calculation |
| Partial cancellation | Booking item model/refund workflow | Physical screen layout |

If implementing weekend pricing changes `Booking`, `ShowSeat`, payment gateway,
and catalog search, coupling is misplaced. If partial cancellation changes the
booking model substantially, that is legitimate because the core responsibility
changed.

### 3.2 Responsibility and cohesion review

| Component | Cohesive responsibility | Review boundary |
|---|---|---|
| `Seat` | Stable physical metadata | Must not own per-show availability |
| `ShowSeat` | Contextual availability/owner/expiry | Lifecycle methods should hide state mutation |
| `Booking` | Selection and booking lifecycle | Payment history reference belongs here if required |
| `CatalogService` | Registration, scheduling, search | Split only if change/load makes capabilities independent |
| `BookingService` | Booking use-case orchestration | Move single-object guards to entities; keep ordering visible |
| `PricingStrategy` | Price calculation contract | Do not add payment/search operations |
| `PaymentGateway` | Charge/refund provider boundary | Translate provider details at adapter |
| `Clock` | Current-time capability | Keep deterministic and narrow |

The existing `BookingService` coordinates several closely related workflows:
create, confirm, cancel, expire, and history. That is not automatically an SRP
violation. Review it when:

- catalog/search behavior leaks into it;
- domain transition rules are duplicated there;
- payment-provider details appear;
- every new booking feature changes one giant method;
- independent clients need only disjoint method groups;
- its lock/store responsibilities obscure workflow.

### 3.3 Coupling direction

```text
main/composition root
    -> concrete catalog, policy, gateway, clock
    -> BookingService

BookingService
    -> PricingPolicy contract
    -> PaymentGateway contract
    -> Clock contract
    -> Booking/ShowSeat domain behavior

Provider adapter
    -> PaymentGateway contract
    -> external SDK
```

High-level booking code should not import provider request/response types. The
composition root selects implementations and may know both sides.

### 3.4 SOLID application table

| Principle | Concrete application | Evidence |
|---|---|---|
| SRP | Catalog, pricing, payment, domain lifecycle, and checkout have distinct responsibilities | Change map remains localized |
| OCP | Add pricing/provider implementations through stable contracts | Existing confirmation flow unchanged |
| LSP | Every pricing/gateway implementation honors input, result, failure, and side-effect contract | Shared contract tests pass |
| ISP | Pricing, clock, and payment contracts expose cohesive client needs | Fakes implement no unrelated operations |
| DIP | Booking flow depends on application-owned contracts | Provider/time details stay at wiring edge |

### 3.5 GRASP-style assignment table

| Responsibility | Heuristic | Owner |
|---|---|---|
| Validate show-seat transition | Information Expert | `ShowSeat` |
| Create show inventory | Creator | `Show`/catalog boundary |
| Receive confirm-booking system event | Controller | `BookingService` |
| Select price behavior | Polymorphism | `PricingPolicy` implementations |
| Isolate provider | Protected Variations/Indirection | `PaymentGateway` |
| Persist/query outside entity semantics | Pure Fabrication | repository/catalog boundary |
| Keep lifecycle methods together | High Cohesion | `Booking` |
| Avoid provider knowledge in booking | Low Coupling | gateway contract |

### 3.6 Extension-axis example: pricing

Requirements:

- base total comes from per-show seat prices;
- weekend surcharge may wrap base pricing;
- future coupons may be optional;
- booking flow only needs a final exact total.

Contract:

```python
from decimal import Decimal, ROUND_HALF_UP
from typing import Protocol


CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


class PricingPolicy(Protocol):
    def total(self, base_amount: Decimal) -> Decimal:
        """Return a finite, non-negative, cent-normalized total."""
        ...


class BasePricing:
    def total(self, base_amount: Decimal) -> Decimal:
        if not base_amount.is_finite() or base_amount < 0:
            raise ValueError("Base amount must be finite and non-negative")
        return money(base_amount)


class SurchargePricing:
    def __init__(self, wrapped: PricingPolicy, rate: Decimal) -> None:
        if not rate.is_finite() or rate < 0:
            raise ValueError("Surcharge rate must be finite and non-negative")
        self._wrapped = wrapped
        self._rate = rate

    def total(self, base_amount: Decimal) -> Decimal:
        subtotal = self._wrapped.total(base_amount)
        return money(subtotal * (Decimal("1") + self._rate))
```

Principle reasoning:

- OCP: new adjustments can compose without editing checkout;
- LSP: each implementation returns a valid final `Decimal` under the same
  contract;
- ISP: checkout sees one required method;
- DIP: checkout depends on `PricingPolicy`;
- composition: surcharge contains another policy;
- KISS/YAGNI: no generic rules engine or subclass per combination.

### 3.7 Behavioral contract table

| Contract | Preconditions | Success guarantee | Failure/side-effect guarantee |
|---|---|---|---|
| `PricingPolicy.total` | finite non-negative base | finite non-negative cent total | invalid input rejected; no mutation |
| `PaymentGateway.charge` | valid booking and positive amount | one recorded provider outcome/result | documented decline form; no hidden booking mutation |
| `Clock.now` | none | comparable current timestamp | deterministic fake may control value |
| `SeatHoldService.hold_all` | unique non-empty selection, future deadline | all selected seats held by one booking | no partial new hold |
| `Notifier.send` | valid recipient/message | delivery accepted or documented result | must not mutate booking |

This table is more useful for LSP than inheritance slogans.

### 3.8 Change simulation

Change:

> Add a premium payment provider for bookings above INR 10,000.

Poor response:

- add `if total > 10000` in `Booking`, `BookingService`, and cancellation;
- let entities construct both SDKs;
- return different result types;
- skip refund support for premium provider.

Principled response:

1. Clarify whether provider selection is policy or fixed configuration.
2. Preserve one `PaymentGateway` behavioral contract.
3. Add a routing adapter/policy only if selection is an actual requirement.
4. Ensure both providers honor charge/refund outcomes.
5. Wire it at the composition root.
6. Run shared contract tests and existing booking tests.
7. Keep seat, catalog, and pricing components unchanged.

The number of new classes is not the success metric. Localized change and
preserved behavior are.

### 3.9 Principle trade-off record

Document significant decisions briefly:

| Decision | Benefit | Cost | Revisit when |
|---|---|---|---|
| Inject `Clock` | Deterministic expiry tests | Extra contract/wiring | Time no longer affects behavior (unlikely) |
| One `PaymentGateway` with charge/refund | Cohesive booking payment need | Charge-only clients see refund | Providers/clients split capabilities |
| Keep booking workflows in one service | Visible ordering/shared boundary | Service may grow | Independent actors/change cycles emerge |
| Compose surcharge over pricing | Independent combination | More object wiring | Rules always change as one formula |
| Store IDs across catalog boundary | Smaller graph/lifecycle independence | Resolution dependency | Objects share one tight lifetime boundary |

Trade-off records prevent principles from becoming unexplained dogma.

## 4. Implement

### 4.1 Refactor hidden volatile dependencies

Before:

```python
from datetime import datetime


class BookingCheckout:
    def confirm(self, booking: Booking) -> None:
        gateway = ConcreteBankSdk(api_key="hard-coded")
        if datetime.now() >= booking.hold_expires_at:
            raise ValueError("Expired")
        gateway.charge(float(booking.total))
        booking.status = BookingStatus.CONFIRMED
```

Problems:

- hidden time/provider dependencies;
- provider types and `float` leak into policy;
- untestable real time;
- direct state mutation;
- no explicit result/failure contract;
- confirmation ordering cannot be safely tested.

After:

```python
from datetime import datetime
from decimal import Decimal
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        ...


class PaymentGateway(Protocol):
    def charge(self, booking_id: str, amount: Decimal) -> ChargeResult:
        ...


class BookingCheckout:
    def __init__(self, clock: Clock, gateway: PaymentGateway) -> None:
        self._clock = clock
        self._gateway = gateway

    def confirm(self, booking: Booking) -> ChargeResult:
        booking.ensure_live_at(self._clock.now())
        result = self._gateway.charge(booking.booking_id, booking.total)
        booking.record_charge(result)
        if result.status is ChargeStatus.COMPLETED:
            booking.confirm()
        return result
```

The refactor applies encapsulation, DIP, injection, Tell, Don't Ask, and explicit
contracts while retaining cohesive workflow ordering.

### 4.2 Use client-owned protocols

Suppose confirmation only needs current time and charge:

```python
class ConfirmationClock(Protocol):
    def now(self) -> datetime:
        ...


class ChargePort(Protocol):
    def charge(self, booking_id: str, amount: Decimal) -> ChargeResult:
        ...
```

Cancellation may depend on a separate capability:

```python
class RefundPort(Protocol):
    def refund(self, payment_reference: str) -> RefundResult:
        ...
```

A single provider adapter may implement both. Split them only if client and
provider boundaries benefit; otherwise one cohesive `PaymentGateway` is simpler.

### 4.3 Preserve invariants while moving behavior

Before:

```python
def cancel_booking(booking: Booking) -> None:
    if booking.status in (BookingStatus.CANCELLED, BookingStatus.EXPIRED):
        raise ValueError("Cannot cancel")
    booking.status = BookingStatus.CANCELLED
```

After:

```python
class Booking:
    def cancel(self) -> None:
        if self._status not in {
            BookingStatus.PENDING_PAYMENT,
            BookingStatus.CONFIRMED,
        }:
            raise ValueError("Booking cannot be cancelled")
        self._status = BookingStatus.CANCELLED
```

Then the coordinator handles cross-boundary ordering:

```python
def cancel_booking(self, booking: Booking) -> None:
    if booking.requires_refund:
        self._payments.refund(booking.completed_payment_reference)
    self._holds.release_for(booking)
    booking.cancel()
```

Do not move refund calls into `Booking`; it owns lifecycle, not provider
interaction. SRP and Information Expert must be balanced with DIP and external
boundaries.

### 4.4 Replace false inheritance with composition

Before:

```python
class WeekendPricing(StandardPricing):
    pass


class WeekendCouponPricing(WeekendPricing):
    pass
```

The hierarchy represents combinations, not substitutable domain types.

After:

```python
base: PricingPolicy = BasePricing()
weekend: PricingPolicy = SurchargePricing(base, Decimal("0.25"))
```

Additional independent adjustments can compose if requirements demand them.
The composition root makes the combination explicit.

### 4.5 Replace duplicated knowledge, not all duplication

Before:

```python
def validate_booking_total(total: Decimal) -> None:
    if not total.is_finite() or total < 0:
        raise ValueError("Invalid money")


def validate_refund_total(total: Decimal) -> None:
    if not total.is_finite() or total < 0:
        raise ValueError("Invalid money")
```

Both encode the same monetary invariant. Move it to a `Money` value object or
one authoritative conversion function.

Do not automatically merge:

```python
def active_booking_ids(bookings: list[Booking]) -> list[str]: ...
def available_seat_ids(seats: list[ShowSeat]) -> list[str]: ...
```

The loops may look similar while the knowledge and reasons to change are
different. A generic `filter_active_things()` may weaken vocabulary and couple
unrelated domains.

### 4.6 Refactor safely

Use this sequence:

1. Add characterization tests for current behavior.
2. State the design problem and desired change boundary.
3. Define or clarify the behavioral contract.
4. Make one responsibility move.
5. Keep public behavior stable unless the requirement changes.
6. Run focused and repository tests.
7. Remove old paths/duplication only after callers migrate.
8. Apply a representative change through the new boundary.
9. Compare complexity before and after.

Principle-driven refactoring is successful only if behavior remains correct and
the target change becomes safer or more local.

## 5. Test design principles

### 5.1 Test SRP and cohesion through change impact

There is no useful `assert_single_responsibility()` function. Test SRP with a
change exercise:

1. Add one pricing rule.
2. Record files/classes changed.
3. Verify booking lifecycle, catalog, and gateway stay unchanged.
4. Run existing tests.
5. Explain why the changed units form one responsibility.

An unexpected wide diff is evidence of misplaced responsibility or coupling.

### 5.2 Test OCP through extension

Add a new implementation without editing the stable consumer:

```python
class FlatDiscountPricing:
    def __init__(self, wrapped: PricingPolicy, discount: Decimal) -> None:
        if not discount.is_finite() or discount < 0:
            raise ValueError("Discount must be finite and non-negative")
        self._wrapped = wrapped
        self._discount = discount

    def total(self, base_amount: Decimal) -> Decimal:
        discounted = self._wrapped.total(base_amount) - self._discount
        return money(max(Decimal("0"), discounted))
```

Evidence:

- checkout code is unchanged;
- old policy tests remain green;
- new behavior has focused tests;
- wiring chooses the new implementation;
- the contract still holds.

### 5.3 Test LSP with a reusable contract suite

```python
class PricingContractMixin:
    def make_policy(self) -> PricingPolicy:
        raise NotImplementedError

    def test_zero_is_valid_and_non_negative(self) -> None:
        self.assertEqual(Decimal("0.00"), self.make_policy().total(Decimal("0")))

    def test_result_is_cent_normalized(self) -> None:
        result = self.make_policy().total(Decimal("10.125"))
        self.assertEqual(result, result.quantize(Decimal("0.01")))

    def test_negative_input_is_rejected_without_mutation(self) -> None:
        with self.assertRaises(ValueError):
            self.make_policy().total(Decimal("-0.01"))
```

Run the mixin/contract assertions for every policy. Add implementation-specific
tests separately. Shared tests do not prove every semantic property, but they
make the contract executable.

### 5.4 Test ISP through fakes and client compilation

A focused fake should implement only what a client needs:

```python
class FakeChargePort:
    def __init__(self, result: ChargeResult) -> None:
        self.result = result
        self.calls: list[tuple[str, Decimal]] = []

    def charge(self, booking_id: str, amount: Decimal) -> ChargeResult:
        self.calls.append((booking_id, amount))
        return self.result
```

If a confirmation test fake must define search, refund, notification, and
reporting methods, the consumed interface is likely too broad.

### 5.5 Test DIP through controlled collaborators

Verify high-level policy with:

- fixed clock;
- successful/declining gateway fake;
- recording notifier;
- deterministic ID source;
- in-memory store implementing the same application contract.

Tests should not patch hidden module globals or perform real network calls.
Constructor/factory wiring tests separately prove concrete adapters are
assembled correctly.

### 5.6 Test encapsulation and Tell, Don't Ask

- invalid transition raises and preserves status;
- public collections cannot mutate internal ownership;
- a coordinator calls `confirm()` rather than assigning a field;
- different callers cannot bypass hold ownership;
- derived queries remain consistent with authoritative state.

Architecture tests can inspect imports or public APIs, but behavioral tests are
the strongest evidence.

### 5.7 Principle review checklist

- [ ] Each class has a specific cohesive purpose.
- [ ] Change reasons/actors are identified rather than inferred from line count.
- [ ] Important knowledge has one authoritative owner.
- [ ] Necessary coupling is explicit; volatile coupling uses a boundary.
- [ ] Stable workflow is extensible along demonstrated variation axes.
- [ ] Every implementation honors a documented behavioral contract.
- [ ] Interfaces reflect client needs.
- [ ] High-level code does not import provider details.
- [ ] Concrete wiring stays at a composition root.
- [ ] Domain owners protect their state with behavior.
- [ ] Deep object-graph traversal is absent from business decisions.
- [ ] Inheritance represents true substitutability.
- [ ] Composition does not add unjustified layers.
- [ ] DRY centralizes knowledge, not coincidental syntax.
- [ ] KISS/YAGNI remove speculative complexity without dropping requirements.
- [ ] Tests prove invariants, failure postconditions, and contract substitution.
- [ ] A representative change stays inside the predicted boundary.

## 6. Adapt

### Adaptation A: add promotional pricing

Review:

- Is promotion a new independent adjustment or a replacement formula?
- Does it compose with weekend pricing?
- Which order applies?
- Can total become negative?
- Does checkout remain unchanged?
- Do all policies honor exact-money postconditions?

Principles:

- OCP/polymorphism for proven pricing variation;
- composition for independent adjustments;
- LSP contract tests for totals;
- YAGNI against a generic expression engine.

### Adaptation B: separate refund provider

Requirement:

> Charges use Provider A, but refunds are processed by Provider B.

Impact:

- one broad payment interface may no longer match client/provider capabilities;
- split `ChargePort` and `RefundPort` if wiring and clients differ;
- confirmation need not depend on refunds;
- cancellation receives the refund capability;
- both adapters stay at the composition root.

This is evidence-driven ISP, not arbitrary interface fragmentation.

### Adaptation C: notification failure must retry

- notification remains outside booking entity;
- confirmation success must not be rolled back by a notification failure unless
  the requirement explicitly says so;
- introduce a recording/retry boundary only as needed;
- keep `Notifier` contract focused;
- sequence/transaction semantics are deepened in later topics.

Relevant principles: SRP, DIP, Pure Fabrication, and explicit failure contracts.

### Adaptation D: two search clients

Requirement:

- customer search needs city/movie/date;
- operations search needs screen schedule and conflicts.

Review whether one `CatalogService` remains cohesive. If clients and change
cycles diverge, expose focused query capabilities or split internal modules.
Do not duplicate catalog state.

Relevant principles: SRP, ISP, DRY, one source of truth.

### Adaptation E: partial cancellation

This changes core booking responsibility rather than merely extending a policy.
OCP does not forbid editing `Booking`. Add `BookingItem`/ticket state if the new
invariants require it, update lifecycle and refund workflow, and preserve
unrelated catalog/payment-provider abstractions.

The lesson: a domain-model change may legitimately modify stable classes.
Principles localize the impact; they do not freeze the model forever.

### Adaptation review

For each change, state:

1. Is this a new responsibility, new variation, or changed core invariant?
2. Which current owner should change?
3. Which components should remain untouched?
4. Is a new abstraction justified by client/volatility evidence?
5. What behavioral contract changes?
6. Which substitutability tests must every implementation pass?
7. What complexity is added, and why is it worth paying?

## Common mistakes

### Using SOLID as five definitions

Reciting slogans does not demonstrate design skill. Connect each principle to a
change, contract, dependency, or failure in the current problem.

### One class per method

Tiny classes can destroy workflow visibility and increase coupling. Split by
cohesive responsibility and independent change, not method count.

### Declaring every large class an SRP violation

Measure reasons to change and state/invariant cohesion. A substantial state
machine or use-case coordinator may be cohesive.

### Calling a class "Service" to avoid ownership

A service name does not justify unrelated behavior. State whether it is a
domain operation, use-case controller, external boundary, query, or technical
fabrication.

### Abstracting every conditional

Lifecycle branches and simple validations often belong directly in guarded
methods. Use polymorphism for a real varying behavior axis.

### Designing for unlimited extension

OCP applies to selected variation. Universal plugin systems add complexity and
usually choose the wrong abstraction before requirements exist.

### Treating OCP as "never modify code"

New domain invariants legitimately change core classes. Protect stable
workflows from known variation, not every line from all future edits.

### Checking LSP by signatures only

Substitution includes preconditions, results, failures, mutation, side effects,
idempotency, and temporal behavior.

### Subclasses that disable parent behavior

Raising `NotImplementedError`, silently doing nothing, or rejecting inputs the
base promises usually means the hierarchy is false or the base contract too
broad.

### Marker interfaces with no client contract

An empty or broad interface used only for naming does not automatically improve
ISP or DIP.

### One-method-interface explosion

ISP is about client-specific cohesion, not minimizing method count. Keep methods
together when clients and implementations need them together.

### Confusing dependency injection with DIP

Injecting a concrete provider improves construction control but leaves source
coupling to provider details. Depend on a consumer-oriented contract when the
boundary justifies it.

### Interface beside every implementation

Stable values/entities do not require mirror interfaces. Add a boundary for
variation, external detail, or test control.

### Provider-shaped abstractions

A `StripeChargeRequestFactory` exposed to booking policy is not inversion.
Translate provider data inside an adapter.

### Inheritance for reuse

If the subtype is not behaviorally substitutable, extract shared functions or
compose a collaborator instead.

### Treating composition as free

Every collaborator adds naming, wiring, navigation, and tests. Compose when
responsibility or variation earns the cost.

### Applying Tell, Don't Ask everywhere

Queries are necessary. Prevent callers from making another object's protected
decision; do not force unrelated orchestration into an entity.

### Counting dots for Law of Demeter

The concern is leaked knowledge of internal topology, not fluent value or
collection syntax.

### DRYing coincidental similarity

A generic helper can couple two rules that should evolve independently. Share
knowledge with one reason to change.

### Using YAGNI to ignore correctness

Failure behavior, invariants, validation, and tests are current requirements,
not speculative features.

### Using KISS to create an anemic script

Simple design still protects state and makes critical dependencies explicit.

### Refactoring without tests

Responsibility movement can change ordering, failure state, and side effects.
Characterize behavior before structural changes.

### Ignoring the cost side of a principle

Every boundary and abstraction has a maintenance cost. Explain why the current
force outweighs it.

## Existing repository examples

### Parking Lot: focused variation contracts

- [`allocation.py`](../../solutions/parking-lot/strategies/allocation.py)
  separates spot selection from the parking workflow.
- [`pricing.py`](../../solutions/parking-lot/strategies/pricing.py) separates fee
  calculation from allocation and payment.
- [`parking_lot.py`](../../solutions/parking-lot/services/parking_lot.py) receives
  those policies and a payment processor through its constructor.
- The [SOLID review](../../solutions/parking-lot/README.md#14-solid-principles-in-this-design)
  connects each principle to the implementation.

Critical review:

- `datetime.now()` and UUID generation remain hidden dependencies; inject them
  if deterministic time/identity behavior becomes important.
- `ParkingLot` owns floor registry, tickets, locking, entry, exit, and payment
  ordering. It is compact and coherent in this scope, but future independent
  catalog/checkout change could justify separation.
- `float` pricing is educationally simple; financial exactness is a separate
  correctness concern.

### Movie Ticket Booking: protected variations

- [`PricingStrategy`](../../solutions/movie-ticket-booking/strategies/pricing_strategy.py)
  is a narrow calculation contract.
- [`PaymentGateway`](../../solutions/movie-ticket-booking/services/payment_gateway.py)
  isolates an external capability.
- [`BookingService`](../../solutions/movie-ticket-booking/services/booking_service.py)
  receives pricing, gateway, and clock dependencies.
- [`WeekendPricingDecorator`](../../solutions/movie-ticket-booking/strategies/weekend_pricing_decorator.py)
  composes pricing behavior instead of creating a subclass combination.
- The [OOP/SOLID review](../../solutions/movie-ticket-booking/README.md#15-oop-and-solid-lessons)
  maps design choices to the principles.

Critical review: transition fields are publicly mutable in some dataclasses.
Use the Topic 3 reference refactor to move single-object guards into `Booking`
and `ShowSeat`, while keeping multi-object/payment ordering in the service.

### ATM: dependency inversion at an external boundary

- [`BankGateway`](../../solutions/atm/services/bank_gateway.py) expresses ATM
  needs instead of tying the ATM to one remote-bank implementation.
- [`CashSelectionStrategy`](../../solutions/atm/strategies/cash_selection_strategy.py)
  isolates exact-note selection.
- The [gateway discussion](../../solutions/atm/README.md#18-bank-gateway-and-dependency-inversion)
  distinguishes policy from a provider adapter.

The hardware-failure workflow also demonstrates that clean abstractions do not
remove ordering/compensation complexity; they make collaborator responsibilities
visible.

### Elevator: substitution and pragmatic restraint

- [`SchedulingStrategy`](../../solutions/elevator/strategies/scheduling_strategy.py)
  defines one selection contract.
- [`DirectionAwareNearestStrategy`](../../solutions/elevator/strategies/direction_aware_nearest_strategy.py)
  implements it without changing the elevator controller.
- The [SOLID discussion](../../solutions/elevator/README.md#20-solid-principles)
  explicitly rejects premature State objects while enum-based transitions are
  sufficient.

This is a useful KISS/OCP balance: one proven algorithm axis is abstracted;
state behavior is not over-engineered.

### Coupon Platform: composition and client-sized rules

- [`EligibilityRule`](../../solutions/coupon-management-and-distribution-platform/strategies/eligibility_rule.py)
  is a narrow client contract.
- [`AllOfEligibilityRule`](../../solutions/coupon-management-and-distribution-platform/strategies/all_of_eligibility_rule.py)
  composes several independently testable rules.
- [`PercentageDiscount`](../../solutions/coupon-management-and-distribution-platform/strategies/percentage_discount.py)
  protects its numeric invariants.

Review whether each new coupon requirement is a composable rule, configuration,
or a change to campaign invariants before adding another class.

### Larger coordinators to review

- [`SplitwiseService`](../../solutions/splitwise/services/splitwise_service.py)
  coordinates users, groups, expenses, settlements, and balances.
- [`LibraryService`](../../solutions/library-management/services/library_service.py)
  coordinates catalog, loans, reservations, fines, notification, and histories.

Do not label them violations from size alone. Perform the actor/change/state
audit. Proposed splits must preserve shared invariants, transaction ordering,
and one source of truth rather than creating pass-through services.

## Practice exercises

### Exercise 1 - Core: fixed principle-recognition gate

Choose the primary diagnosis or principle:

`cohesion/SRP`, `OCP`, `LSP`, `ISP`, `DIP`, `encapsulation`, `composition`,
`Law of Demeter`, `DRY`, `YAGNI`, or `no violation yet`.

1. A booking service constructs a provider SDK inside `confirm()`.
2. A subtype raises `NotImplementedError` for a valid base operation.
3. A confirmation fake implements 20 unused reporting methods.
4. Adding pricing requires editing a central `if kind == ...` every month.
5. A controller assigns `booking.status` directly.
6. Two modules copy the same money-rounding business rule.
7. Checkout navigates `booking.show.screen.theatre.gateway.config`.
8. A subclass exists only to combine weekend and coupon behavior.
9. A generic plugin framework exists for one fixed implementation.
10. A 180-line booking coordinator sequences cohesive confirmation,
    cancellation, expiry, and retry workflows.
11. One class formats reports, calculates fines, sends mail, and mutates loans.
12. Constructor injection supplies a concrete `StripeClient` directly.
13. A method has an `if booking.status` guard inside `Booking.confirm()`.
14. Two similar loops calculate unrelated restaurant distance and tax brackets.
15. A charge implementation returns success without actually charging while the
    contract promises a completed provider outcome.

Scoring key:

1. DIP;
2. LSP;
3. ISP;
4. OCP;
5. encapsulation;
6. DRY;
7. Law of Demeter;
8. composition;
9. YAGNI;
10. no violation yet - audit change reasons before splitting;
11. cohesion/SRP;
12. DIP remains unresolved even though injection is present;
13. no violation yet - lifecycle branching belongs to the state owner;
14. no violation yet - similar syntax is not shared knowledge;
15. LSP.

Score one point each. Questions 1-7, 10, 12, and 15 are critical.

### Exercise 2 - Core: SRP and cohesion audit

Audit this `CommerceManager` responsibility list:

- register customer;
- update product catalog;
- calculate tax and discounts;
- reserve inventory;
- charge/refund payment;
- transition order state;
- send email/SMS;
- generate finance CSV;
- call `datetime.now()`;
- persist every object in dictionaries.

Deliver:

1. change axes/actors;
2. responsibilities that belong to domain objects;
3. varying policies;
4. external boundaries;
5. cohesive use-case controllers;
6. query/reporting boundary;
7. composition-root wiring;
8. responsibilities that should remain together for ordering;
9. before/after dependency sketch;
10. ten behavioral tests.

Twelve-point rubric:

- 2: order and inventory invariants move to clear owners/boundaries.
- 2: payment, notification, clock, and persistence are explicit dependencies.
- 2: pricing/tax variation is separated without a generic rules universe.
- 2: checkout/cancellation ordering remains visible and cohesive.
- 1: catalog/registration and finance reporting are not in checkout.
- 1: no duplicated source of truth is introduced.
- 1: split is justified by actors/change, not line count.
- 1: tests prove failure postconditions.

Pass at 10/12 with full points on domain ownership and external boundaries.

### Exercise 3 - Core: variation and OCP decision table

For each change, choose `direct modification`, `configuration/value`,
`polymorphic boundary`, or `defer with YAGNI`, and justify the axis:

1. Add one new fixed seat type with a base price table.
2. Add three independently selectable pricing algorithms.
3. Rename `PENDING` to `PENDING_PAYMENT` across the domain.
4. Support a second payment provider selected per merchant.
5. Add a speculative blockchain payment someday.
6. Change cancellation from full to per-seat partial cancellation.
7. Change hold duration from five to seven minutes by deployment.
8. Add a second matching algorithm for elevators.
9. Add one required validation to all money values.
10. Add taxes whose formulas vary by jurisdiction.

Expected decisions:

1. configuration/value unless behavior differs;
2. polymorphic boundary;
3. direct modification;
4. polymorphic/external boundary plus selection policy if required;
5. defer with YAGNI;
6. direct core-model modification;
7. configuration/value;
8. polymorphic boundary;
9. direct authoritative value-object modification;
10. polymorphic policy when jurisdictions truly vary.

Score one point each. Questions 3, 5, 6, and 9 test whether OCP is being
over-applied and are critical.

### Exercise 4 - Core: LSP contract audit

Contract:

```text
AllocationPolicy.select(candidates, request)
- accepts any finite candidate sequence, including empty;
- never mutates candidates;
- returns None or one object from candidates;
- returned candidate satisfies request;
- tie-breaking is deterministic;
```

Evaluate implementations:

A. Returns `None` for empty and nearest eligible candidate otherwise.
B. Raises `ValueError` for empty.
C. Sorts the caller's list in place, then returns an eligible member.
D. Constructs a new candidate not in the input.
E. Returns an ineligible candidate when none fits.
F. Uses candidate ID as a deterministic final tie-breaker.
G. Returns a different tied candidate randomly on each call.
H. Returns `None` even when eligible candidates exist.

Answer key:

- A and F can satisfy the contract.
- B strengthens the precondition.
- C violates no-mutation.
- D violates result membership.
- E violates eligibility.
- G violates determinism.
- H weakens the success postcondition.

Score one point each plus two points for writing reusable contract tests. Pass
at 9/10; B, C, D, E, and G are critical.

### Exercise 5 - Core: ISP client matrix

A provider interface contains:

```text
charge, refund, payout, search_transactions,
download_statement, verify_bank_account, send_receipt
```

Clients:

- checkout: `charge`;
- cancellation: `refund`;
- merchant settlement: `payout`, `verify_bank_account`;
- finance reporting: `search_transactions`, `download_statement`;
- notification worker: `send_receipt`.

Produce focused contracts, name their consumers, and decide whether one adapter
may implement several.

Required result:

- no client depends on unused capability groups;
- payment provider details remain outside contracts;
- checkout fake needs only charge;
- settlement methods remain cohesive together;
- receipt sending is not mislabeled as a payment responsibility;
- one concrete provider adapter may implement multiple protocols.

Pass by satisfying all six.

### Exercise 6 - Core: DIP and hidden-dependency refactor

Refactor a service that directly uses:

- `datetime.now()`;
- `uuid.uuid4()`;
- `StripeClient()`;
- `smtplib`;
- a global dictionary store.

For each dependency, decide:

1. whether it needs inversion in the current scope;
2. the smallest consumer-oriented contract;
3. injection/wiring location;
4. fake/test control;
5. what should remain concrete.

Required boundaries when behavior depends on them:

- `Clock`;
- `IdGenerator`;
- `ChargePort`/payment gateway;
- `Notifier`;
- store/repository contract if persistence replacement is in scope.

Do not wrap pure stable domain values or every built-in collection. Pass when a
unit test runs without real time, random IDs, network, email, or global state,
and the composition root is the only concrete wiring location.

### Exercise 7 - Core: DRY, KISS, and YAGNI decisions

Classify each proposal as `do now`, `wait for evidence`, or `reject`:

1. Centralize copied money rounding used in five financial workflows.
2. Generalize two similar loops from unrelated domains into `ThingProcessor`.
3. Add a controlled clock because hold expiry is a current requirement.
4. Build event sourcing in a 60-minute in-memory interview.
5. Add one `DateRange` value used by booking and maintenance overlap.
6. Create an abstract factory for one stable value object.
7. Duplicate a three-line test setup to keep two scenarios clear.
8. Centralize legal booking transitions repeated in four controllers.
9. Design support for 30 imagined discount combinations before requirements.
10. Keep a direct entity method with one lifecycle `if`.

Expected:

1. do now;
2. reject;
3. do now;
4. reject/defer outside scope;
5. do now when semantics are identical;
6. reject;
7. wait/accept local duplication;
8. do now in the state owner;
9. reject;
10. do now/keep simple.

Score one point each. Questions 2, 3, 8, and 10 are critical.

### Exercise 8 - Core and timed: refactor Order Checkout

In 45 minutes, start with one `OrderManager` containing branches for:

- item validation;
- inventory reservation;
- standard/VIP pricing;
- system time;
- payment provider calls;
- order status assignment;
- notification;
- in-memory storage.

Requirements:

- reservation is all-or-none;
- failed payment releases inventory;
- successful payment confirms the order;
- notification failure does not reverse confirmation;
- VIP pricing is replaceable;
- tests control time/payment/notification;
- no distributed or persistent implementation is required.

Deliver:

- 8 minutes: change/responsibility map;
- 27 minutes: refactor with tests;
- 10 minutes: add a second pricing policy and explain trade-offs.

Fifteen-point rubric:

- 2: order/inventory invariants have clear owners.
- 2: checkout retains correct cross-object ordering.
- 2: price variation uses one justified narrow contract.
- 2: time/payment/notification are controlled boundaries.
- 2: payment failure releases inventory and preserves valid order state.
- 1: notification failure leaves confirmed order intact.
- 1: second pricing policy does not edit checkout.
- 1: implementations satisfy shared contracts.
- 1: composition root owns concrete wiring.
- 1: no speculative factory/event/rules framework is added.

Pass at 12/15 with full points on inventory/payment failure ordering.

### Exercise 9 - Core: repository service audit

Choose one:

- [`BookingService`](../../solutions/movie-ticket-booking/services/booking_service.py);
- [`SplitwiseService`](../../solutions/splitwise/services/splitwise_service.py);
- [`LibraryService`](../../solutions/library-management/services/library_service.py).

Produce:

1. public method/change-axis table;
2. owned state and collaborator map;
3. rules that belong to entities/values;
4. external/volatile boundaries;
5. current strengths;
6. actual cohesion/coupling risks;
7. one minimal refactor justified by a current test/change;
8. one proposed split you reject as overengineering;
9. focused regression tests;
10. before/after trade-off statement.

Completion requires evidence from code and tests. "The file is long" earns no
credit.

### Exercise 10 - Timed change-pressure drill

Apply this change to Exercise 8 in 15 minutes:

> A high-value order requires fraud approval after inventory reservation but
> before payment. A declined review releases inventory. Normal orders must not
> depend on provider-specific fraud data.

Expected impact:

- introduce a consumer-oriented `FraudCheck` boundary only because the
  requirement is now real;
- keep fraud provider types in an adapter;
- place selection threshold in configuration/policy;
- sequence validation -> reservation -> fraud -> payment;
- release inventory on fraud decline;
- normal flow uses an approve/no-review result under the same contract or a
  cohesive conditional policy;
- add contract tests and unchanged normal-order regression;
- avoid modifying pricing, notification, or order value types.

Pass when the change is localized, failure state is correct, and no speculative
fraud framework appears.

## Interview self-check

Answer without notes. Give one point per complete answer.

1. What problem do design principles solve?
2. What is a reason to change?
3. What is high cohesion?
4. Why is class size not an SRP test?
5. What is healthy coupling?
6. Name four coupling dimensions.
7. Distinguish encapsulation and information hiding.
8. State SRP in practical terms.
9. When can a coordinator remain cohesive?
10. State OCP relative to a variation axis.
11. Why does OCP not mean no modification?
12. When should a conditional remain a conditional?
13. State LSP behaviorally.
14. How can a subtype strengthen a precondition?
15. How can it weaken a postcondition?
16. What else besides signatures belongs to a contract?
17. How do contract tests support LSP?
18. State ISP from the client's perspective.
19. Why is one-method-per-interface not the goal?
20. State DIP and dependency direction.
21. Distinguish DIP from dependency injection.
22. What is a composition root?
23. When is an interface not worth adding?
24. Explain Information Expert with authority.
25. What is a Controller responsibility?
26. What is Pure Fabrication?
27. What does Protected Variations accomplish?
28. When is inheritance preferable to composition?
29. What does Tell, Don't Ask prevent?
30. Why is Law of Demeter not a dot-count rule?
31. Distinguish DRY knowledge from similar syntax.
32. How do KISS and YAGNI differ?
33. Why can principles conflict?
34. How do you test SRP/OCP through change?
35. What makes a principle-driven refactor successful?

Core questions: 3, 7, 8, 10, 13, 16, 18, 20, 21, 24, 28, and 31.

Expected answer points:

1. Manage responsibility, dependency, contracts, and change safely.
2. One actor/business/technical force that changes a cohesive unit.
3. Members support one clear purpose/state/invariant/change set.
4. Lines do not reveal actors, invariants, or independent changes.
5. Explicit necessary dependence on stable/domain-appropriate contracts.
6. Any four of breadth, strength, direction, volatility, temporal, data, global.
7. Group/protect state behavior versus hide volatile representation/decision.
8. One cohesive responsibility/reason/actor to change, not one method.
9. When its steps form one use case with necessary shared ordering/boundary.
10. Extend a chosen proven variation without editing stable consumer workflow.
11. Core requirements/invariants legitimately change existing model code.
12. When it is simple lifecycle/validation or variation lacks independent
    change/substitution value.
13. Every subtype/implementation preserves client correctness and contract.
14. Reject input the abstraction declares valid or require more conditions.
15. Return less/incorrect guarantee or fail to act as promised.
16. Preconditions, postconditions, invariants, failures, mutation, side effects,
    idempotency, and ordering as relevant.
17. Run the same behavioral assertions against every implementation.
18. A client depends only on cohesive capabilities it needs.
19. Client/change cohesion, not method count, defines useful boundaries.
20. High-level policy and detail depend on a consumer-oriented abstraction;
    source direction points toward stable policy contract.
21. Architectural dependency rule versus construction technique.
22. Boundary where concrete implementations are selected and wired.
23. Stable concrete value/entity/helper with no volatility, alternative, or test
    control need.
24. Assign to the object with knowledge and authority to protect the rule.
25. Receive system event and coordinate, delegating domain decisions.
26. Non-domain type invented to preserve cohesion/low coupling for technical or
    application responsibility.
27. Places stable boundary around likely variation/volatility.
28. True meaningful subtype with full behavioral substitution and stable shared
    invariants.
29. Callers querying internal state to make the owner's protected decision.
30. It limits leaked topology knowledge, not harmless chained syntax.
31. One business decision/source versus code that merely looks alike.
32. KISS chooses understandable sufficient design; YAGNI defers unrequired
    capability.
33. Each optimizes a different force and adds costs/trade-offs.
34. Add the extension and measure whether changes stay in predicted owners while
    old tests remain green.
35. Preserved behavior plus a safer/localized target change at justified
    complexity cost.

Score at least 30/35 and answer every core question correctly.

## Quick review checklist

- [ ] I list concrete change axes before applying principles.
- [ ] Classes group state, rules, and methods that belong together.
- [ ] I evaluate SRP by reasons/actors, not size.
- [ ] Necessary domain coupling remains explicit.
- [ ] Volatile/external dependencies are behind narrow boundaries.
- [ ] Protected state changes through domain behavior.
- [ ] OCP is applied to a named, demonstrated variation axis.
- [ ] I do not treat OCP as a ban on core-model modification.
- [ ] Contracts define inputs, results, failures, mutation, and side effects.
- [ ] Every implementation passes shared substitutability tests.
- [ ] No subtype disables or weakens promised behavior.
- [ ] Interfaces match cohesive client needs.
- [ ] Test fakes implement no unrelated capabilities.
- [ ] High-level code does not import provider details.
- [ ] I distinguish DIP, injection, and composition-root wiring.
- [ ] I avoid mirror interfaces with no boundary/variation value.
- [ ] Information Expert also has authority to protect the rule.
- [ ] Controllers coordinate rather than owning every decision.
- [ ] Composition/inheritance choices follow lifecycle and substitution.
- [ ] Callers do not reach through deep graphs or edit foreign state.
- [ ] Commands and queries have unsurprising effects.
- [ ] DRY centralizes business knowledge, not coincidental syntax.
- [ ] KISS/YAGNI remove speculation without removing required correctness.
- [ ] Every abstraction has a stated benefit, cost, and revisit condition.
- [ ] A realistic change affects the predicted boundary and existing tests pass.

## Mastery gate

Topic 5 is complete only when all of the following are true:

- [ ] I score at least 30 out of 35 on the self-check without notes and answer
  every designated core question correctly.
- [ ] I score at least 13 out of 15 on the fixed recognition gate, including all
  ten critical cases.
- [ ] My CommerceManager responsibility audit scores at least 10 out of 12 with
  correct domain ownership and external boundaries.
- [ ] I score at least 9 out of 10 on the OCP decision table, including all four
  anti-overengineering cases.
- [ ] I score at least 9 out of 10 on the LSP audit, including every critical
  violation, and run one shared contract suite against two implementations.
- [ ] My ISP client matrix satisfies all six required outcomes.
- [ ] My DIP exercise runs with controlled time, IDs, payment, notification, and
  state without real external effects.
- [ ] I score at least 9 out of 10 on the DRY/KISS/YAGNI gate, including all
  critical cases.
- [ ] I refactor Order Checkout in 45 minutes and score at least 12 out of 15.
- [ ] I add the fraud-review change in 15 minutes with correct release ordering
  and no unrelated pricing/notification changes.
- [ ] I complete one evidence-based repository service audit and reject at least
  one unjustified abstraction.
- [ ] I demonstrate an OCP extension without modifying its stable consumer.
- [ ] I demonstrate LSP with behavioral contract tests, not type signatures.
- [ ] I explain DIP versus injection and inheritance versus composition using
  code I wrote.
- [ ] Every proposed abstraction names its current force, benefit, cost, and
  deletion/revisit condition.
- [ ] All original and new tests remain green after refactoring.

The readiness sentence for this topic is:

> I can diagnose cohesion, coupling, contracts, and dependency direction;
> apply SOLID and responsibility heuristics to a concrete change; test the
> improvement; and avoid abstractions whose cost exceeds their present value.

## Next topic

[**Topic 6 - Creational Design Patterns**](./06-creational-design-patterns.md)
builds on Topic 5's Creator, construction, dependency, and variation decisions
to cover Factory Method, Abstract Factory, Builder, Prototype, Singleton
trade-offs, and Python-native alternatives.
