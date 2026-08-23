# LLD Preparation Bible

This directory is the learning hub for low-level design and machine-coding
interview preparation in Python 3.10+.

The material is split by major topic so each chapter can be learned, practised,
reviewed, and updated independently. The solution implementations live under
[`solutions/`](../solutions/).

## Start here

1. Read the [preparation roadmap](./roadmap.md).
2. Complete [Topic 1 - Requirements Analysis](./topics/01-requirements-analysis.md).
3. Complete [Topic 2 - Python and OOP Foundations](./topics/02-python-oop-foundations.md).
4. Complete [Topic 3 - Domain Modeling and Responsibility Assignment](./topics/03-domain-modeling-and-responsibility-assignment.md).
5. Complete [Topic 4 - UML and Interaction Modeling](./topics/04-uml-and-interaction-modeling.md).
6. Complete [Topic 5 - Design Principles and Heuristics](./topics/05-design-principles-and-heuristics.md).
7. Complete [Topic 6 - Creational Design Patterns](./topics/06-creational-design-patterns.md).
8. Complete [Topic 7 - Structural Design Patterns](./topics/07-structural-design-patterns.md).
9. Use the linked implementations to review real code and tests.
10. Mark a topic complete only after passing its mastery gate.

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
| 8 | Behavioral Design Patterns | Planned |
| 9 | Application Patterns and Reusable Building Blocks | Planned |
| 10 | API Contracts and Error Modeling | Planned |
| 11 | Concurrency and Thread Safety | Planned |
| 12 | Persistence and Transaction Boundaries | Planned |
| 13 | Clean Code and Refactoring | Planned |
| 14 | Testing Low-Level Designs | Planned |
| 15 | Interview Execution, Problem Practice, and Readiness | Planned |

## Supporting material

- [Practice hub](./practice/README.md)
- [Problem catalogue](./practice/problem-catalog.md)
- [Interview workflow](./practice/interview-workflow.md)
- [Mock-interview rubric](./practice/mock-interview-rubric.md)
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
