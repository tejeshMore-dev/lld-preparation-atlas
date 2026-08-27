# 3. Domain Modeling and Responsibility

## Outcome

Find the smallest object model that owns the important rules.

## Model from workflows

For each core use case:

1. Write the input and desired result.
2. List the state read or changed.
3. Name the rule that protects that change.
4. Assign the rule to the object with the needed information.

This is more reliable than extracting every noun from the prompt.

## Responsibility test

A responsibility belongs where the required state already lives.

| Rule | Likely owner |
|---|---|
| A seat cannot be held twice | Seat inventory or show |
| A game ends after four aligned pieces | Board or win policy |
| A locker accepts only fitting parcels | Locker |
| A coupon cannot exceed its limit | Coupon |
| A ticket moves through valid states | Ticket |

Use a domain service only when a rule genuinely spans multiple entities and no single entity is the natural owner.

## Make invariants executable

    class Seat:
        def hold(self, hold_id):
            if self._hold_id is not None:
                raise SeatUnavailable(self.id)
            self._hold_id = hold_id

The operation says what happened, checks the rule, and changes state together.

## Relationships

- **Composition:** the child belongs to the parent’s lifecycle.
- **Association:** objects know or use each other but live independently.
- **Dependency:** a short-lived collaborator is passed to an operation.
- **Inheritance:** one object must be substitutable for another.

Choose the weakest relationship that supports the workflow.

## Aggregates

When persistence or concurrency matters, group objects that must change atomically. The aggregate root is the only entry point for those changes.

Keep aggregates small. A cinema is not one giant transaction merely because it contains screens and shows.

## Walk one critical flow

Before coding, narrate:

    command -> load state -> validate -> mutate -> publish/save -> return

If responsibility jumps between unrelated classes or returns to a controller for business logic, revise the model.

## Common traps

- Classes named Manager, Helper, or Utils hiding unclear ownership.
- Anemic entities plus one enormous service.
- Bidirectional references everywhere.
- One aggregate for the entire system.
- Modeling tables instead of behavior.

## Readiness check

For every rule, you can point to exactly one owner and explain why it has the information needed to enforce it.

Next: [UML and interaction sketches](./04-uml-and-interaction-modeling.md).
