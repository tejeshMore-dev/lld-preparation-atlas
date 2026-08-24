# Final LLD Readiness Checklist

Preparation is complete only when the evidence is repeatable.

## Knowledge

- [ ] Every essential topic mastery gate is complete.
- [ ] Core principles and patterns can be explained without notes.
- [ ] Pattern choice can be justified, including when not to use it.

## Design

- [ ] At least 12 varied problems were designed independently.
- [ ] Requirements become responsibilities, contracts, state, and tests.
- [ ] Important invariants have one clear owner.
- [ ] Failure behavior and relevant concurrency are not ignored.

## Implementation

- [ ] At least 8 problems were implemented end to end.
- [ ] Core workflows compile and run.
- [ ] Tests cover happy paths, boundaries, invalid operations, and failures.
- [ ] Code avoids god classes, hidden dependencies, and leaked mutable state.

## Interview performance

- [ ] At least 5 timed mocks were completed.
- [ ] Three consecutive unseen mocks scored at least 80/100 with no critical
  failure and no major hint.
- [ ] At least 3 mocks included follow-up requirement changes.
- [ ] A normal problem can be completed in 45-60 minutes.
- [ ] Assumptions and trade-offs are communicated clearly.
- [ ] Every readiness mock has a preserved [attempt log](./attempt-log-template.md)
  with evidence, hints, follow-up, score, and repair history.

## Final readiness statement

> I can take an unfamiliar LLD prompt from clarification to a tested,
> explainable implementation under interview time, and I can adapt it when the
> requirements change.
