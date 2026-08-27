# 5. Design Principles and Heuristics

## Outcome

Place responsibilities so likely changes stay local.

## Optimize for cohesion and coupling

- **High cohesion:** a class has one focused reason to exist.
- **Low coupling:** a class knows only the collaborators it needs.
- **Information hiding:** unstable decisions sit behind small interfaces.
- **Tell, do not ask:** ask objects to act instead of extracting their state.

These ideas are more useful than reciting acronyms.

## SOLID as questions

| Principle | Ask |
|---|---|
| Single responsibility | Which kind of change would edit this class? |
| Open/closed | Which known variation deserves a replaceable policy? |
| Liskov substitution | Can every implementation honor the same promises? |
| Interface segregation | Does each caller depend only on operations it uses? |
| Dependency inversion | Does domain code depend on a capability, not infrastructure? |

## Isolate real variation

If fee calculation varies, introduce a pricing policy. If it does not vary, a function is enough.

    class CheckoutService:
        def __init__(self, price_calculator, payment_gateway):
            self._prices = price_calculator
            self._payments = payment_gateway

Dependencies are explicit and independently replaceable. There is no need for a framework or container in a small interview solution.

## Use duplication as evidence

Do not abstract on the first example. A useful rule:

- first use: write the clearest code;
- second use: notice what differs;
- third use: extract the stable concept.

Premature abstraction couples unrelated cases through a guess.

## Design by trade-off

Every abstraction has a cost: more types, indirection, and concepts. Introduce it when it buys one of these:

- isolates a named change;
- protects an invariant;
- separates domain from an external system;
- enables a meaningful substitute in tests;
- removes repeated branching from core workflows.

## Common traps

- One interface per class.
- Pattern names used as justification.
- A “generic” engine before two concrete cases exist.
- A controller that performs all business logic.
- Applying SOLID to tiny value objects until the flow becomes unreadable.

## Readiness check

For each abstraction, you can name the change it isolates and the simpler alternative you rejected.

Next: [Creational patterns](./06-creational-design-patterns.md).
