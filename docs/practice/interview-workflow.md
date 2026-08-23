# LLD Interview Workflow

Use this structure for a 45-60 minute design or machine-coding round.

| Stage | Target time | Output |
|---|---:|---|
| Restate and clarify | 5-8 minutes | Bounded requirements and assumptions |
| Model responsibilities | 8-10 minutes | Core objects, ownership, relationships, state |
| Define interactions | 5-8 minutes | Contracts and critical sequence |
| Implement critical path | 20-25 minutes | Runnable or logically complete core behavior |
| Test and review | 5-10 minutes | Edge cases, failures, trade-offs, follow-up change |

## Execution checklist

1. Clarify the objective, actors, and must-have use cases.
2. State assumptions and out-of-scope behavior.
3. Extract business rules and invariants.
4. Identify state owners and collaborators.
5. Define narrow public contracts.
6. Walk through one critical sequence before coding.
7. Implement the happy path without bypassing invariants.
8. Add validation, failure behavior, and tests.
9. Discuss concurrency or persistence only when relevant.
10. Apply a follow-up change and explain its impact.

## Communication rule

Narrate decisions and trade-offs, not every keystroke. If information is
missing, state the simplest reasonable assumption and continue.
