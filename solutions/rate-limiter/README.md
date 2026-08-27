# Rate Limiter Low-Level Design

Decide whether a key may spend request capacity now, using deterministic time and an atomic per-key algorithm.

## Understanding the Problem

Decide whether a key may spend request capacity now, using deterministic time and an atomic per-key algorithm.

The design starts with the business invariant and the critical workflow. Named patterns come later, only where a requirement creates a real variation or boundary.

## Requirements

### Clarifying Questions

- What forms the key?
- Which algorithm and burst behavior are required?
- Do requests have weights?
- Is state local or distributed?
- Should store failure fail open or closed?

### Final Requirements

1. Resolve a validated rate policy per key/context.
2. Implement token-bucket admission.
3. Return allowed, remaining, and retry-after.
4. Make refill/check/consume atomic.
5. Evict safely idle state and inject monotonic time.

The detailed reference below records additional assumptions, exclusions, validation rules, and edge cases.

## Core Entities and Relationships

| Entity | Responsibility |
|---|---|
| RateLimitPolicy | Capacity and refill configuration. |
| BucketState | Tokens, time, version, and last access. |
| RateLimitDecision | Immutable admission result. |
| RateLimiter | Coordinates one decision. |
| PolicyProvider | Resolves key/route policy. |
| StateStore | Owns atomic state transition. |
| Clock | Provides monotonic time. |

The object that owns mutable state also owns the invariant protecting that state. Coordinating services load collaborators and sequence the use case; they do not bypass entity behavior.

## Class Design

### Good Solution

Keep algorithm state per key and inject a fakeable monotonic clock.

### Great Solution

Put the full transition inside StateStore atomicity, preserve fractional refill, define idle eviction, policy migration, failure mode, and distributed clock authority.

### Final Class Design

The critical collaboration is: validate -> resolve policy -> atomic load/create -> refill -> consume or deny -> persist -> return metadata.

The full class map, state transitions, method contracts, and design rationale are preserved in the detailed reference below.

## Implementation

Implement one vertical slice before filling every class:

    validate -> resolve policy -> atomic load/create -> refill -> consume or deny -> persist -> return metadata

### Complete Code Implementation

This repository currently treats this problem as a Markdown design exercise. The contracts, algorithms, atomic boundaries, pseudocode, and complete verification plan are in the detailed reference below. Implement the entity that owns the main invariant first, then the coordinating service.

## Verification

Verify the happy path, the highest-risk rejection, and state after failure. Then force two competing operations at the atomic boundary and assert the invariant, not thread timing.

The detailed reference lists problem-specific test cases and complexity.

## Extensibility

- Distributed atomic store
- Hierarchical and weighted limits
- Dynamic policy, shadow mode, and metrics

Each extension should enter through a named policy, boundary, or lifecycle change rather than a new conditional inside the main workflow.

## What Is Expected at Each Level?

### Junior

Deliver the agreed core workflow with coherent entities, valid state changes, and straightforward failure handling.

### Mid-level

Make invariants explicit, isolate real variations, cover failure paths with tests, and discuss the relevant concurrency boundary.

### Senior

Explain exact versus approximate global limits, hierarchical atomicity, clock skew, cleanup races, overshoot, and fail-open/closed trade-offs.

## Interview Walkthrough

1. Clarify the version-one scope and exclusions.
2. State the invariants before drawing classes.
3. Introduce the core entities and walk: validate -> resolve policy -> atomic load/create -> refill -> consume or deny -> persist -> return metadata.
4. Compare the good and great solution based on the stated requirements.
5. Implement a complete vertical slice and one failure test.
6. Handle a realistic follow-up through an explicit extension seam.

## Detailed Design Reference

<details>
<summary>Open the implementation-specific deep dive</summary>
Design an admission controller that limits requests per key and returns useful retry metadata under concurrent load.

## 1. Understanding the problem

A rate limiter answers:

    may this key spend this request cost now?

Its correctness depends on time and atomic state updates. The design must define:

- what is limited;
- over which interval or refill rule;
- whether bursts are allowed;
- where state lives;
- what happens when the state store fails.

This guide focuses on an in-process limiter and shows the distributed extension boundary.

## 2. Clarifying questions

- Is the key a user, API token, IP, route, tenant, or combination?
- Is the rule fixed-window, sliding-window, token-bucket, or leaky-bucket?
- Are bursts allowed?
- Do requests have different costs?
- Are rules global or route-specific?
- Is the limiter local or shared across instances?
- What metadata must denial return?
- Is time measured with a monotonic clock?
- How long is idle-key state retained?
- Should dependency failure fail open or fail closed?
- Are configuration changes immediate?

## 3. Final requirements

Version one supports:

1. A limiter decision per string key.
2. Token-bucket behavior.
3. Capacity and tokens-per-second refill rate.
4. Optional request cost.
5. Allow/deny decision.
6. Remaining capacity and retry-after metadata.
7. Monotonic injected Clock.
8. Per-key state isolation.
9. Atomic concurrent admission.
10. Idle-key cleanup.
11. A PolicyProvider seam for per-route/key configuration.

Distributed storage and global quotas are follow-ups.

## 4. Token bucket model

A bucket has:

- capacity C;
- current tokens T, where 0 <= T <= C;
- refill rate R tokens/second;
- last_refill_time.

At time now:

    elapsed = max(0, now - last_refill_time)
    refilled = min(C, T + elapsed * R)

If refilled >= cost:

    allow
    remaining = refilled - cost

Otherwise:

    deny
    missing = cost - refilled
    retry_after = missing / R

Fractional tokens preserve partial refill progress. Capacity controls maximum burst; refill rate controls sustained throughput.

## 5. Invariants

1. Token count stays between zero and capacity.
2. One accepted request subtracts its exact cost once.
3. A denied request does not subtract cost.
4. Refill never exceeds capacity.
5. The read-refill-check-subtract-write sequence is atomic per key.
6. Different keys do not share bucket state unless a hierarchy explicitly requires it.
7. Negative elapsed time never creates or removes tokens.
8. Invalid cost or policy is rejected before state mutation.
9. Decision metadata corresponds to the committed bucket state.
10. Cleanup does not grant more capacity than the selected idle-reset semantics.

## 6. Core model

| Type | Important state | Responsibility |
|---|---|---|
| RateLimitPolicy | capacity, refill rate | validated immutable rule |
| BucketState | tokens, last refill, last access, version | mutable per-key state |
| RateLimitDecision | allowed, remaining, retry_after, limit | immutable result |
| RateLimiter | store, policy provider, clock | coordinates one admission |
| PolicyProvider | configuration | resolves policy by key/context |
| StateStore | bucket records | atomic state access/update |
| Clock | monotonic now | deterministic elapsed time |
| CleanupPolicy | idle duration | state-retention decision |

Relationships:

    RateLimiter --> PolicyProvider
    RateLimiter --> StateStore
    RateLimiter --> Clock
    StateStore o-- BucketState
    RateLimiter --> RateLimitDecision

## 7. Public contract

A useful API:

    allow(key, cost=1, context=None) -> RateLimitDecision

Decision fields:

- allowed;
- limit/capacity;
- remaining, rounded according to contract;
- retry_after when denied;
- reset/fully-refilled time when useful;
- policy identifier/version for diagnostics.

Returning a decision is more useful than a Boolean and keeps HTTP-specific headers outside the core component.

## 8. Policy design

RateLimitPolicy validates:

- capacity > 0;
- refill_rate > 0;
- allowed cost semantics;
- optional maximum cost.

PolicyProvider can resolve by route, tenant tier, or key.

A policy change must define bucket migration:

- clamp existing tokens to new capacity;
- reset to full;
- scale proportionally;
- keep old policy until bucket expiry.

Version one can clamp and record policy_version in BucketState.

## 9. State-store design

InMemoryStateStore may use:

    dict[key, BucketState]
    dict[key, Lock] or lock striping

State creation must also be atomic so two first requests do not create independent full buckets.

A store contract should expose one atomic operation or callback rather than separate get() and set() that callers can race:

    update(key, initial_factory, transition) -> decision

For a remote store, the transition belongs in a server-side script or compare-and-set loop.

## 10. Admission workflow

    Client -> RateLimiter: allow(key, cost)
    RateLimiter -> PolicyProvider: policy_for(key, context)
    RateLimiter -> StateStore: atomic update(key)
    StateStore -> BucketState: refill(now)
    StateStore -> BucketState: consume if sufficient
    StateStore -> RateLimiter: committed decision
    RateLimiter -> Client: RateLimitDecision

Step by step:

1. Validate key and positive cost.
2. Resolve a validated policy.
3. Read monotonic now once.
4. Enter the keyâ€™s atomic state transition.
5. Create a full bucket if absent.
6. Refill using elapsed time.
7. Consume or calculate retry_after.
8. Update last-refill/access fields without losing fractional progress.
9. Persist the state.
10. Return metadata derived from that state.

## 11. Time correctness

Use a monotonic clock for elapsed duration. Wall time can jump because of synchronization or manual changes.

Clock is injected:

    clock.now() -> monotonic seconds

Tests advance a FakeClock without sleeping.

When a distributed store performs the transition, choose one authoritative time source. Client clocks with skew can produce unfair refill.

## 12. Fractional refill detail

Suppose capacity=10, rate=1.5 tokens/second, current tokens=0, and 1 second passes. The bucket has 1.5 tokens.

If a cost-1 request is allowed, 0.5 token remains. Do not round down and discard it.

last_refill_time can be set to now when the fractional token count itself preserves progress. With integer-only tokens, retain leftover elapsed/refill credit explicitly.

## 13. Alternative algorithms

| Algorithm | Strength | Weakness |
|---|---|---|
| Fixed window | O(1), very simple | double burst at boundary |
| Sliding log | exact recent history | O(requests) memory |
| Sliding counter | smooth approximation | weighted-window complexity |
| Token bucket | controlled burst plus sustained rate | refill/time math |
| Leaky bucket | smooth output/queue | different admission semantics |

Choose from product semantics, not pattern preference.

## 14. Fixed-window sketch

State:

    window_start
    count

Atomic transition resets when now crosses the window, then increments if count + cost <= limit.

It is useful when boundary bursts are acceptable and operational simplicity matters.

## 15. Sliding-log sketch

Store accepted timestamps per key. Remove timestamps older than the interval, then admit if remaining count plus cost is within the limit.

It is exact but memory and cleanup cost grow with traffic.

## 16. Error and failure policy

| Failure | Result |
|---|---|
| empty key | validation error |
| cost <= 0 | validation error |
| cost > capacity | deny or validation error by contract |
| policy missing | default policy or configuration error |
| clock moves backward | clamp elapsed to zero and alert |
| state-store timeout | fail-open or fail-closed policy |
| corrupted state | reject/reset according to risk policy |
| cleanup racing request | conditional removal/recreation |

Security-sensitive endpoints often fail closed; availability-sensitive endpoints may fail open with metrics. Make it configurable and observable.

## 17. Concurrency

Per-key atomicity is sufficient for independent limits.

In memory:

- one global lock is easiest but contended;
- a lock per key gives isolation but requires lock cleanup;
- striped locks bound lock memory with some false contention.

Distributed:

- Redis/Lua-style atomic script;
- database compare-and-set with version;
- strongly consistent quota service;
- local approximate shards with periodic reconciliation when small overshoot is acceptable.

Read followed by write in separate remote calls is incorrect.

## 18. Hierarchical limits

A request may need to satisfy:

- user limit;
- tenant limit;
- route limit;
- global emergency limit.

All relevant buckets must be consumed consistently. Options:

- one atomic multi-key script;
- fixed lock ordering in memory;
- reserve/rollback with careful compensation;
- evaluate strict global limit in a separate service.

Do not subtract the first bucket and then simply fail on the second without rollback semantics.

## 19. Idle-key eviction

Unbounded keys cause memory growth.

Record last_access and remove keys idle long enough to refill fully:

    safe_idle >= capacity / refill_rate

After that duration, recreating a full bucket is equivalent to leaving it stored.

Cleanup can be periodic, sampled during requests, or delegated to store TTL. Ensure a cleanup operation cannot delete a bucket that was just updated; use versions or atomic TTL refresh.

## 20. Observability

Record:

- allowed and denied counts;
- store failures;
- retry-after distribution;
- active key count;
- cleanup count;
- decision latency;
- fail-open/fail-closed occurrences;
- policy version.

Avoid using raw user keys as high-cardinality metric labels. Hash or aggregate carefully.

## 21. Complexity

Per request:

- token bucket arithmetic: O(1);
- state lookup/update: O(1) average in memory;
- memory: O(active keys);
- cleanup: O(active keys) for a full sweep, amortizable.

Sliding log differs: O(events in window) space per active key.

## 22. Verification

Using FakeClock, test:

- initial burst up to capacity;
- next request denied;
- partial refill;
- full refill capped at capacity;
- weighted request cost;
- retry_after calculation;
- independent keys;
- invalid policy and cost;
- fractional token preservation;
- backward clock behavior;
- idle eviction equivalence;
- policy capacity reduction;
- concurrent requests allow exactly available capacity;
- first-request state creation race;
- store failure under both failure policies;
- hierarchical rollback/atomic behavior if supported.

## 23. Patterns and principles

| Technique | Purpose |
|---|---|
| Strategy | algorithm variants |
| Value object | policy and decision |
| Repository/state store | local or remote bucket state |
| Dependency injection | clock, policy provider, store |
| Atomic transition | correctness boundary |
| Decorator | metrics or fallback around limiter |
| Factory | selecting an algorithm from configuration |

Do not hide the algorithm behind abstractions before its semantics are specified.

## 24. Extensibility

- **Distributed state:** atomic remote script and authoritative time.
- **Route policies:** PolicyProvider uses request context.
- **Weighted operations:** cost parameter already isolates it.
- **Dynamic configuration:** versioned policies and migration rule.
- **Shadow mode:** calculate and record decisions without denying.
- **Quotas:** add a non-refilling balance with reset semantics.
- **Adaptive limits:** separate controller updates policy; limiter remains deterministic.
- **Client headers:** adapter translates RateLimitDecision into protocol fields.

## 25. Trade-offs

- Token bucket permits bursts intentionally.
- Exact global limiting costs coordination and latency.
- Per-key locks improve concurrency but create lifecycle complexity.
- Local limiters are fast but allow aggregate overshoot across instances.
- Fail-open protects availability; fail-closed protects the guarded resource.
- Floating arithmetic is convenient; fixed-point/integer units may improve reproducibility.

## 26. Interview expectations

### Junior

Implement one algorithm, per-key state, basic allow/deny, and deterministic tests.

### Mid-level

Add atomic concurrency, decision metadata, injected time, state cleanup, and algorithm trade-offs.

### Senior

Discuss distributed atomicity, clock authority, hierarchical limits, policy migration, fail-open/closed semantics, overshoot bounds, and observability.

## 27. Interview walkthrough

1. Clarify key, capacity, refill rate, burst, and local/distributed scope.
2. Write token-bucket equations and invariants.
3. Define Policy, BucketState, Decision, Clock, and StateStore.
4. Put the full decision inside one per-key atomic transition.
5. Test burst, refill, denial, and concurrent capacity.
6. Add cleanup and failure policy.
7. Explain distributed storage as a replacement for StateStore, not a rewrite of the algorithm.

</details>
