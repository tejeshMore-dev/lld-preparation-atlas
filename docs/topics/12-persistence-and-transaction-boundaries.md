# 12. Persistence and Transaction Boundaries

## Outcome

Save domain changes without letting storage concerns control the model. This is an extension topic.

## Persist aggregates, not object graphs

A transaction should usually match one business consistency boundary. Load an aggregate, ask it to act, then save it.

    booking = bookings.get(booking_id)
    booking.confirm(payment_receipt)
    bookings.save(booking)

The repository translates between stored representation and domain objects.

## Define the atomic promise

Examples:

- creating a ticket and occupying a spot succeed together;
- reserving seats and creating a hold succeed together;
- recording payment and marking paid do not always live in one database.

When one transaction cannot cover every side effect, define ordering and recovery explicitly.

## External side effects

A database transaction cannot roll back an email or most payment calls.

Useful approaches:

- perform external work after commit when it is optional;
- store an outbox record in the same transaction, then publish later;
- use idempotency keys for retryable external operations;
- compensate when a completed side effect must be reversed.

## Optimistic versus pessimistic control

| Approach | Good fit |
|---|---|
| Optimistic version check | conflicts are rare and retries are cheap |
| Pessimistic row/resource lock | conflicts are common or overselling is costly |
| Unique constraint | database can express the invariant directly |

Constraints are a final guard, not a replacement for a clear domain error.

## Mapping

Keep database IDs and timestamps where they matter, but do not force every table relation into a bidirectional object relation. Fetch what the use case needs.

## Common traps

- One transaction around an entire request including network calls.
- Saving each child independently when the aggregate must stay consistent.
- Treating rollback as recovery for external side effects.
- Repository interfaces that expose ORM details.
- Retrying non-idempotent work after an unknown outcome.

## Readiness check

You can draw the transaction boundary and explain what happens if each external step fails before or after commit.

Next: [Clean code and refactoring](./13-clean-code-and-refactoring.md).
