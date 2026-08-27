# 11. Concurrency and Thread Safety

## Outcome

Identify shared invariants and protect each check-and-change as one operation.

## Find the race

A race usually looks harmless:

    if seat.is_available():
        seat.reserve(customer)

Two threads can both pass the check. The invariant is not “reserve is locked”; it is “a seat has at most one active reservation.”

## Correctness, coordination, scarcity

| Concern | Question | Typical tool |
|---|---|---|
| Correctness | Which state must change atomically? | lock, transaction, compare-and-set |
| Coordination | Must work happen in order? | condition, queue, event |
| Scarcity | Which resource has a hard limit? | semaphore, pool, token bucket |

Name the concern before choosing the primitive.

## Choose a lock boundary

Protect the smallest state that owns the invariant, but keep the full check-and-update inside it.

    class Seat:
        def reserve(self, customer_id):
            with self._lock:
                if self._customer_id is not None:
                    raise SeatUnavailable
                self._customer_id = customer_id

A per-seat lock allows unrelated seats to proceed concurrently. A show-wide lock is simpler but reduces concurrency. State the trade-off.

## Keep critical sections boring

Inside a lock:

- validate shared state;
- make the smallest mutation;
- capture facts needed afterward;
- exit.

Avoid network calls, callbacks, file I/O, or acquiring locks in inconsistent order.

## Liveness

Correct data can still produce a broken program.

- **Deadlock:** operations wait on each other forever.
- **Starvation:** one operation never gets access.
- **Livelock:** operations react but make no progress.

Prefer one lock when the problem is small. If multiple locks are necessary, define a global acquisition order.

## Optimistic concurrency

For persisted aggregates, store a version and update only if it still matches. A conflict means reload and retry the use case if retry is safe.

## Testing

Use barriers or deterministic hooks to force competing calls to reach the vulnerable point. Repeating a flaky test a thousand times is weak evidence.

## Common traps

- Locking a method but not the invariant.
- One global lock without explaining the throughput cost.
- Holding a lock during external I/O.
- Publishing events before the protected state commits.
- Confusing thread-safe collections with a thread-safe workflow.

## Readiness check

For every shared rule, you can name its owner, atomic boundary, contention trade-off, and failure behavior.

Next: [Persistence and transactions](./12-persistence-and-transaction-boundaries.md).
