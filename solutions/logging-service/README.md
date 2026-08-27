# Logging Service Low-Level Design

Build an in-process logging pipeline that filters immutable events, formats them, and fans out to several destinations safely.

## Understanding the Problem

Build an in-process logging pipeline that filters immutable events, formats them, and fans out to several destinations safely.

The design starts with the business invariant and the critical workflow. Named patterns come later, only where a requirement creates a real variation or boundary.

## Requirements

### Clarifying Questions

- Is this a library or distributed ingestion system?
- Do handlers have independent levels and formats?
- Is delivery synchronous or asynchronous?
- What happens when a queue or destination fails?
- How are context and secrets handled?

### Final Requirements

1. Support named loggers and ordered levels.
2. Create immutable structured LogEvents.
3. Fan out through handler-specific filters and formatters.
4. Write to console/memory and allow other appenders.
5. Define bounded async, flush, close, and failure behavior.

The detailed reference below records additional assumptions, exclusions, validation rules, and edge cases.

## Core Entities and Relationships

| Entity | Responsibility |
|---|---|
| LogEvent | Immutable time, level, message, context, and error. |
| Logger | Creates and dispatches one event. |
| Handler | Combines threshold, filters, formatter, and appender. |
| Formatter | Converts an event to text or bytes. |
| Appender | Owns destination I/O and lifecycle. |
| LogManager | Provides named logger configuration. |
| ContextProvider | Supplies request-local fields. |

The object that owns mutable state also owns the invariant protecting that state. Coordinating services load collaborators and sequence the use case; they do not bypass entity behavior.

## Class Design

### Good Solution

Separate Formatter from Appender and use Handler for per-destination configuration.

### Great Solution

Use immutable configuration snapshots, bounded async queues with explicit overflow, flush/close barriers, failure isolation, and safe context/redaction.

### Final Class Design

The critical collaboration is: level check -> create immutable event once -> handler filter -> format -> append/fan-out -> report internal failures through safe fallback.

The full class map, state transitions, method contracts, and design rationale are preserved in the detailed reference below.

## Implementation

Implement one vertical slice before filling every class:

    level check -> create immutable event once -> handler filter -> format -> append/fan-out -> report internal failures through safe fallback

### Complete Code Implementation

This repository currently treats this problem as a Markdown design exercise. The contracts, algorithms, atomic boundaries, pseudocode, and complete verification plan are in the detailed reference below. Implement the entity that owns the main invariant first, then the coordinating service.

## Verification

Verify the happy path, the highest-risk rejection, and state after failure. Then force two competing operations at the atomic boundary and assert the invariant, not thread timing.

The detailed reference lists problem-specific test cases and complexity.

## Extensibility

- File rotation and remote batching
- Dynamic configuration and sampling
- Correlation context, redaction, and metrics

Each extension should enter through a named policy, boundary, or lifecycle change rather than a new conditional inside the main workflow.

## What Is Expected at Each Level?

### Junior

Deliver the agreed core workflow with coherent entities, valid state changes, and straightforward failure handling.

### Mid-level

Make invariants explicit, isolate real variations, cover failure paths with tests, and discuss the relevant concurrency boundary.

### Senior

Explain backpressure, event loss semantics, recursive failure prevention, concurrency, lifecycle guarantees, and why audit logging needs a stronger contract.

## Interview Walkthrough

1. Clarify the version-one scope and exclusions.
2. State the invariants before drawing classes.
3. Introduce the core entities and walk: level check -> create immutable event once -> handler filter -> format -> append/fan-out -> report internal failures through safe fallback.
4. Compare the good and great solution based on the stated requirements.
5. Implement a complete vertical slice and one failure test.
6. Handle a realistic follow-up through an explicit extension seam.

## Detailed Design Reference

<details>
<summary>Open the implementation-specific deep dive</summary>
Design an in-process logging framework with levels, structured events, formatting, filtering, multiple destinations, and safe asynchronous delivery.

## 1. Understanding the problem

A logger is a reusable component, not a centralized log-storage platform.

Its core job is:

    call -> event -> filter -> format -> append

The design should allow console, file, memory, or remote outputs without coupling caller code to destination details.

The hard parts are configuration, fan-out, thread safety, queue overflow, failure isolation, and preventing the logger from recursively logging its own failures.

## 2. Clarifying questions

- Is this an in-process library or a distributed ingestion service?
- Which levels exist?
- Are log events structured?
- Can each destination use a different threshold and format?
- Do named loggers inherit parent configuration?
- Is delivery synchronous or asynchronous?
- What happens when a destination fails?
- What happens when an async queue is full?
- Must flush guarantee durability?
- Is file rotation required?
- How is request context attached?
- Must secrets be redacted?

## 3. Final requirements

Version one supports:

1. TRACE, DEBUG, INFO, WARN, ERROR, and FATAL levels.
2. Named loggers.
3. Immutable LogEvent values.
4. Message plus structured context.
5. Logger and handler thresholds.
6. Several handlers per logger.
7. Replaceable formatters.
8. Console and in-memory appenders.
9. Thread-safe writes.
10. Optional bounded asynchronous appender.
11. Flush and close lifecycle.
12. Explicit appender-failure policy.

Distributed collection, indexing, search, and alerting remain external.

## 4. Invariants

1. One logging call creates at most one LogEvent timestamp and identity.
2. Every handler receives the same immutable event.
3. A rejected level performs no formatting or I/O.
4. Appender writes are serialized when the destination requires it.
5. An accepted async event is either delivered or accounted for by the overflow/failure policy.
6. close() rejects new events and handles queued events according to its contract.
7. Logging an internal failure cannot recurse indefinitely.
8. Context supplied by one request does not leak into another.
9. Secret fields are redacted before they reach an unsafe destination.

## 5. Pipeline model

| Type | Important state | Responsibility |
|---|---|---|
| LogLevel | severity ordering | threshold comparison |
| LogEvent | time, level, message, logger, context, error | immutable logging fact |
| Logger | name, threshold, handlers | creates and dispatches events |
| Handler | threshold, filters, formatter, appender | per-destination pipeline |
| LogFilter | configuration | accepts/rejects an event |
| Formatter | configuration | converts event to text/bytes |
| Appender | destination resources | writes formatted output |
| LogManager | logger/configuration registry | creates and updates named loggers |
| ContextProvider | request-local data | correlation and structured fields |

Relationships:

    LogManager o-- Logger
    Logger o-- Handler
    Handler --> LogFilter
    Handler --> Formatter
    Handler --> Appender
    Logger --> ContextProvider

## 6. LogEvent design

LogEvent should be immutable and contain:

- timestamp;
- monotonic/sequence data if ordering matters;
- level;
- logger name;
- message template or rendered message;
- structured context map;
- exception metadata;
- thread/process identity when useful.

Copy or freeze context at event creation. A caller mutating a dictionary after log() must not change queued events.

Avoid storing raw exception objects in long-lived queues if they retain large object graphs; capture stable exception details.

## 7. Level filtering

Levels have a total order.

    event.level >= configured_threshold

Filter early at Logger to avoid event construction when possible. Handler thresholds still matter because console may accept INFO while a file accepts DEBUG.

If message construction is expensive, accept a lazy message supplier or parameterized template rather than requiring callers to precompute the string.

## 8. Logger design

Useful public API:

    trace(message, **context)
    debug(message, **context)
    info(message, **context)
    warn(message, **context)
    error(message, error=None, **context)
    log(level, message, **context)
    is_enabled(level) -> bool

Logger:

1. checks its effective threshold;
2. merges explicit and request context;
3. creates one immutable event using Clock;
4. offers the event to every handler;
5. applies the configured failure policy.

It does not format or write destinations itself.

## 9. Handler design

Handler combines per-destination behavior:

    if level accepted
       and all filters accept:
        output = formatter.format(event)
        appender.append(output)

Different handlers can use:

- human-readable console text;
- JSON file output;
- ERROR-only remote delivery;
- a filter that samples noisy events.

Handler composition avoids a subclass for every level/format/destination combination.

## 10. Formatter design

Formatter is a strategy:

    format(event) -> str | bytes

Examples:

- TextFormatter with timestamp, level, logger, message, context;
- JsonFormatter with stable keys;
- PatternFormatter with validated tokens.

Formatting failures should not break domain workflows silently. Route them to a fallback error sink and follow the configured logger failure policy.

Structured logs should preserve context fields rather than embedding everything into one message.

## 11. Appender design

Appender contract:

    append(formatted_event)
    flush()
    close()

Implementations:

- ConsoleAppender: serialized stream writes;
- MemoryAppender: deterministic tests;
- FileAppender: file lifecycle and optional rotation;
- RemoteAppender: batching, retry, and timeout;
- AsyncAppender: decorates another appender with a queue and worker.

Appender owns destination resources; Formatter owns representation.

## 12. Logging workflow

    Caller -> Logger: info(message, context)
    Logger -> Logger: level check and event creation
    Logger -> Handler*: handle(event)
    Handler -> Filter*: accept(event)
    Handler -> Formatter: format(event)
    Handler -> Appender: append(output)

A failure in one handler should not necessarily prevent other independent handlers from receiving the event. Define whether the logger swallows, reports, or propagates appender failures.

For typical application logging, protect the application and report through a minimal fallback sink.

## 13. Asynchronous appender

AsyncAppender wraps a real appender.

Components:

- bounded queue;
- worker thread;
- lifecycle state;
- overflow policy;
- failure counter/fallback;
- flush barrier.

Overflow choices:

| Policy | Trade-off |
|---|---|
| Block caller | preserves events, increases latency/deadlock risk |
| Drop newest | protects old queued events |
| Drop oldest | preserves recent information |
| Synchronous fallback | latency spike but may preserve event |
| Sample | bounded loss with metrics |

The policy must be explicit and observable.

### Flush

flush() should establish a barrier: every event accepted before the call is processed before flush returns, then delegate to the wrapped appender.

### Close

1. atomically stop accepting new events;
2. enqueue/signal shutdown;
3. drain according to contract;
4. join worker;
5. flush and close wrapped appender.

## 14. Configuration and hierarchy

LogManager can return a stable Logger by name.

Named hierarchy such as app.payment.checkout may inherit:

- threshold;
- handlers;
- propagation flag.

Be careful not to deliver the same event twice through child and parent handlers unintentionally. Configuration updates should publish an immutable snapshot so logging calls do not hold a global lock during I/O.

## 15. Context propagation

Request context can use a context-local mechanism:

    with log_context(request_id=..., user_id=...):
        logger.info("payment started")

Explicit call fields override or merge with ambient fields according to a documented rule.

Always clear scoped context. Thread-local storage alone is insufficient for some asynchronous runtimes; use the languageâ€™s context propagation facility.

## 16. Secret redaction

Redact before unsafe serialization/output.

Options:

- denylist known secret keys;
- allowlist permitted fields;
- typed Sensitive values;
- formatter/filter decorator.

Do not rely only on string replacement after formatting. Record redaction failures and keep the fallback sink safe.

## 17. Error policy

| Failure | Suggested handling |
|---|---|
| disabled level | return immediately |
| filter error | reject event and record internal metric |
| formatter error | fallback message without unsafe context |
| one appender fails | continue other handlers |
| queue full | apply configured overflow policy |
| worker failure | mark unhealthy; fallback/drop with metric |
| close called twice | idempotent |
| log after close | reject or use explicit fallback |

Never report an internal error through the same failing logger pipeline.

## 18. Patterns and principles

| Technique | Purpose |
|---|---|
| Strategy | formatter and filter variation |
| Composite/fan-out | several handlers |
| Decorator | async, retry, masking, sampling |
| Factory/manager | named logger configuration |
| Adapter | external stream/file/remote client |
| Immutable value | LogEvent |
| Producer-consumer | bounded asynchronous delivery |
| Dependency injection | clock, context provider, appenders |

Ordering of decorators matters: mask before remote output; retry around the destination; async placement determines where work occurs.

## 19. Concurrency

- Logger handler configuration is read from an immutable snapshot.
- LogEvent is immutable.
- Console/FileAppender serializes destination writes.
- Async queue provides producer/consumer coordination.
- close and append share a lifecycle lock/atomic state.
- Do not hold the manager configuration lock while formatting or doing I/O.
- Preserve per-appender event order if promised; global order across appenders is generally not guaranteed.

## 20. Complexity

For H handlers:

- disabled log call: O(1);
- dispatch: O(H) plus formatter and I/O cost;
- async enqueue: O(1) average;
- memory: O(queue capacity + retained configuration);
- flush: proportional to queued events and destination latency.

Filtering before formatting avoids unnecessary work.

## 21. Verification

Test:

- level ordering and thresholds;
- logger-level early rejection;
- different thresholds per handler;
- text and structured formatting;
- context merge and isolation;
- fan-out to multiple appenders;
- one handler failing while another succeeds;
- concurrent writes are not interleaved incorrectly;
- bounded queue overflow policies;
- flush barrier;
- close idempotency and log-after-close;
- worker failure fallback;
- secret redaction;
- no recursive failure logging;
- deterministic timestamps through Clock.

## 22. Extensibility

- **File rotation:** RotationPolicy around FileAppender.
- **Remote batching:** batching decorator with retry and circuit breaker.
- **Dynamic configuration:** atomic immutable config snapshots.
- **Metrics:** counters for accepted, dropped, failed, and queue depth.
- **Sampling:** Filter based on event key/rate.
- **Correlation:** ContextProvider.
- **Audit logging:** separate durable contract; do not treat best-effort logs as an audit ledger.
- **Distributed tracing:** adapter that maps trace/span context into fields.

## 23. Trade-offs

- Synchronous logging is simple and observable but adds request latency.
- Async logging isolates latency but introduces loss and lifecycle semantics.
- Hierarchical inheritance is convenient but can surprise users with duplicate output.
- Structured events improve analysis but require field governance.
- Swallowing failures protects the app; audit/security use cases may require a fail-closed contract.

## 24. Interview expectations

### Junior

Model Logger, levels, one Formatter, and console/file Appender.

### Mid-level

Add handlers, thresholds, multiple outputs, dependency separation, errors, and tests.

### Senior

Discuss immutable configuration, bounded async delivery, overflow, flush/close guarantees, failure isolation, context propagation, secret handling, and audit-log differences.

## 25. Interview walkthrough

1. Establish that this is an in-process library.
2. Draw Logger -> Handler -> Formatter -> Appender.
3. State early-filtering, immutable-event, and failure-isolation invariants.
4. Implement synchronous fan-out first.
5. Test threshold and one failing destination.
6. Add AsyncAppender as a decorator with explicit overflow and close contracts.
7. Discuss remote ingestion separately.

</details>
