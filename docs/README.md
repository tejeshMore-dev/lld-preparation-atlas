# LLD Curriculum

This curriculum is deliberately compact. Read a chapter, explain its main decision in your own words, then apply it to a problem.

## Core path

| Step | Topic | Question it answers |
|---:|---|---|
| 1 | [Requirements](./topics/01-requirements-analysis.md) | What exactly are we building? |
| 2 | [Python and OOP](./topics/02-python-oop-foundations.md) | How should objects expose behavior? |
| 3 | [Domain modeling](./topics/03-domain-modeling-and-responsibility-assignment.md) | Which object owns each rule? |
| 4 | [Design principles](./topics/05-design-principles-and-heuristics.md) | Where should change be isolated? |
| 5 | [Behavioral patterns](./topics/08-behavioral-design-patterns.md) | How should policies and workflows vary? |
| 6 | [Concurrency](./topics/11-concurrency-and-thread-safety.md) | Which check-and-change must be atomic? |
| 7 | [Interview execution](./topics/15-interview-execution-problem-practice-and-readiness.md) | How do I deliver under time pressure? |

## Pattern reference

Patterns are a vocabulary, not a checklist.

- [Creational patterns](./topics/06-creational-design-patterns.md)
- [Structural patterns](./topics/07-structural-design-patterns.md)
- [Behavioral patterns](./topics/08-behavioral-design-patterns.md)

## Extended path

These chapters go beyond the usual introductory LLD curriculum.

- [UML and interaction modeling](./topics/04-uml-and-interaction-modeling.md)
- [Application patterns](./topics/09-application-patterns-and-reusable-building-blocks.md)
- [API contracts and errors](./topics/10-api-contracts-and-error-modeling.md)
- [Persistence and transactions](./topics/12-persistence-and-transaction-boundaries.md)
- [Clean code and refactoring](./topics/13-clean-code-and-refactoring.md)
- [Testing LLDs](./topics/14-testing-low-level-designs.md)

## How to study a chapter

1. Read the core idea and decision table.
2. Recreate the small example without looking.
3. Name one situation where the technique is unnecessary.
4. Apply it to a [problem breakdown](../solutions/README.md).
5. Stop when the readiness check is true.

Follow the [roadmap](./roadmap.md) for a complete preparation plan. Use the [practice kit](./practice/README.md) for timed attempts.
