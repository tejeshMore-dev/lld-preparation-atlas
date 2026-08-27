# Mock Rubric

Score observable evidence, not familiarity with the prompt. A strong pass is 80/100 with no critical failure or major hint.

| Category | Points |
|---|---:|
| Scope, assumptions, and requirements | 10 |
| Domain model and responsibility ownership | 20 |
| Workflow, state, and contracts | 15 |
| Invariants, failures, and concurrency | 15 |
| Code quality and completeness | 15 |
| Tests and testability | 10 |
| Trade-offs and follow-up adaptation | 10 |
| Communication and time | 5 |
| **Total** | **100** |

## Critical failure

Do not pass an attempt that:

- misses a must-have use case;
- permits double booking, double payment, data loss, or an equivalent broken invariant;
- cannot produce a coherent critical flow;
- depends on extensive interviewer rescue;
- collapses under a small follow-up.

## Interpretation

- 90–100: strong and independent.
- 80–89: ready, with a specific improvement.
- 70–79: close but inconsistent.
- Below 70: repair weak skills before adding volume.

Record the score and evidence in the [attempt log](./attempt-log-template.md).
