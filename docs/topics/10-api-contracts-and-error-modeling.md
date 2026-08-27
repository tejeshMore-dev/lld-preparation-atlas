# 10. API Contracts and Error Modeling

## Outcome

Design operations whose success, failure, and retry behavior are clear. This extension matters when an LLD exposes a library or service boundary.

## Start with intent

Prefer task-shaped methods:

    hold_seats(show_id, seat_ids, customer_id)

over storage-shaped methods:

    update_seats(seat_ids, status)

The first contract can protect the workflow. The second asks callers to preserve internal rules.

## Commands and results

A command groups stable input. A result exposes only what the caller needs.

    @dataclass(frozen=True)
    class HoldSeats:
        show_id: str
        seat_ids: tuple[str, ...]
        customer_id: str

Do not return mutable domain internals merely for convenience.

## Error taxonomy

| Error | Meaning | Typical handling |
|---|---|---|
| Validation | input is malformed | fix request |
| Conflict | current state rejects the action | refresh or choose another |
| Not found | referenced identity is absent | correct identity |
| Dependency | external capability failed | retry or compensate |
| Internal | broken invariant or bug | alert and investigate |

Use specific errors at the boundary. Preserve the original cause when translating infrastructure failures.

## Idempotency

Retries are safe only when repeating an operation has the intended effect. For create or payment operations, accept an idempotency key and remember the first result.

Idempotency does not make concurrent execution harmless by itself; the key check and state change must share an atomic boundary.

## Compatibility

Make additive changes when possible:

- add optional input with a default;
- add result fields without changing existing meaning;
- avoid reusing an enum value for a new concept;
- version genuinely incompatible contracts.

## Common traps

- Boolean success flags with no failure meaning.
- Catching every exception and returning None.
- Exposing database errors to callers.
- Assuming retries are safe.
- Generic CRUD APIs around behavior-rich domains.

## Readiness check

For each operation, you can state its success result, expected failures, side effects, and retry semantics.

Next: [Concurrency](./11-concurrency-and-thread-safety.md).
