# Interview Workflow

| Time | Output |
|---:|---|
| 0–5 min | use cases, invariants, assumptions, exclusions |
| 5–12 min | core objects and responsibility owners |
| 12–17 min | one critical sequence and contracts |
| 17–35 min | runnable vertical slice |
| 35–42 min | success, rejection, and state-after-failure tests |
| 42–45 min | trade-offs and one follow-up |

## Checklist

1. Restate the problem and choose a version-one scope.
2. Name the rules that must never break.
3. Assign each mutable fact to one owner.
4. Trace a command from caller to result.
5. Implement through behavior, not public field mutation.
6. Make external dependencies explicit.
7. Protect any shared check-and-change.
8. Test the main success and highest-risk failure.
9. Explain one simpler alternative and one extension seam.

Narrate decisions and causes, not every keystroke. When details are missing, state the smallest reasonable assumption and continue.
