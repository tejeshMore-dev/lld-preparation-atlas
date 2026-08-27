# 4. UML and Interaction Sketches

## Outcome

Use small diagrams to expose design mistakes and communicate a workflow. This is an extension topic; interviews rarely need formal UML notation.

## Draw only what answers a question

| Diagram | Use it when you need to show |
|---|---|
| Class diagram | ownership, important fields, and dependencies |
| Sequence diagram | call order, failure order, and transaction boundary |
| State diagram | legal lifecycle transitions |
| Component sketch | adapters around the domain |

A diagram is disposable reasoning, not a second implementation.

## Class sketch

Show only meaningful relationships and methods.

    classDiagram
      ParkingService --> SpotAllocationPolicy
      ParkingService --> TicketRepository
      Ticket *-- Vehicle
      Ticket --> ParkingSpot

Avoid listing every getter, constructor, or primitive field.

## Sequence sketch

    sequenceDiagram
      User->>BookingService: hold(show, seats)
      BookingService->>Show: tryHold(seats)
      Show-->>BookingService: hold
      BookingService->>HoldRepository: save(hold)
      BookingService-->>User: holdId

Add alternative branches only for the failures that shape the design.

## State sketch

State machines are useful when operations depend on lifecycle:

    CREATED -> ACTIVE -> PAID -> CLOSED
                 |
                 -> EXPIRED

Write transitions as behavior such as pay() or expire(), not unrestricted status assignment.

## Keep diagrams aligned with code

A useful diagram has:

- the same names as the code;
- arrows that match real dependencies;
- one visible owner for each mutable state;
- no class added only to make the picture look layered.

If the diagram takes longer to explain than the workflow, delete detail.

## Common traps

- Treating aggregation and composition symbols as the main design problem.
- Drawing a complete system before agreeing on scope.
- Diagrams with boxes but no behavior.
- Sequence diagrams that omit failure or rollback.
- Keeping stale diagrams after code changes.

## Readiness check

You can sketch the core classes and one critical sequence in under five minutes, then explain a design decision the sketch revealed.

Next: [Design principles](./05-design-principles-and-heuristics.md).
