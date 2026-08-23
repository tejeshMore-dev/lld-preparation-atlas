# Low-Level Design Preparation

A structured Python 3.10+ repository for learning low-level design, practising
interview execution, and reviewing runnable implementations with tests.

This repository contains two connected resources:

- A topic-by-topic [LLD Preparation Bible](./docs/README.md).
- A catalogue of [working LLD solutions](./solutions/README.md).

## Choose your path

### Learn LLD systematically

1. Open the [curriculum index](./docs/README.md).
2. Follow the [preparation roadmap](./docs/roadmap.md).
3. Complete each topic's exercises and mastery gate.
4. Apply the topic to implementations under `solutions/`.

### Review or practise a design problem

1. Choose a problem from the [solution catalogue](./solutions/README.md).
2. Read its requirements and invariants before inspecting code.
3. Predict the object model and critical workflow.
4. Run the demonstration and tests.
5. Compare the implementation with your design.
6. Attempt the advancement exercises in the solution guide.

## Repository structure

```text
lld-solutions/
|-- README.md
|-- docs/
|   |-- README.md                       # Curriculum index
|   |-- roadmap.md                      # Topic order and completion criteria
|   |-- topics/                         # One file per major LLD topic
|   |-- practice/                       # Problems, mocks, rubric, readiness
|   `-- templates/                      # Reusable design and README templates
|-- solutions/
|   |-- README.md                       # Implemented-solution catalogue
|   |-- parking-lot/
|   |-- library-management/
|   `-- ...
`-- scripts/
    `-- run-all-tests.ps1               # Full repository verification
```

## Requirements

- Python 3.10 or newer.
- PowerShell for the repository-wide test script.
- No third-party Python packages.

## Quick start

Run one demonstration from the repository root:

```powershell
python "solutions/parking-lot/main.py"
```

Run its tests:

```powershell
python -m unittest discover -s "solutions/parking-lot/tests" -t "solutions/parking-lot" -v
```

Run every solution test suite:

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/run-all-tests.ps1"
```

## Curriculum progress

| Topic | Status |
|---|---|
| [Requirements Analysis and Scope Definition](./docs/topics/01-requirements-analysis.md) | Complete |
| [Python and Object-Oriented Foundations](./docs/topics/02-python-oop-foundations.md) | Complete |
| [Domain Modeling and Responsibility Assignment](./docs/topics/03-domain-modeling-and-responsibility-assignment.md) | Complete |
| [UML and Interaction Modeling](./docs/topics/04-uml-and-interaction-modeling.md) | Complete |
| [Design Principles and Heuristics](./docs/topics/05-design-principles-and-heuristics.md) | Complete |
| [Creational Design Patterns](./docs/topics/06-creational-design-patterns.md) | Complete |
| [Structural Design Patterns](./docs/topics/07-structural-design-patterns.md) | Complete |
| Behavioral Design Patterns | Next |

See the [roadmap](./docs/roadmap.md) for all fifteen topics.

## Practice and assessment

- [Problem catalogue](./docs/practice/problem-catalog.md)
- [Interview workflow](./docs/practice/interview-workflow.md)
- [Mock-interview rubric](./docs/practice/mock-interview-rubric.md)
- [Final readiness checklist](./docs/practice/readiness-checklist.md)
- [Design-brief template](./docs/templates/design-brief-template.md)

## Adding a solution

1. Use a lowercase kebab-case directory under `solutions/`.
2. Keep the implementation self-contained with its own `main.py` and `tests/`.
3. Follow the [solution README template](./docs/templates/solution-readme-template.md).
4. Add the solution to `solutions/README.md` and `scripts/run-all-tests.ps1`.
5. Run the entire test suite before considering the solution complete.
