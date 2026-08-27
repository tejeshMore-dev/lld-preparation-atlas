# 8. Behavioral Patterns

## Outcome

Make changing policies, workflows, and state transitions explicit.

## The high-value set

| Need | Pattern |
|---|---|
| Swap an algorithm or business rule | Strategy |
| Notify independent listeners | Observer |
| Encapsulate a request for queueing or undo | Command |
| Behavior changes with lifecycle | State |
| Fixed workflow with replaceable steps | Template method |
| Traverse without exposing representation | Iterator |
| Centralize a complex conversation | Mediator |

Strategy and State are the most common in interview designs.

## Strategy

A strategy represents a replaceable policy.

    class NearestSpotPolicy:
        def choose(self, spots, vehicle):
            return min(
                (spot for spot in spots if spot.fits(vehicle)),
                key=lambda spot: spot.distance,
            )

The parking service depends on choose(), not on a chain of vehicle-type conditions.

## State

Use a state object when lifecycle branching is large and each state supports different operations. For a small lifecycle, an enum plus guarded methods is clearer.

    def cancel(self):
        if self.status not in {PENDING, CONFIRMED}:
            raise InvalidTransition
        self.status = CANCELLED

## Observer

Publish domain events after a successful state change. Listeners handle secondary work such as notifications or analytics.

Do not use an event to hide a required synchronous step. If booking is not complete without reserving inventory, that work belongs in the main transaction.

## Command

A command is valuable when requests must be queued, retried, logged, authorized, or undone. A plain service method is enough for synchronous one-off calls.

## Common traps

- Strategy classes for two lines that never vary.
- Observer chains with invisible execution order.
- State classes that contain only a status name.
- Commands with no queueing, history, or execution boundary.
- Pattern combinations that obscure the primary workflow.

## Readiness check

You can replace a policy, add a listener, or extend a lifecycle without changing unrelated domain objects.

Next: [Application patterns](./09-application-patterns-and-reusable-building-blocks.md).
