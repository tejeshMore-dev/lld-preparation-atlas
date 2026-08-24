# LLD Practice Attempt Log Template

Copy this file for every independent full practice or timed mock. Complete the
setup before starting, preserve artifacts when time ends, and score before
repairing the solution.

Related guidance:

- [Topic 15 - Interview Execution, Problem Practice, and Readiness](../topics/15-interview-execution-problem-practice-and-readiness.md)
- [Interview workflow](./interview-workflow.md)
- [Mock-interview rubric](./mock-interview-rubric.md)
- [Final readiness checklist](./readiness-checklist.md)

## 1. Attempt identity

| Field | Value |
|---|---|
| Date | |
| Problem | |
| Capability family | |
| Format | discussion / sketch / machine coding / hybrid |
| Time limit | |
| Unseen? | yes / no; explain prior exposure |
| Interviewer/reviewer | |
| Environment/tools allowed | |
| Target role/round | |

## 2. Interview contract

- Expected output:
- Must-have depth:
- Language/runtime:
- Execution/testing expected:
- Persistence expectation:
- Concurrency expectation:
- Planned follow-up:
- Hint policy:

## 3. Bounded design brief

### Objective


### Must-have use cases

1.
2.
3.

### Business rules and invariants

1.
2.
3.

### Assumptions

-

### Out of scope

-

### Highest-risk failure


## 4. Model and execution artifacts

- Domain vocabulary:
- Invariant owners:
- Relationships/cardinality:
- Lifecycle/transition table:
- Public contracts/errors:
- Critical success sequence:
- Critical failure sequence:
- Selected vertical slice:
- Deferred concerns:
- Test plan:

Link or paste the diagram, code, and test output here:


## 5. Timeline

| Event | Minute | Evidence/note |
|---|---:|---|
| Clarification ended | | |
| Model stabilized | | |
| Coding began | | |
| First execution | | |
| First test passed | | |
| Follow-up introduced | | |
| Final summary began | | |
| Attempt ended | | |

## 6. Follow-up impact

- Changed assumption/rule:
- Affected owner:
- Contract change:
- Workflow/effect-order change:
- Persistence/concurrency implication:
- Regression/new tests:
- New trade-off/limitation:
- Completed within time?:

## 7. Guidance log

Classify each intervention as clarification, minor nudge, major hint, or solution
intervention.

| Minute | Intervention | Classification | Effect on solution |
|---:|---|---|---|
| | | | |

## 8. Rubric

Every score needs observable evidence.

| Category | Maximum | Score | Evidence |
|---|---:|---:|---|
| Requirements, assumptions, and scope | 10 | | |
| Domain modeling and responsibility ownership | 15 | | |
| Relationships, state, and interaction flow | 10 | | |
| Interfaces and dependency boundaries | 10 | | |
| Invariants, validation, and failure behavior | 10 | | |
| Extensibility without overengineering | 10 | | |
| Code quality and language correctness | 15 | | |
| Tests and testability | 10 | | |
| Trade-offs and requirement adaptation | 5 | | |
| Communication and time management | 5 | | |
| **Total** | **100** | | |

## 9. Critical-failure gate

- [ ] A must-have use case could not be satisfied.
- [ ] A major invariant could be bypassed.
- [ ] The design could not be implemented coherently in the chosen language.
- [ ] A serious data-loss, double-booking, or double-payment path remained.
- [ ] A small requirement change could not be handled independently.
- [ ] Major or solution-providing guidance removed independence.

If any item is checked, the attempt does not pass regardless of numeric score.

## 10. Debrief

- Completed artifacts:
- Missing/unfinished artifacts:
- Tests executed and results:
- Strongest behavior to retain:
- First bottleneck or defect:
- Root skill/category:
- Downstream symptoms:
- Time/scope decision to change:
- Honest current limitation:

## 11. Repair loop

- Highest-leverage focused drill:
- Immediate segment retry result:
- Spaced verification date:
- Spaced/unseen verification result:
- Weakness closed? Evidence:

## 12. Assessment decision

- [ ] Prompt was genuinely unseen.
- [ ] Score is at least 80/100.
- [ ] No critical failure occurred.
- [ ] No major hint or solution intervention occurred.
- [ ] Core work completed within the agreed 45-60 minute range.
- [ ] Evidence bundle is preserved.

**Independent pass:** yes / no

**Current trailing independent-pass streak:**

Do not edit the original attempt score after repairing the solution. Record the
repair and verification separately.
