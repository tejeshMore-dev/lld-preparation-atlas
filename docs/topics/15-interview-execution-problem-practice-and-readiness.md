# 15. Interview Execution

## Outcome

Deliver a clear, runnable design under time pressure and adapt it to a follow-up.

## A 45-minute shape

| Time | Focus |
|---:|---|
| 0–5 min | clarify use cases, invariants, and scope |
| 5–12 min | identify objects and assign responsibilities |
| 12–17 min | walk the critical sequence |
| 17–35 min | implement one vertical slice |
| 35–42 min | test success and failure |
| 42–45 min | discuss trade-offs and follow-up |

Adjust the split, but do not spend half the interview drawing every class.

## Narrate decisions

Good communication is brief and causal:

- “Spot owns occupancy because it has the state needed to prevent double assignment.”
- “Pricing is injected because rates are a stated variation.”
- “The availability check and reservation share one lock.”
- “I am deferring persistence because it does not change this domain contract.”

Name the simpler alternative when adding an abstraction.

## Implementation order

1. Values and enums used by the workflow.
2. The entity that owns the main invariant.
3. One policy or boundary interface, if required.
4. The application service.
5. A happy-path test and a rejection test.

Keep the code runnable. A small complete flow is stronger than twenty unfinished class shells.

## Handle follow-ups

Before editing:

1. restate the new requirement;
2. identify which assumption changed;
3. point to the seam that should absorb it;
4. make the smallest coherent change;
5. rerun or update the affected test.

If the change cuts across everything, say which earlier design choice caused it.

## Self-review

Ask:

- Did I solve the agreed problem?
- Does each invariant have one owner?
- Is the primary workflow easy to trace?
- Are dependencies explicit?
- Is concurrency handled where state is shared?
- Did I prove failure leaves valid state?
- Can I explain every abstraction?

## Practice loop

Choose a prompt from the [problem catalogue](../practice/problem-catalog.md). Use the [interview workflow](../practice/interview-workflow.md), score it with the [mock rubric](../practice/mock-interview-rubric.md), and record one improvement in the [attempt log](../practice/attempt-log-template.md).

Do not reread the same solution immediately. Reattempt it from a blank file after several days.

## Readiness check

Complete three unseen 45–60 minute problems in a row with clear scope, a coherent model, runnable core behavior, focused tests, and no major rescue hints.

Then keep practicing weak areas, not the entire syllabus.
