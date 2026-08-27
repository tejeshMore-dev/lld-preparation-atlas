# ATM

Coordinate an authenticated session, bank authorization, and physical cash while keeping balances and machine inventory consistent.

## Scope

Support card sessions, PIN authentication, balance inquiry, withdrawal, deposit, transfer, and a bounded cash dispenser. Real device drivers, networking, and fraud systems are external.

## Model

| Type | Responsibility |
|---|---|
| Card and Account | identity and bank state |
| ATM | session and transaction orchestration |
| BankGateway | authorization and account operations |
| CashDispenser | note inventory and dispensing |
| CashSelectionStrategy | chooses an exact note combination |
| Transaction | immutable/auditable operation record |
| Money | exact amount and currency |

## Withdrawal flow

1. Require an authenticated session and valid amount.
2. Reserve or select an exact note combination.
3. Ask the bank to debit the account.
4. Dispense the selected notes.
5. Record success and return the card/session state.

If debit succeeds but dispensing fails, compensate or mark the transaction for reconciliation. The order is a trade-off, not something an in-memory lock can solve across systems.

## Design choices

- ATM acts as a facade and application service.
- BankGateway and CashSelectionStrategy are replaceable boundaries.
- CashDispenser owns note counts.
- Session state and transaction state are separate lifecycles.
- Decimal-backed Money prevents float errors.

## Correctness

Cash selection and note deduction are one local critical section. Transfers require an atomic bank operation. Authentication attempts and card retention are security policies, not subclasses.

## Run

    python "solutions/atm/main.py"
    python -m unittest discover -s "solutions/atm/tests" -t "solutions/atm" -v

## Follow-ups

Add withdrawal limits, denomination replenishment, partial device failure, offline mode, receipt printing, and reconciliation.
