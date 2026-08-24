# LLD Mock-Interview Rubric

Score each category from `0` to its maximum and cite observable evidence. A pass
is at least `80/100` with no critical failure. A readiness-streak pass must also
be unseen and completed without a major hint.

| Category | Points |
|---|---:|
| Requirements, assumptions, and scope | 10 |
| Domain modeling and responsibility ownership | 15 |
| Relationships, state, and interaction flow | 10 |
| Interfaces and dependency boundaries | 10 |
| Invariants, validation, and failure behavior | 10 |
| Extensibility without overengineering | 10 |
| Code quality and language correctness | 15 |
| Tests and testability | 10 |
| Trade-offs and requirement adaptation | 5 |
| Communication and time management | 5 |
| **Total** | **100** |

## Critical failures

An interview does not pass if the design:

- Cannot satisfy a must-have use case.
- Allows a major invariant to be bypassed.
- Cannot be implemented coherently in the chosen language.
- Contains an unresolved data-loss, double-booking, or double-payment path.
- Depends on memorized classes but cannot handle a small requirement change.
- Receives so much guidance that the solution is no longer independent.

Classify guidance as clarification, minor nudge, major hint, or
solution-providing intervention. Preserve the decision in the
[attempt log](./attempt-log-template.md).

## Score interpretation

- `90-100`: strong independent performance.
- `80-89`: interview ready, with identifiable improvement areas.
- `70-79`: close, but not yet consistent.
- Below `70`: revisit weak topics before adding more problem volume.
