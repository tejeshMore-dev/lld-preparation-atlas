# Low-Level Design Interview Guide

A practical Python repository for learning object-oriented design and explaining it clearly in an interview.

The goal is not to memorize class diagrams or force design patterns. It is to turn a small set of requirements into code that is easy to change, test, and discuss.

## The interview loop

Use the same loop for every problem:

1. **Clarify** the actors, use cases, rules, and scope.
2. **Model** the state, responsibilities, and invariants.
3. **Walk** one critical flow before writing code.
4. **Implement** a thin end-to-end slice.
5. **Verify** happy paths, failures, and shared-state risks.
6. **Adapt** the design to one likely follow-up.

That is the core of this repository.

## Start here

- [Curriculum](./docs/README.md) — the shortest useful learning path.
- [Roadmap](./docs/roadmap.md) — a four-phase study plan.
- [Problem breakdowns](./solutions/README.md) — runnable and design-only examples.
- [Practice kit](./docs/practice/README.md) — prompts, mocks, and scoring.
- [Progress tracker](https://tejeshmore-dev.github.io/lld-preparation-atlas/) — private browser-local progress.

If time is limited, study Topics 1, 3, 5, 8, 11, and 15, then solve three problems.

## What is covered

The core path covers requirements, object modeling, OOP, design principles, useful patterns, concurrency, and interview delivery.

The extended path adds topics often skipped by introductory LLD guides:

- UML and interaction sketches
- application-service and repository boundaries
- API and error contracts
- transactions and persistence
- refactoring and test strategy

## Repository map

    docs/topics/       concise concept chapters
    docs/practice/     prompts, rubric, and readiness checks
    docs/templates/    reusable interview notes
    solutions/         problem breakdowns, code, and tests
    site/              local-progress web app
    scripts/           repository verification

## Run the code

Requires Python 3.10+ and no third-party Python packages.

    python "solutions/parking-lot/main.py"
    python -m unittest discover -s "solutions/parking-lot/tests" -t "solutions/parking-lot" -v
    powershell -ExecutionPolicy Bypass -File "scripts/run-all-tests.ps1"

Tracker tests:

    npm.cmd test --prefix site

## A good solution

A strong LLD answer has:

- a small, explicit scope;
- behavior close to the state it protects;
- dependencies passed through narrow interfaces;
- one clear owner for each invariant;
- deliberate handling of failure and concurrency;
- tests around behavior, not implementation trivia.

Use patterns only when they make a change easier to absorb.
