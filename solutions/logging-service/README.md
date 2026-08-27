# Logging Service

Design an in-process logger with levels, structured events, formatting, and multiple outputs.

## Scope

Support level filtering, contextual fields, configurable formatters, and several appenders. Distributed log collection, indexing, and alerting are external systems.

## Model

| Type | Responsibility |
|---|---|
| LogEvent | immutable timestamp, level, message, context, and error |
| Logger | creates events and applies its threshold |
| Formatter | converts an event to bytes or text |
| Appender | writes a formatted event to one destination |
| Handler | combines threshold, formatter, and appender |
| LogManager | named logger configuration |

Flow:

    call -> Logger -> LogEvent -> Handler(s) -> Formatter -> Appender

## Critical flow

1. Return early when the logger threshold rejects the level.
2. Capture time and context once in an immutable event.
3. Send the same event to each eligible handler.
4. Each handler formats and appends it.
5. Apply the configured failure policy if an appender fails.

Logging should not recursively log its own internal failure.

## Design decisions

- Formatter and Appender are strategies with different responsibilities.
- Handlers allow different levels and formats per destination.
- Decorators can add sampling, masking, or retry, but composition order must be explicit.
- Child loggers may inherit configuration; avoid surprising duplicate propagation.
- Structured context is data, not string concatenation.

## Concurrency and performance

Console and file appenders need serialized writes. An asynchronous appender can place immutable events on a bounded queue. Define overflow behavior: block, drop newest, drop oldest, or fall back synchronously.

Flush and close must drain accepted events. Never hold the configuration lock while doing destination I/O.

## Follow-ups

- JSON formatting and secret redaction.
- File rotation.
- Correlation context scoped to a request.
- Dynamic configuration.
- Batched remote appender with retry.

## Interview finish

Implement LogEvent, Logger, Handler, one formatter, console/memory appenders, and tests for thresholds, context, fan-out, appender failure, and concurrent writes.
