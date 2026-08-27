# 9. Application Patterns

## Outcome

Keep use-case orchestration, domain rules, and infrastructure separate. This is an extension topic for larger LLD exercises.

## A small layered shape

    caller -> application service -> domain model
                    |
                    -> repository / gateway

- **Application service:** coordinates one use case.
- **Domain object:** owns business state and invariants.
- **Repository:** loads and saves aggregates.
- **Gateway:** talks to an external capability.
- **Mapper:** translates between representations.

Dependencies point toward the domain.

## Application service

A service should read like a workflow:

    def reserve(self, command):
        show = self._shows.get(command.show_id)
        hold = show.hold(command.seat_ids, self._clock.now())
        self._shows.save(show)
        self._events.publish(hold.created_event())
        return hold.id

Validation that depends only on Show belongs inside Show. Loading, saving, and publication remain orchestration.

## Repository

Model repositories as collection-like domain ports:

- get(id)
- add(entity)
- save(entity)
- remove(entity)

Avoid a separate repository method for every query unless the use case needs it. Do not leak ORM rows or query builders into domain code.

## Policies and specifications

Use a policy for a calculation or decision that varies. Use a specification when a business predicate must be combined, named, or reused. A direct method is simpler for one local rule.

## Domain events

An event states a completed fact: BookingConfirmed, ParcelDeposited. It can decouple optional reactions, but it does not replace transaction design.

## Common traps

- Layers that only forward calls.
- A repository per table rather than per aggregate.
- Domain objects importing database or HTTP clients.
- Events used for required atomic work.
- “Reusable” base services with unrelated type parameters.

## Readiness check

You can trace one use case and clearly label orchestration, domain decisions, and external boundaries.

Next: [API contracts and errors](./10-api-contracts-and-error-modeling.md).
