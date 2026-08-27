# Rate Limiter

Design an in-process admission controller that limits requests per key.

## Scope

Support a configurable policy per user or API key and return an allow/deny decision with retry metadata. Distributed coordination and durable configuration are follow-ups.

## Contract

    decision = limiter.allow(key, cost=1)

A decision should include allowed, remaining capacity, and retry_after when denied.

## Algorithms

| Algorithm | Strength | Cost |
|---|---|---|
| Fixed window | simple and O(1) | bursts at boundaries |
| Sliding log | exact recent history | memory grows with traffic |
| Sliding counter | smoother approximation | more math and state |
| Token bucket | allows controlled bursts | clock/refill logic |
| Leaky bucket | smooth output rate | queue semantics |

Token bucket is a strong default: capacity controls burst size and refill rate controls sustained traffic.

## Model

| Type | Responsibility |
|---|---|
| RateLimitPolicy | capacity, refill/window, and cost rules |
| BucketState | tokens/count and last update |
| RateLimiter | atomic decision for a key |
| PolicyProvider | resolves policy by key or route |
| Clock | monotonic time |
| StateStore | reads and conditionally updates state |

## Token-bucket decision

1. Load the key’s state.
2. Refill based on elapsed monotonic time, capped at capacity.
3. If tokens cover cost, subtract and allow.
4. Otherwise deny and calculate time until enough tokens exist.
5. Save the state atomically.

Do not update last-refill time in a way that discards fractional refill progress.

## Correctness

The read-refill-check-subtract-write sequence is one atomic operation. Use a per-key lock in memory or a server-side atomic script/conditional update in a distributed store.

Bound state growth with idle-key eviction. Eviction must not accidentally grant more capacity than the chosen semantics allow.

## Follow-ups

- Route-specific and hierarchical limits.
- Distributed Redis-backed state.
- Weighted requests.
- Shadow mode and metrics.
- Fail-open versus fail-closed dependency policy.

## Interview finish

Implement token bucket with an injected clock and tests for burst capacity, partial refill, denial metadata, clock behavior, key isolation, and concurrent admission.
