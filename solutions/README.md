# LLD Problem Breakdowns

Each guide follows the same interview-first shape: scope, model, critical flow, decisions, correctness, and follow-ups.

## Runnable Python solutions

| Problem | Main design pressure |
|---|---|
| [Airline Reservation](./airline-reservation/) | per-flight seat inventory and booking lifecycle |
| [ATM](./atm/) | session state, cash selection, and compensation |
| [Cab Booking](./cab-booking/) | driver matching and exclusive assignment |
| [Coupon Platform](./coupon-management-and-distribution-platform/) | eligibility, supply, and redemption |
| [Elevator](./elevator/) | scheduling and car state |
| [Food Delivery](./food-delivery/) | order lifecycle and courier assignment |
| [Hotel Management](./hotel-management/) | date-range inventory and folio |
| [Library Management](./library-management/) | title versus copy and loan rules |
| [Movie Ticket Booking](./movie-ticket-booking/) | seat holds and double-booking |
| [Parking Lot](./parking-lot/) | spot allocation, tickets, and pricing |
| [Splitwise](./splitwise/) | exact splits and balance invariants |

Run any solution with:

    python "solutions/<name>/main.py"
    python -m unittest discover -s "solutions/<name>/tests" -t "solutions/<name>" -v

Run all runnable suites:

    powershell -ExecutionPolicy Bypass -File "scripts/run-all-tests.ps1"

## Design walkthroughs

These are concise Markdown designs intended for a blank-file interview exercise.

| Problem | Main design pressure |
|---|---|
| [Amazon Locker](./amazon-locker/) | package sizing, codes, and expiry |
| [Connect Four](./connect-four/) | board rules, turns, and win detection |
| [File System](./file-system/) | recursive hierarchy and path resolution |
| [Inventory Management](./inventory-management/) | stock ledger and reservations |
| [Logging Service](./logging-service/) | filtering, formatting, and fan-out |
| [Rate Limiter](./rate-limiter/) | atomic admission under time windows |

## How to use a guide

1. Read only the scope.
2. Design for 15 minutes from a blank page.
3. Compare models and invariants.
4. Trace the critical flow.
5. Implement one slice and one failure test.
6. Try a follow-up without rereading the guide.
