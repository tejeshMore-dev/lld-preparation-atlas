# 6. Creational Patterns

## Outcome

Control construction when creating an object is itself a meaningful decision.

## Decision guide

| Need | Pattern or technique |
|---|---|
| A few validated fields | Constructor or factory function |
| A readable object with many optional parts | Builder |
| Choose one concrete family at runtime | Factory method |
| Create several matching products | Abstract factory |
| Exactly one process-wide instance | Usually avoid; inject one instance instead |
| Copy a configured template | Prototype or explicit clone |

Start with a constructor. Add a pattern only when creation rules are changing or leaking into callers.

## Factory

A factory centralizes a choice and returns a useful abstraction.

    def create_rate_limiter(config, clock):
        if config.algorithm == "token_bucket":
            return TokenBucket(config.capacity, config.rate, clock)
        if config.algorithm == "fixed_window":
            return FixedWindow(config.limit, config.window, clock)
        raise ValueError("unsupported algorithm")

The factory owns selection. Each limiter still owns its behavior.

## Builder

Use a builder when named, stepwise construction improves validation or readability. Python keyword arguments often make a builder unnecessary.

    report = Report(title="Daily", format=PDF, include_summary=True)

Prefer this over a fluent builder unless construction has ordered steps or complex cross-field rules.

## Dependency injection is the default

Create objects at the application edge and pass collaborators inward. This makes lifecycle and ownership visible without a service locator or singleton.

## Common traps

- A factory that only calls one constructor.
- Static global access disguised as Singleton.
- Builders for objects with three required fields.
- Returning concrete types from a supposedly stable factory boundary.
- Mixing object creation with domain workflow.

## Readiness check

You can choose between a constructor, function, factory, and builder based on a concrete creation problem.

Next: [Structural patterns](./07-structural-design-patterns.md).
