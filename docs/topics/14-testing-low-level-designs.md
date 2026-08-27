# 14. Testing Low-Level Designs

## Outcome

Prove behavior, boundaries, and invariants with a small, trustworthy test suite.

## Test by responsibility

| Layer | Prove |
|---|---|
| Value object | validation and equality |
| Entity or aggregate | state transitions and invariants |
| Policy | decision table and edge cases |
| Application service | orchestration and failure ordering |
| Adapter | translation to an external contract |
| Concurrency boundary | competing operations preserve the invariant |

Most domain tests need no mocks.

## Test shape

Use Arrange, Act, Assert and name the business fact.

    def test_second_customer_cannot_hold_same_seat(self):
        seat = Seat("A1")
        seat.hold("customer-1")

        with self.assertRaises(SeatUnavailable):
            seat.hold("customer-2")

        self.assertEqual(seat.customer_id, "customer-1")

The final assertion proves failure did not corrupt state.

## Fakes, stubs, and mocks

- **Fake:** working in-memory implementation, useful for repositories.
- **Stub:** returns controlled data.
- **Spy/mock:** records interaction, useful when the interaction is the behavior.

Mock external boundaries, clocks, randomness, and slow resources. Avoid mocking the object under test’s domain collaborators merely to mirror implementation.

## Determinism

Inject a clock and ID source when time or randomness affects behavior. Tests should not sleep or rely on wall-clock timing.

## Test the decision table

For every core rule, cover:

- normal success;
- boundary value;
- expected rejection;
- state after rejection;
- likely follow-up variant.

A few focused tests are stronger than broad tests with many unrelated assertions.

## Concurrency tests

Coordinate competing threads at a barrier, release them together, and assert the invariant: exactly one winner, no partial state, expected loser error.

## Common traps

- Testing private methods.
- One integration test as the entire suite.
- Exact call-order assertions that do not matter to the contract.
- Flaky sleeps in concurrent tests.
- Coverage percentage treated as design evidence.

## Readiness check

You can map every important invariant to a focused test and explain what a failure would mean.

Next: [Interview execution](./15-interview-execution-problem-practice-and-readiness.md).
