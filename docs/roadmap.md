# LLD Roadmap

The shortest path to interview readiness is repeated design practice with feedback. Reading alone is not enough.

## Phase 1: Frame and model

Study Topics [1](./topics/01-requirements-analysis.md), [2](./topics/02-python-oop-foundations.md), and [3](./topics/03-domain-modeling-and-responsibility-assignment.md).

Deliverable: for two problems, write five core use cases, the main entities, and one invariant per entity.

## Phase 2: Design for change

Study Topic [5](./topics/05-design-principles-and-heuristics.md), then use the pattern chapters [6](./topics/06-creational-design-patterns.md), [7](./topics/07-structural-design-patterns.md), and [8](./topics/08-behavioral-design-patterns.md) as references.

Deliverable: implement two problems. Add one follow-up requirement to each without rewriting the core model.

## Phase 3: Make it reliable

Study concurrency [11](./topics/11-concurrency-and-thread-safety.md) and testing [14](./topics/14-testing-low-level-designs.md). Add APIs [10](./topics/10-api-contracts-and-error-modeling.md) and persistence [12](./topics/12-persistence-and-transaction-boundaries.md) when the problem needs them.

Deliverable: identify a race, define the atomic boundary, and test a failure path in two implementations.

## Phase 4: Perform under pressure

Use the [interview workflow](./practice/interview-workflow.md) and Topic [15](./topics/15-interview-execution-problem-practice-and-readiness.md).

Complete three 45–60 minute unseen mocks. After each attempt, record:

- the first wrong assumption;
- the weakest invariant;
- the largest unnecessary abstraction;
- the follow-up that caused the most change.

## Suggested order

| Week | Focus | Practice |
|---|---|---|
| 1 | requirements, OOP, modeling | Parking Lot |
| 2 | principles and patterns | Connect Four, Elevator |
| 3 | concurrency and tests | Movie Booking, Inventory |
| 4 | timed delivery | three unseen problems |

## Ready means

You are ready when you can repeatedly:

- narrow ambiguous scope in under five minutes;
- explain why each important class exists;
- trace one workflow and one failure end to end;
- keep shared check-and-update operations atomic;
- write a runnable vertical slice with focused tests;
- absorb a follow-up without a redesign.

Track attempts with the [attempt log](./practice/attempt-log-template.md), not with hours studied.
