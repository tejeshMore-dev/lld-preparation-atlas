# Library Management

Search a catalogue, lend physical copies, manage reservations, return items, and calculate fines.

## Scope

Support books, book copies, members, librarians, search, loans, reservations, fines, and notifications. Acquisition and inter-library lending are outside the core.

## Model

| Type | Responsibility |
|---|---|
| Book | title-level bibliographic data |
| BookItem | one physical copy and its status |
| Catalog | search indexes |
| Member | borrowing eligibility and limits |
| Loan | checkout, due date, and return |
| Reservation | queue/lifecycle for a title or copy |
| FineStrategy | calculates overdue charge |
| LibraryService | borrow, return, reserve, and renew |

The central distinction is Book versus BookItem: many physical copies share one title.

## Borrow flow

1. Validate member account and borrowing limit.
2. Load the copy and any reservation priority.
3. Atomically mark the copy loaned and create a Loan.
4. Record the due date and notify interested observers.

Return closes the loan, calculates a fine through FineStrategy, and makes the copy available or reserved for the next member.

## Design choices

- BookItem owns copy state.
- Loan owns due/returned lifecycle.
- FineStrategy varies member and item rules.
- MemberFactory demonstrates creation by member type.
- Observer handles secondary notifications and logging.
- Composition is preferred to deeper member inheritance for new policies.

## Correctness

Copy availability check and loan creation must be atomic. Reservation queue advancement and return should commit together. Notification failure must not undo a valid return.

## Run

    python "solutions/library-management/main.py"
    python -m unittest discover -s "solutions/library-management/tests" -t "solutions/library-management" -v

## Follow-ups

Add renewals, copy holds, lost-item charges, e-books, branches, transfers, and waitlist notifications.
