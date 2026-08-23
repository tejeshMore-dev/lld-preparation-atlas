# Implemented LLD Solutions

Each directory contains a self-contained Python implementation, tests, a
demonstration entry point, and a detailed design guide.

## Catalogue

| Solution | Primary coverage | Guide |
|---|---|---|
| Parking Lot | Allocation, pricing, payments, state, thread safety | [Open](./parking-lot/README.md) |
| Library Management | Loans, reservations, fines, observers, inheritance | [Open](./library-management/README.md) |
| Splitwise | Split policies, money, balances, settlement | [Open](./splitwise/README.md) |
| Elevator | Scheduling, request lifecycle, state, simulation | [Open](./elevator/README.md) |
| ATM | Session state, gateways, cash selection, compensation | [Open](./atm/README.md) |
| Movie Ticket Booking | Seat holds, expiry, locking, payments, refunds | [Open](./movie-ticket-booking/README.md) |
| Hotel Management | Date ranges, availability, booking lifecycle, folios | [Open](./hotel-management/README.md) |
| Airline Reservation | Seat inventory, booking, pricing, check-in | [Open](./airline-reservation/README.md) |
| Cab Booking | Distance, driver matching, dispatch, fare, payment | [Open](./cab-booking/README.md) |
| Food Delivery | Cart, ordering, partner matching, payment, refund | [Open](./food-delivery/README.md) |
| Coupon Platform | Eligibility, distribution, discount, redemption | [Open](./coupon-management-and-distribution-platform/README.md) |

## Standard solution layout

```text
solutions/<problem>/
|-- README.md
|-- main.py
|-- models/
|-- services/
|-- strategies/       # when the problem has replaceable policies
|-- factories/        # when construction requires a dedicated boundary
|-- observers/        # when event subscribers are present
`-- tests/
```

Optional directories should exist only when the design needs them.

## Run a solution

From the repository root:

```powershell
python "solutions/parking-lot/main.py"
python -m unittest discover -s "solutions/parking-lot/tests" -t "solutions/parking-lot" -v
```

Replace `parking-lot` with another directory name from the catalogue.

Run all solution tests with:

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/run-all-tests.ps1"
```

## Review method

For each solution:

1. Read the requirements, assumptions, and out-of-scope list.
2. Identify the owner of every important invariant.
3. Walk through the critical success and failure sequences.
4. Locate the contracts introduced for variation or external boundaries.
5. Run the tests as executable requirements.
6. Attempt one follow-up change before reading the suggested extension.

The [problem catalogue](../docs/practice/problem-catalog.md) tracks current and
recommended future coverage.
