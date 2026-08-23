# Topic 1 - Requirements Analysis and Scope Definition

[Curriculum index](../README.md) | [Preparation roadmap](../roadmap.md)

- **Category:** LLD problem-solving mindset
- **Difficulty:** Beginner
- **Priority:** Essential
- **Prerequisites:** None beyond basic programming
- **Running example:** Parking Lot
- **Output:** A concise, testable LLD design brief

## Outcome

After completing this topic, you should be able to take a vague prompt such as
"Design a parking lot" and, within five to eight minutes:

- Establish the system goal and interview scope.
- Identify actors and must-have use cases.
- Extract business rules and invariants.
- Discover important alternate and failure flows.
- Separate requirements, assumptions, and design decisions.
- Decide which concurrency, persistence, and external-system concerns matter.
- State what is deliberately out of scope.
- Turn requirements into testable acceptance scenarios.
- Freeze a reasonable version-one scope and begin modeling.

## Core idea

A vague interview prompt is not a specification. Before selecting classes,
interfaces, or patterns, convert it into a bounded problem.

```text
Vague prompt
    -> domain vocabulary
    -> actors and use cases
    -> rules and invariants
    -> failures and constraints
    -> explicit scope
    -> acceptance scenarios
    -> object model
```

Requirements tell you **what must be true**. Design tells you **how the code
will make it true**. Mixing the two too early produces unnecessary classes,
missing behaviors, and designs optimized for assumptions the interviewer never
made.

## 1. Learn

### 1.1 Classify every statement

During clarification, classify information instead of keeping an unstructured
list of notes.

| Category | Question it answers | Example |
|---|---|---|
| Goal | Why does this system exist? | Park and retrieve vehicles safely |
| Actor | Who or what interacts with it? | Driver, attendant, payment provider |
| Use case | What must an actor accomplish? | Park a vehicle |
| Business rule | What domain policy applies? | A truck requires a large spot |
| Invariant | What must never become false? | One spot cannot hold two vehicles |
| Constraint | What limits the solution? | Complete an in-memory design in 60 minutes |
| Quality requirement | How well must it behave? | Concurrent entries must not assign the same spot |
| Assumption | What are we temporarily treating as true? | One parking-lot location |
| Out of scope | What are we intentionally excluding? | Monthly subscriptions |
| Acceptance scenario | How will we verify behavior? | Parking fails when no compatible spot exists |
| Design decision | How will we implement it? | Use an allocation-policy interface |

The last row is intentionally different. "Support different allocation rules"
is a requirement. "Create `SpotAllocationStrategy`" is a design decision. Do
not present an implementation choice as though the interviewer requested it.

### 1.2 Functional requirements

Functional requirements describe observable behavior. Express them with a
verb and a domain outcome.

Good examples:

- Register parking floors and spots.
- Park a supported vehicle in a compatible available spot.
- Issue a ticket for a successful entry.
- Calculate the fee when a vehicle exits.
- Complete payment before releasing the spot.
- Report current availability by spot type.

Weak examples:

- Have a `ParkingLot` class.
- Use a factory.
- Store tickets in a dictionary.

The weak examples are implementation choices, not user-visible capabilities.

### 1.3 Business rules and invariants

A business rule describes allowed behavior. An invariant is a rule that must
remain true across every operation and state transition.

Parking-lot examples:

- A motorcycle fits a regular, compact, or large spot.
- A car fits a compact or large spot.
- A truck fits only a large spot.
- An occupied spot cannot be allocated.
- A vehicle cannot have two active tickets.
- A ticket is paid at most once.
- A spot becomes available only after a successful exit.

The most valuable requirements often contain words such as `must`, `cannot`,
`exactly one`, `at most one`, `only after`, or `until`. These phrases usually
become validations, state transitions, atomic operations, or database
constraints later.

### 1.4 Actors and system boundaries

An actor is anything outside the current design boundary that initiates or
participates in a use case.

Possible parking-lot actors:

- Driver or parking attendant.
- Entry gate.
- Exit gate.
- Payment provider.
- Administrator.

Actors are not automatically classes. An actor helps discover inputs, outputs,
and external dependencies. The system boundary determines what the interview
solution owns.

For example, the design may own ticket state but only call a payment-provider
contract. It does not need to implement a bank.

### 1.5 Use cases and flows

For each must-have use case, identify three kinds of flow:

1. **Happy flow:** the intended operation succeeds.
2. **Alternate flow:** a valid variation takes another path.
3. **Failure flow:** a rule or dependency prevents completion.

Example for `park vehicle`:

```text
Happy:
Vehicle arrives -> compatible spot is found -> spot is occupied -> ticket is issued

Alternate:
Vehicle arrives -> several spots fit -> configured allocation policy selects one

Failure:
Vehicle arrives -> no compatible spot exists -> request fails without changing state
```

The final phrase is important. A failure should not leave half-completed state.
That observation later influences method boundaries, exception handling,
transactions, and tests.

### 1.6 Relevant non-functional requirements

Only discuss qualities that affect this LLD. Convert vague adjectives into a
specific behavioral constraint.

| Vague request | Useful LLD clarification |
|---|---|
| It should be scalable | Which in-process operation or state should be replaceable? |
| It should be fast | What operation is frequent, and what response-time expectation matters? |
| It should be reliable | What happens when payment succeeds but a later step fails? |
| It should support concurrency | Which operations may occur simultaneously on the same resource? |
| It should be extensible | Which rules are expected to vary: pricing, allocation, or payment? |
| It should be maintainable | Which responsibilities should change independently? |

Common LLD-relevant qualities include:

- Thread safety around shared in-memory state.
- Deterministic behavior for testing.
- Replaceable policies or external integrations.
- Idempotent retry behavior.
- Validation and meaningful failure contracts.
- Auditable state transitions.

Do not begin a distributed-systems discussion unless the prompt or interviewer
requires it.

### 1.7 Assumptions, constraints, and out-of-scope items

These terms should not be used interchangeably.

- **Assumption:** a temporary interpretation used because information is
  missing, such as "one parking-lot location."
- **Constraint:** a fixed limit, such as "use only in-memory storage."
- **Out of scope:** a capability intentionally excluded from this version,
  such as advance reservations.

Say assumptions aloud. Silent assumptions are difficult for an interviewer to
correct and often become hidden bugs.

### 1.8 Prioritize the scope

Split requirements into three levels:

- **Must:** required for the core workflow to make sense.
- **Should:** valuable after the critical path works.
- **Could:** a reasonable extension, not part of version one.

For a 45-60 minute parking-lot interview:

| Priority | Candidate scope |
|---|---|
| Must | Add spots, park, issue ticket, calculate fee, pay, exit |
| Should | Multiple allocation and pricing policies, availability query |
| Could | Reservations, passes, lost tickets, electric charging, multiple locations |

This prevents a large product wishlist from consuming the design round.

### 1.9 Freeze version one

Clarification has diminishing returns. After approximately five to eight
minutes:

1. Summarize the agreed must-have scope.
2. State any assumptions still needed.
3. State what is deferred.
4. Ask for confirmation.
5. Begin the model.

If the interviewer does not answer a question, choose the simplest reasonable
assumption, state it, and continue.

## 2. Recognize

Certain prompt words reveal hidden design concerns.

| Prompt signal | Concern to clarify |
|---|---|
| Multiple, different, configurable | A rule or implementation may vary |
| Only one, exactly one, at most one | Cardinality or invariant |
| Simultaneously, multiple gates, concurrent | Atomicity and thread safety |
| Expires, scheduled, after N minutes | Time source and lifecycle |
| Retry, duplicate request | Idempotency |
| Cancel, refund, undo | Reversal and state transitions |
| History, audit, report | Durable records and query needs |
| External provider | Dependency boundary and failure behavior |
| Priority, nearest, cheapest, best | Selection policy |
| Notify, publish, subscribe | Events and observers |
| Role, permission, owner | Authorization boundary |
| Money, percentage, tax | Precision, rounding, and currency rules |

### Questions to ask first

Use this order rather than randomly interviewing the interviewer:

1. **Goal:** What is the primary outcome of the system?
2. **Actors:** Who initiates the important operations?
3. **Core flows:** Which use cases must be designed or implemented today?
4. **Rules:** What makes an operation valid or invalid?
5. **Lifecycle:** What states exist, and which transitions are allowed?
6. **Failures:** What should happen when a dependency or operation fails?
7. **Variation:** Which policies or providers may change?
8. **Shared state:** Can requests touch the same resource concurrently?
9. **Storage:** Is the solution in-memory, persistent, or abstracted?
10. **Boundary:** What should explicitly remain outside this round?

### Questions not to over-ask

Avoid spending interview time on details that do not affect the current model:

- UI colors and screen layout.
- Exact cloud provider or deployment topology.
- Massive-scale estimates in a pure machine-coding round.
- Every hypothetical future feature.
- Technology choices already fixed by the interviewer.

Ask a question because its answer changes the design, an invariant, a public
contract, or an important test.

## 3. Model

At this stage, model the problem boundary rather than the class structure. The
object model comes in later topics.

### 3.1 Running example: bounded Parking Lot brief

#### Objective

Design an in-memory parking lot that assigns compatible spots, tracks active
parking sessions, charges for elapsed time, and releases spots after successful
payment.

#### Actors

- Entry operator or entry gate.
- Exit operator or exit gate.
- Administrator configuring floors and spots.
- External payment provider.

#### Must-have use cases

1. Add a floor and uniquely identified spots.
2. Park a supported vehicle.
3. Issue an entry ticket.
4. Calculate an exit fee.
5. Pay and complete an exit.
6. Query available spots.

#### Business rules and invariants

1. Floor IDs and spot IDs are unique within the parking lot.
2. Only compatible spots may be assigned.
3. An occupied spot cannot be assigned again.
4. A vehicle has at most one active ticket.
5. A successful entry creates exactly one active ticket.
6. An invalid or failed entry changes no occupancy state.
7. The fee is never negative and has a defined minimum billing unit.
8. A failed payment does not release the spot.
9. A successful exit closes the ticket and releases its spot exactly once.

#### Assumptions

- One parking-lot location with multiple floors.
- Motorcycles, cars, and trucks are supported.
- Spot inventory is configured before use.
- A single currency is used.
- Time is supplied by the application and can be controlled in tests.
- Payment is represented by an external contract rather than a banking system.

#### Version-one quality requirements

- Core state changes must be safe when entry and exit calls run concurrently.
- Pricing, allocation, and payment implementations should be replaceable.
- Business behavior should be testable without sleeping or calling a real
  payment service.

#### Out of scope

- Advance reservations.
- Monthly subscriptions and loyalty programs.
- Lost-ticket workflow.
- Electric-vehicle charging.
- Multiple parking-lot locations.
- Database schema and distributed coordination.
- Physical gate and sensor protocols.

#### Open questions

- Should an oversized spot be used when the ideal size is unavailable?
- Is payment retry allowed on the same active ticket?
- Which instant determines the pricing rule: entry or exit time?

An open question is not permission to stall. Choose and state a simple default
if no answer is available.

### 3.2 Requirement-to-behavior traceability

Before naming classes, connect each major requirement to behavior and a test.

| ID | Requirement | Required behavior | Verification |
|---|---|---|---|
| R1 | Park a compatible vehicle | Select and reserve one valid free spot | Ticket identifies a compatible occupied spot |
| R2 | Prevent duplicate parking | Reject a second active session for the same vehicle | Second entry fails and state is unchanged |
| R3 | Charge for duration | Calculate a non-negative fee from entry and exit time | Boundary-duration examples return expected fees |
| R4 | Pay before exit | Release the spot only after payment success | Failed payment leaves ticket and spot active |
| R5 | Support concurrent entry | Make check-and-assign atomic | Two requests cannot receive the same spot |

This table becomes the bridge to object responsibilities, methods, locks, and
tests in later topics.

### 3.3 Acceptance scenarios

Use concise Given/When/Then statements when a rule needs precision.

```text
Scenario: park a car successfully
Given a compatible free spot exists
When a car enters
Then one compatible spot becomes occupied
And one active ticket is returned

Scenario: reject duplicate active parking
Given a vehicle already has an active ticket
When the same vehicle attempts to enter again
Then the request is rejected
And the original ticket and occupancy remain unchanged

Scenario: preserve state after failed payment
Given an active ticket exists
And the payment provider declines the charge
When the vehicle attempts to exit
Then the ticket remains active
And the spot remains occupied
```

Acceptance scenarios are not a replacement for unit tests. They make the
requirements precise enough that later tests can be written without guessing.

## 4. Implement the requirements artifact

The implementation output of this topic is a design brief, not production
code. Use the following template at the beginning of every LLD problem.

```markdown
# <Problem> - LLD Design Brief

## Objective
<One or two sentences defining the system outcome.>

## Interview contract
- Time available:
- Expected output: diagram / code sketch / runnable code
- Language and storage constraints:

## Actors
- ...

## Domain vocabulary
| Term | Meaning |
|---|---|
| ... | ... |

## Must-have use cases
1. ...

## Business rules and invariants
1. ...

## Alternate and failure flows
- ...

## Relevant quality requirements
- ...

## External dependencies
- ...

## Assumptions
- ...

## Out of scope
- ...

## Open questions
- ...

## Acceptance scenarios
- Given ... when ... then ...

## Likely follow-up changes
- ...
```

### Interview narration

A clear transition from requirements to design sounds like this:

> I will focus on parking, ticketing, pricing, payment, and exit for one
> multi-floor location. I am treating reservations, subscriptions, and durable
> storage as out of scope. The key invariants are unique active parking per
> vehicle, exclusive spot occupancy, compatibility, and releasing a spot only
> after successful payment. I will now assign these responsibilities to the
> model and walk through entry and exit.

This summary gives the interviewer a chance to correct the scope before code
is built on top of it.

## 5. Test the requirements

Requirements themselves need quality checks.

### Completeness check

- Does every must-have use case have a clear success outcome?
- Are important alternate and failure flows included?
- Are lifecycle boundaries such as create, cancel, expire, and complete clear?
- Are external dependencies and their failures acknowledged?
- Are time, money, identity, and shared-resource rules explicit when relevant?

### Consistency check

- Do any rules contradict each other?
- Can two actors perform operations that produce incompatible states?
- Does an out-of-scope statement conflict with a must-have use case?
- Is the same term used with one meaning throughout the brief?

### Testability check

- Can every must-have behavior be observed?
- Can vague words such as fast, flexible, and reliable be made concrete?
- Does every invariant have at least one positive or negative scenario?
- Can failure behavior be asserted without depending on a real external system?

### Scope check

- Can the critical path be designed or coded in the available time?
- Are HLD concerns excluded unless they affect local contracts?
- Have optional features been separated from must-have behavior?
- Is there enough flexibility for likely follow-up questions without building
  those features now?

## 6. Adapt

Interviewers often change a requirement to test whether the original scope and
model were thoughtful. Do not immediately rewrite the design. First classify
the change.

### Change-impact questions

1. Is this a new use case, rule, state, actor, dependency, or quality constraint?
2. Which existing invariant is affected?
3. Does a public contract need to change?
4. Is existing state still valid?
5. Which acceptance scenarios must be added or changed?
6. Was this an expected variation or a genuinely new responsibility?

### Parking Lot follow-up changes

#### Change A: weekend surcharge

- Classification: pricing-rule variation.
- Preserved invariants: occupancy, ticket uniqueness, and payment-before-exit.
- New acceptance need: the same stay may cost differently based on the chosen
  pricing time and day.

#### Change B: advance reservations

- Classification: new use case and new spot lifecycle states.
- Affected invariant: a spot may be unavailable without being occupied.
- New questions: expiry, cancellation, no-show behavior, and the relationship
  between a reservation and an entry ticket.

#### Change C: several entry gates

- Classification: concurrency requirement.
- Affected invariant: exclusive spot allocation must become an atomic check and
  state change.
- New acceptance need: simultaneous requests never receive the same spot.

Notice that requirement analysis identifies the impact without prematurely
choosing a design pattern or storage technology.

## Common mistakes

### Starting with classes

Writing `ParkingLot`, `Floor`, `Spot`, and `Vehicle` immediately feels
productive but can miss payment failure, duplicate entry, or concurrent
allocation. Discover behaviors and rules first.

### Treating nouns as requirements

A noun list is domain vocabulary, not a design. Requirements must explain what
the system does and what must remain true.

### Asking unlimited questions

The goal is not to recreate months of product discovery. Ask high-impact
questions, state reasonable assumptions, freeze version one, and proceed.

### Silently inventing scope

If you assume in-memory storage, one location, or one currency, say so. The
interviewer can then accept or correct the assumption.

### Solving HLD during an LLD round

Load balancers, shards, queues, and deployment regions are distractions unless
they affect the component contract being designed.

### Forcing patterns during clarification

"Use Strategy" is not a requirement. First establish that an algorithm or
policy must vary; pattern selection comes later.

### Ignoring failure behavior

Only describing successful flows creates partial mutations, ambiguous retries,
and missing states later.

### Using vague quality words

"Scalable" and "extensible" are not actionable until the expected variation or
constraint is identified.

### Designing every possible future feature

Capture likely changes, but implement only the agreed version-one scope. YAGNI
does not mean ignoring change; it means preparing sensible boundaries without
building speculative behavior.

## Existing repository examples

The current Parking Lot solution demonstrates how a bounded requirement set
becomes code and tests:

- [Parking Lot guide](../../solutions/parking-lot/README.md) - domain vocabulary,
  requirements, architecture, workflows, limitations, and advancement
  exercises.
- [Parking Lot service](../../solutions/parking-lot/services/parking_lot.py) - orchestration
  of the entry and exit rules.
- [Parking Spot model](../../solutions/parking-lot/models/parking_spots.py) - compatibility
  and occupancy invariants.
- [Parking Lot tests](../../solutions/parking-lot/tests/test_parking_lot.py) - executable
  examples of success and failure behavior.

When reviewing the solution, trace each rule in the README to the method that
enforces it and the test that proves it.

## Practice exercises

### Exercise 1: requirement or design decision?

Classify each statement and rewrite it if necessary:

1. The system supports hourly and daily pricing.
2. Create a `PricingStrategy` abstract class.
3. A user cannot reserve the same room twice for overlapping times.
4. Store bookings in a dictionary.
5. Failed notification delivery is retried at most three times.
6. Use the Observer pattern.

Expected categories:

1. Functional requirement or business-rule variation.
2. Design decision.
3. Invariant.
4. Design decision.
5. Failure and retry rule.
6. Design decision.

### Exercise 2: vague prompt expansion

For each prompt, write a design brief without drawing classes:

- Vending machine.
- Meeting-room booking.
- Splitwise-style expense sharing.
- Elevator system.
- Logging framework.

For each brief, include at least:

- Three must-have use cases.
- Five business rules or invariants.
- Three failure scenarios.
- Three assumptions.
- Three out-of-scope items.
- Five acceptance scenarios.

### Exercise 3: contradiction hunt

Review this fictional brief:

```text
A reservation guarantees a parking spot.
Spots are assigned only when a vehicle arrives.
Any available spot may be assigned to a walk-in driver.
Reservations never expire.
The system does not store reservations.
```

Identify the contradictions and missing lifecycle rules before proposing any
classes.

### Exercise 4: timed clarification drill

Take an unseen LLD prompt and spend no more than eight minutes producing:

1. Objective.
2. Actors.
3. Must-have use cases.
4. Invariants.
5. Failure flows.
6. Assumptions.
7. Out-of-scope list.
8. Acceptance scenarios.

Then explain the scope aloud in no more than ninety seconds.

### Exercise 5: change-impact drill

After completing a brief, randomly select one change:

- Add expiry.
- Add cancellation and refund.
- Add multiple providers.
- Add concurrent requests.
- Add audit history.
- Add a configurable selection policy.

Classify the change and identify affected rules, contracts, state, and tests.
Do not redesign the whole system.

## Interview self-check

Answer these without notes:

1. Why is a vague prompt not yet a specification?
2. What is the difference between a requirement and a design decision?
3. What is the difference between a business rule and an invariant?
4. How does an actor differ from a class?
5. What makes a non-functional requirement useful in LLD?
6. What is the difference between an assumption and a constraint?
7. Why should out-of-scope behavior be stated explicitly?
8. How do happy, alternate, and failure flows differ?
9. Which words in a prompt often reveal an invariant?
10. When should concurrency be discussed?
11. Why should an external payment system remain outside the design boundary?
12. How do acceptance scenarios improve the later design?
13. When should clarification stop?
14. How should you proceed when the interviewer does not answer a question?
15. How do you analyze a follow-up change without immediately rewriting code?

## Quick review checklist

Before moving from requirements to object modeling, verify:

- [ ] I can state the system objective in two sentences.
- [ ] Actors and system boundaries are explicit.
- [ ] Must-have use cases are prioritized.
- [ ] Domain terms have unambiguous meanings.
- [ ] Important invariants are written down.
- [ ] Happy, alternate, and failure flows are covered.
- [ ] Relevant concurrency, time, money, and persistence questions were asked.
- [ ] External systems are represented as boundaries, not implemented products.
- [ ] Assumptions are visible.
- [ ] Out-of-scope features are visible.
- [ ] Every core requirement has an acceptance scenario.
- [ ] Version one fits the interview time.
- [ ] Likely follow-up changes have been noted but not prematurely implemented.
- [ ] The interviewer has heard a concise scope summary.

## Mastery gate

Topic 1 is complete only when all of the following are true:

- [ ] I can produce a usable design brief for an unseen prompt in eight minutes.
- [ ] I can explain the agreed scope in ninety seconds without rambling.
- [ ] I consistently separate requirements, assumptions, constraints, and
  design decisions.
- [ ] I identify at least five meaningful invariants for a typical domain.
- [ ] I cover success, alternate, and failure behavior.
- [ ] I explicitly decide whether concurrency, persistence, time, money, and
  external dependencies matter.
- [ ] I trace every must-have requirement to at least one acceptance scenario.
- [ ] I can handle three follow-up changes by describing their impact before
  changing the design.
- [ ] I have completed this process for at least five different problem
  families.
- [ ] I no longer begin an LLD problem by immediately writing class names or
  choosing design patterns.

The readiness sentence for this topic is:

> I can turn an ambiguous LLD prompt into a bounded, internally consistent,
> testable version-one specification before designing classes.

## Next topic

[Topic 2 - Python and Object-Oriented Foundations](./02-python-oop-foundations.md)
will cover objects, state, behavior, identity, encapsulation, abstraction,
inheritance, polymorphism, composition, contracts, equality, hashing,
immutability, collections, typing, exceptions, and dependency injection.
