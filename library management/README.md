# Library Management LLD

An in-memory Python low-level design for catalog search, physical book copies,
member-specific borrowing rules, loans, overdue fines, reservations,
notifications, and observer-based event handling.

## Design

- `Catalog` owns searchable book metadata.
- `BookItem` represents a physical copy and tracks availability, borrower, and
  reservation ownership.
- `StudentMember` and `FacultyMember` provide different borrowing limits and
  loan periods.
- `LibraryService` coordinates borrowing, returns, FIFO reservations, fine
  payments, and domain events.
- `FineStrategy` makes fine calculation replaceable.
- `Subject` and `Observer` decouple logging and email-style event handling.
- `MemberFactory` centralizes creation of supported member types.

Reservation state moves through `WAITING -> READY -> COMPLETED`. It can move to
`CANCELLED` from either `WAITING` or `READY`. A ready physical copy is held for
the matching member.

## Run

From this directory:

```powershell
python main.py
python -m unittest discover -s tests -v
```

The implementation stores data in memory; persistence, authentication, and a
network API are intentionally outside this LLD's scope.
