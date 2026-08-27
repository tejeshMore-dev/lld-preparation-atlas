# 7. Structural Patterns

## Outcome

Connect objects and external systems without leaking their shape through the domain.

## Decision guide

| Need | Pattern |
|---|---|
| Convert one interface into another | Adapter |
| Add optional behavior around a call | Decorator |
| Present a small entry point to a subsystem | Facade |
| Control access, caching, or lazy loading | Proxy |
| Separate abstraction from platform variation | Bridge |
| Treat individual and grouped nodes uniformly | Composite |

## Adapter

An adapter translates an external API into a domain-facing capability.

    class StripePaymentGateway:
        def __init__(self, client):
            self._client = client

        def charge(self, payment):
            response = self._client.create_charge(
                cents=payment.amount_in_cents,
                token=payment.token,
            )
            return Receipt(response["id"])

The checkout service should know charge(), not Stripe response fields.

## Decorator

A decorator preserves a contract while adding behavior:

    gateway = RetryingGateway(LoggingGateway(real_gateway))

Ordering matters. Retrying outside logging produces different observations from logging outside retrying.

## Facade versus service

A facade simplifies an existing subsystem. An application service coordinates a use case and may enforce workflow rules. Do not call every orchestration class a facade.

## Composite

Composite fits real recursive structures such as files and directories. It is a poor fit when leaf and container operations have different promises.

## Common traps

- Wrappers that expose the wrapped implementation anyway.
- Decorators that change the contract or swallow failures.
- A facade that becomes the entire domain model.
- Proxy behavior that surprises callers.
- Pattern layers added only to “decouple” already stable code.

## Readiness check

You can point to the boundary being adapted, wrapped, simplified, or controlled.

Next: [Behavioral patterns](./08-behavioral-design-patterns.md).
