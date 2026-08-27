# 13. Clean Code and Refactoring

## Outcome

Improve a design while preserving behavior. This is an extension topic, best learned on working code.

## Readability follows the workflow

A reader should find the main use case before its details.

Good names express domain intent:

- allocate_spot, not process;
- active_hold, not data;
- SeatUnavailable, not OperationError.

Keep happy-path orchestration short. Move validation to the object that owns the rule.

## Smells and moves

| Smell | Likely move |
|---|---|
| Long conditional on policy | extract strategy |
| Repeated group of primitives | introduce value object |
| Service reads and writes entity fields | move behavior to entity |
| Method changes for unrelated reasons | split responsibilities |
| External types spread through domain | add adapter |
| Constructor has many dependencies | split workflow or facade |

A smell is evidence to investigate, not an automatic command.

## Refactor safely

1. Add a characterization test around current behavior.
2. Make one structural change.
3. Run focused tests.
4. Keep names and contracts aligned.
5. Remove dead compatibility code.

Do not combine a behavior change, pattern rewrite, and persistence migration in one step unless the scope demands it.

## Comments

Comment why a trade-off or constraint exists. Prefer code for what happens.

Useful:

    # Lock order is show, then seat, to avoid deadlock.

Not useful:

    # Increment count by one.

## Know when to stop

Interview code should be complete enough to prove the design, not production-framework complete. Stop abstracting when the critical flow is clear, extensions have an obvious seam, and tests can isolate dependencies.

## Common traps

- Refactoring without tests.
- Extracting helpers that hide domain language.
- Base classes created only to remove a few duplicated lines.
- Tiny methods that force readers to jump constantly.
- “Clean architecture” folders with no meaningful boundaries.

## Readiness check

You can identify the design pressure behind a smell and make the smallest safe change that addresses it.

Next: [Testing LLDs](./14-testing-low-level-designs.md).
