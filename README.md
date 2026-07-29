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
```

## Run tests

```powershell
python -m unittest discover -s "Parking lot/tests" -t "Parking lot" -v
python -m unittest discover -s "library management/tests" -t "library management" -v
python -m unittest discover -s "Splitwise/tests" -t "Splitwise" -v
python -m unittest discover -s "Elevator/tests" -t "Elevator" -v
```

Each solution README contains its requirements, architecture, workflows, class
relationships, OOP and SOLID explanations, design-pattern walkthroughs,
complexity analysis, limitations, and advancement exercises.
