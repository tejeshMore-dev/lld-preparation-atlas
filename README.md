# Low-Level Design Solutions

Python implementations of common low-level design problems, with detailed
explanations and tests inside each solution.

## Available solutions

| Solution | Concepts covered | Links |
|---|---|---|
| Parking Lot | Strategy, Decorator, dependency injection, allocation, pricing, payments, state management, thread safety | [Open solution](./Parking%20lot/) / [Read guide](./Parking%20lot/README.md) |
| Library Management | Strategy, Factory, Observer, inheritance, catalog search, loans, fines, FIFO reservations, state machines | [Open solution](./library%20management/) / [Read guide](./library%20management/README.md) |
| Splitwise | Strategy, Factory, precise money, equal/exact/percentage splits, debt netting, settlements, simplification | [Open solution](./Splitwise/) / [Read guide](./Splitwise/README.md) |
| Elevator | Strategy, controller orchestration, scheduling, LOOK routing, request/state machines, discrete simulation, safety rules | [Open solution](./Elevator/) / [Read guide](./Elevator/README.md) |
| ATM | State machines, secure PIN concepts, Gateway, Strategy, precise money, exact cash dispensing, transactions, compensation | [Open solution](./ATM/) / [Read guide](./ATM/README.md) |
| Movie Ticket Booking | Seat holds, concurrent double-booking protection, state machines, Strategy, Decorator, Gateway, exact money, refunds | [Open solution](./Movie%20Ticket%20Booking/) / [Read guide](./Movie%20Ticket%20Booking/README.md) |
| Hotel Management | Date-range availability, room holds, concurrent reservation protection, Strategy, Decorator, folios, check-in/out, refunds | [Open solution](./Hotel%20Management/) / [Read guide](./Hotel%20Management/README.md) |

## Requirements

- Python 3.10 or newer
- No third-party packages

## Run demonstrations

From the repository root:

```powershell
python "Parking lot/main.py"
python "library management/main.py"
python "Splitwise/main.py"
python "Elevator/main.py"
python "ATM/main.py"
python "Movie Ticket Booking/main.py"
python "Hotel Management/main.py"
```

## Run tests

```powershell
python -m unittest discover -s "Parking lot/tests" -t "Parking lot" -v
python -m unittest discover -s "library management/tests" -t "library management" -v
python -m unittest discover -s "Splitwise/tests" -t "Splitwise" -v
python -m unittest discover -s "Elevator/tests" -t "Elevator" -v
python -m unittest discover -s "ATM/tests" -t "ATM" -v
python -m unittest discover -s "Movie Ticket Booking/tests" -t "Movie Ticket Booking" -v
python -m unittest discover -s "Hotel Management/tests" -t "Hotel Management" -v
```

Each solution README contains its requirements, architecture, workflows, class
relationships, OOP and SOLID explanations, design-pattern walkthroughs,
complexity analysis, limitations, and advancement exercises.
