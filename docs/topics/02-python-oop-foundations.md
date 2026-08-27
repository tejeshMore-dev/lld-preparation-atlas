# 2. Python and OOP Foundations

## Outcome

Create objects with clear identity, state, behavior, and boundaries.

## Choose the right kind of object

| Kind | Use it for | Example |
|---|---|---|
| Value object | Meaning comes from its fields | Money, Position |
| Entity | Identity survives state changes | Ticket, Order |
| Service | Coordinates work across objects | BookingService |
| Policy | A rule that may vary | PricingPolicy |
| Repository | Access to stored entities | TicketRepository |

Prefer immutable value objects. Put validation at construction so invalid values do not travel through the system.

    from dataclasses import dataclass
    from decimal import Decimal

    @dataclass(frozen=True)
    class Money:
        amount: Decimal
        currency: str

        def __post_init__(self):
            if self.amount < 0:
                raise ValueError("amount cannot be negative")

## Encapsulation means protecting rules

Private fields alone are not encapsulation. An object is useful when callers ask it to perform behavior rather than rearrange its state.

Weak:

    ticket.status = "paid"

Stronger:

    ticket.mark_paid(receipt_id)

The second operation can validate the current state and preserve its invariant.

## Prefer composition

Inheritance is appropriate for a real, stable substitutability relationship. Most LLD variation is better expressed as a collaborator:

    class Checkout:
        def __init__(self, pricing_policy):
            self._pricing_policy = pricing_policy

This keeps pricing independent of checkout state and makes tests simple.

## Python choices that help

- Dataclasses for small data-rich objects.
- Enum for a closed set of states.
- Protocol or abstract base class at a real substitution boundary.
- Exceptions for exceptional failures; result types for expected business outcomes.
- Dependency injection through constructors.
- Type hints to communicate contracts, not to imitate Java.

## Common traps

- Getter-and-setter classes with no behavior.
- A “manager” object that owns every decision.
- Deep inheritance trees for vehicle, user, or product variants.
- Global singletons that hide dependencies.
- Abstract interfaces with only one stable implementation and no boundary value.

## Readiness check

You can explain whether a concept is an entity, value, policy, or service—and why—without referring to its class name.

Next: [Domain modeling](./03-domain-modeling-and-responsibility-assignment.md).
