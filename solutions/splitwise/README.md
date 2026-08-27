# Splitwise

Record shared expenses, calculate exact participant shares, maintain pairwise balances, and settle debts.

## Scope

Support users, groups, equal/exact/percentage splits, expenses, balances, settlements, and optional debt simplification. Payments and currency conversion are outside the core.

## Model

| Type | Responsibility |
|---|---|
| User | participant identity |
| Group | membership and expense history |
| Expense | payer, amount, splits, and description |
| Split | one participant’s exact share |
| SplitStrategy | validates and calculates shares |
| BalanceSheet | pairwise net ledger |
| Settlement | recorded repayment |
| SplitwiseService | coordinates expenses and settlements |

Invariant: the sum of splits equals the expense exactly. Pairwise balances are antisymmetric:

    balance(A, B) = -balance(B, A)

## Add-expense flow

1. Validate payer, participants, currency, and positive total.
2. Select equal, exact, or percentage SplitStrategy.
3. Calculate shares and assign any rounding remainder deterministically.
4. Create an immutable Expense.
5. Atomically update the balance sheet.
6. Append to group history.

For each participant, the payer is owed that participant’s share; the payer’s own share creates no debt.

## Design choices

- Money uses Decimal and one explicit rounding rule.
- Split strategies isolate algorithms and validation.
- A small factory selects the strategy from input type.
- BalanceSheet owns normalization and netting.
- Debt simplification is a view/optimization, not a rewrite of expense history.

## Correctness

Expense creation and ledger updates share one transaction. An idempotency key prevents duplicate client retries. Concurrent settlements use versions or conditional balance updates.

## Run

    python "solutions/splitwise/main.py"
    python -m unittest discover -s "solutions/splitwise/tests" -t "solutions/splitwise" -v

## Follow-ups

Add multi-currency groups, recurring expenses, edit history, payment integration, optimized settlements, and audit events.
