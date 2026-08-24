# LLD Preparation Bible

This directory is the learning hub for low-level design and machine-coding
interview preparation in Python 3.10+.

The material is split by major topic so each chapter can be learned, practised,
reviewed, and updated independently. The solution implementations live under
[`solutions/`](../solutions/).

Use the live [LLD Preparation Lab](https://tejeshmore-dev.github.io/lld-preparation-atlas/)
to mark personal topic progress. Checkbox state is stored privately in the
browser and can be exported as a JSON backup.

## Start here

1. Read the [preparation roadmap](./roadmap.md).
2. Complete [Topic 1 - Requirements Analysis](./topics/01-requirements-analysis.md).
3. Complete [Topic 2 - Python and OOP Foundations](./topics/02-python-oop-foundations.md).
4. Complete [Topic 3 - Domain Modeling and Responsibility Assignment](./topics/03-domain-modeling-and-responsibility-assignment.md).
5. Complete [Topic 4 - UML and Interaction Modeling](./topics/04-uml-and-interaction-modeling.md).
6. Complete [Topic 5 - Design Principles and Heuristics](./topics/05-design-principles-and-heuristics.md).
7. Complete [Topic 6 - Creational Design Patterns](./topics/06-creational-design-patterns.md).
8. Complete [Topic 7 - Structural Design Patterns](./topics/07-structural-design-patterns.md).
9. Complete [Topic 8 - Behavioral Design Patterns](./topics/08-behavioral-design-patterns.md).
10. Complete [Topic 9 - Application Patterns and Reusable Building Blocks](./topics/09-application-patterns-and-reusable-building-blocks.md).
11. Complete [Topic 10 - API Contracts and Error Modeling](./topics/10-api-contracts-and-error-modeling.md).
12. Complete [Topic 11 - Concurrency and Thread Safety](./topics/11-concurrency-and-thread-safety.md).
13. Complete [Topic 12 - Persistence and Transaction Boundaries](./topics/12-persistence-and-transaction-boundaries.md).
14. Complete [Topic 13 - Clean Code and Refactoring](./topics/13-clean-code-and-refactoring.md).
15. Complete [Topic 14 - Testing Low-Level Designs](./topics/14-testing-low-level-designs.md).
16. Complete [Topic 15 - Interview Execution, Problem Practice, and Readiness](./topics/15-interview-execution-problem-practice-and-readiness.md).
17. Use the linked implementations to review real code and tests.
18. Mark a topic complete only after passing its mastery gate.

## Topic index

| Topic | Chapter | Status |
|---:|---|---|
| 1 | [Requirements Analysis and Scope Definition](./topics/01-requirements-analysis.md) | Complete |
| 2 | [Python and Object-Oriented Foundations](./topics/02-python-oop-foundations.md) | Complete |
| 3 | [Domain Modeling and Responsibility Assignment](./topics/03-domain-modeling-and-responsibility-assignment.md) | Complete |
| 4 | [UML and Interaction Modeling](./topics/04-uml-and-interaction-modeling.md) | Complete |
| 5 | [Design Principles and Heuristics](./topics/05-design-principles-and-heuristics.md) | Complete |
| 6 | [Creational Design Patterns](./topics/06-creational-design-patterns.md) | Complete |
| 7 | [Structural Design Patterns](./topics/07-structural-design-patterns.md) | Complete |
| 8 | [Behavioral Design Patterns](./topics/08-behavioral-design-patterns.md) | Complete |
| 9 | [Application Patterns and Reusable Building Blocks](./topics/09-application-patterns-and-reusable-building-blocks.md) | Complete |
| 10 | [API Contracts and Error Modeling](./topics/10-api-contracts-and-error-modeling.md) | Complete |
| 11 | [Concurrency and Thread Safety](./topics/11-concurrency-and-thread-safety.md) | Complete |
| 12 | [Persistence and Transaction Boundaries](./topics/12-persistence-and-transaction-boundaries.md) | Complete |
| 13 | [Clean Code and Refactoring](./topics/13-clean-code-and-refactoring.md) | Complete |
| 14 | [Testing Low-Level Designs](./topics/14-testing-low-level-designs.md) | Complete |
| 15 | [Interview Execution, Problem Practice, and Readiness](./topics/15-interview-execution-problem-practice-and-readiness.md) | Complete |

**Bible content progress:** 15 of 15 topics complete (100%). Personal readiness
is determined by Topic 15's portfolio and timed-mock mastery gate.

## Supporting material

- [Practice hub](./practice/README.md)
- [Problem catalogue](./practice/problem-catalog.md)
- [Interview workflow](./practice/interview-workflow.md)
- [Mock-interview rubric](./practice/mock-interview-rubric.md)
- [Practice attempt-log template](./practice/attempt-log-template.md)
- [Final readiness checklist](./practice/readiness-checklist.md)
- [LLD design-brief template](./templates/design-brief-template.md)
- [Solution README template](./templates/solution-readme-template.md)
- [Implemented solution catalogue](../solutions/README.md)

## Chapter workflow

Every topic follows the same progression:

`Understand -> Explain -> Model -> Implement -> Test -> Solve Timed -> Adapt`

Each chapter should include:

1. Outcome and scope boundary.
2. Learn.
3. Recognize.
4. Model.
5. Implement.
6. Test.
7. Adapt.
8. Common mistakes.
9. Repository examples.
10. Exercises, self-check, and mastery gate.

## LLD boundary

This Bible focuses on in-process design: requirements, objects,
responsibilities, interactions, APIs, state, failure handling, concurrency,
persistence boundaries, tests, and maintainability.

Capacity estimation, service decomposition, sharding, replication, distributed
consensus, and deployment topology belong mainly to high-level system design.
They appear here only when they change a local component contract.
