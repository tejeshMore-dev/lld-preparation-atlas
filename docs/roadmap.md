# LLD Preparation Roadmap

This roadmap defines the order of study and the evidence required before LLD
preparation can be considered complete.

## Learning progression

Use the same progression for every topic:

`Understand -> Explain -> Model -> Implement -> Test -> Solve Timed -> Adapt`

- **Understand:** recognize the vocabulary and core rules.
- **Explain:** teach the idea without notes.
- **Model:** apply it to a supplied problem.
- **Implement:** express it correctly in Python.
- **Test:** prove normal, boundary, and failure behavior.
- **Solve Timed:** complete the task within an interview constraint.
- **Adapt:** handle a follow-up requirement without unnecessary rewriting.

## Curriculum order

| Topic | Name | Depends on | Status |
|---:|---|---|---|
| 1 | [Requirements Analysis and Scope Definition](./topics/01-requirements-analysis.md) | None | Complete |
| 2 | [Python and Object-Oriented Foundations](./topics/02-python-oop-foundations.md) | Topic 1 | Complete |
| 3 | [Domain Modeling and Responsibility Assignment](./topics/03-domain-modeling-and-responsibility-assignment.md) | Topics 1-2 | Complete |
| 4 | [UML and Interaction Modeling](./topics/04-uml-and-interaction-modeling.md) | Topic 3 | Complete |
| 5 | [Design Principles and Heuristics](./topics/05-design-principles-and-heuristics.md) | Topics 2-3 | Complete |
| 6 | [Creational Design Patterns](./topics/06-creational-design-patterns.md) | Topics 2, 5 | Complete |
| 7 | [Structural Design Patterns](./topics/07-structural-design-patterns.md) | Topics 2, 5 | Complete |
| 8 | [Behavioral Design Patterns](./topics/08-behavioral-design-patterns.md) | Topics 2, 5 | Complete |
| 9 | [Application Patterns and Reusable Building Blocks](./topics/09-application-patterns-and-reusable-building-blocks.md) | Topics 3, 5-8 | Complete |
| 10 | [API Contracts and Error Modeling](./topics/10-api-contracts-and-error-modeling.md) | Topics 3, 5, 9 | Complete |
| 11 | [Concurrency and Thread Safety](./topics/11-concurrency-and-thread-safety.md) | Topics 2-3, 10 | Complete |
| 12 | [Persistence and Transaction Boundaries](./topics/12-persistence-and-transaction-boundaries.md) | Topics 3, 9-11 | Complete |
| 13 | [Clean Code and Refactoring](./topics/13-clean-code-and-refactoring.md) | Topics 2-12 | Complete |
| 14 | [Testing Low-Level Designs](./topics/14-testing-low-level-designs.md) | Topics 2-13 | Complete |
| 15 | [Interview Execution, Problem Practice, and Readiness](./topics/15-interview-execution-problem-practice-and-readiness.md) | All previous topics | Complete |

**Bible content progress:** 15 of 15 topics complete (100%). This tracks authored
curriculum content, not an individual's mastery evidence.

## Recommended preparation phases

### Phase 1 - Frame and model

- Topics 1-4.
- Produce bounded requirements, object models, relationships, and interaction
  flows before using named patterns.

### Phase 2 - Design for change

- Topics 5-10.
- Apply principles and patterns only where requirements create a genuine
  variation or boundary.

### Phase 3 - Make it robust

- Topics 11-14.
- Handle shared state, persistence, failure ordering, refactoring, and testing.

### Phase 4 - Perform under interview conditions

- Topic 15.
- Solve unfamiliar problems, communicate trade-offs, write runnable code, and
  respond to requirement changes under time pressure.

## Overall definition of done

Preparation is complete when all of these are true:

- [ ] Every essential topic mastery gate has been passed.
- [ ] At least 12 varied LLD problems have been designed independently.
- [ ] At least 8 problems have been implemented end to end with tests.
- [ ] At least 5 timed mock interviews have been completed.
- [ ] Three consecutive unseen mocks scored at least 80/100, with no critical
  failure and no major hints.
- [ ] At least 3 mocks included a follow-up requirement change.
- [ ] Core code was compiling or logically complete within 45-60 minutes.
- [ ] Designs consistently covered requirements, invariants, failures, tests,
  relevant concurrency, and important trade-offs.
- [ ] No design depends on memorizing one solution or forcing patterns.

Use the [readiness checklist](./practice/readiness-checklist.md) and
[mock-interview rubric](./practice/mock-interview-rubric.md), preserving each
attempt with the [attempt-log template](./practice/attempt-log-template.md), for
the final assessment.
