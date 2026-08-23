# Topic 2 - Python and Object-Oriented Foundations

[Curriculum index](../README.md) | [Preparation roadmap](../roadmap.md) |
[Previous topic](./01-requirements-analysis.md)

- **Category:** Programming and design foundations
- **Difficulty:** Beginner to intermediate
- **Priority:** Essential
- **Prerequisites:** Topic 1, Python syntax, functions, and basic collections
- **Running example:** A small parking domain
- **Output:** A valid, encapsulated, testable Python object model

## Outcome

After completing this topic, you should be able to:

- Explain identity, equality, references, mutability, and copying in Python.
- Create classes that begin valid and protect their invariants.
- Separate public behavior from internal representation.
- Use abstraction, inheritance, polymorphism, and composition intentionally.
- Express narrow contracts with `ABC` or `Protocol`.
- Distinguish dependency, association, aggregation, and composition.
- Choose suitable equality, hashing, and immutability semantics.
- Use dataclasses, enums, type hints, collections, and generics safely.
- Inject dependencies instead of hiding their construction inside domain logic.
- Model failures without leaving objects partially mutated.
- Organize a small solution into cohesive Python modules.
- Explain why each language feature supports the design rather than merely
  naming an OOP concept.

## Core idea

LLD is not the act of drawing many classes. It is the act of assigning state,
behavior, ownership, and contracts so that business rules remain true as the
system changes.

```text
Object = identity or value + state + behavior + invariants

Good collaboration = narrow contract + explicit dependency + clear ownership
```

Python makes it easy to create objects and equally easy to share mutable state,
leak internals, or depend on concrete implementations accidentally. Sound LLD
requires understanding both OOP ideas and Python's actual object model.

## Scope boundary

This topic teaches the language and OOP mechanics needed by later chapters. It
does not attempt to teach:

- Full domain discovery and responsibility assignment.
- The complete SOLID catalogue.
- GoF design patterns.
- UML notation.
- Thread synchronization.
- Database mapping and transaction design.
- Framework-specific dependency-injection containers.
- Metaclasses, descriptors, garbage-collector internals, or advanced generic
  variance.

Those subjects either have dedicated topics or have low interview value for a
first LLD pass.

Code fences in this chapter are focused excerpts. Some reuse types or imports
introduced in an earlier fence. When moving them into a standalone Python 3.10
module, add the required imports and consider
`from __future__ import annotations` for self or later-defined type references.

## 1. Learn

### 1.1 Python's object model

Python variables are names bound to objects. A variable does not contain a
private copy of an object.

```python
items = ['ticket']
alias = items
alias.append('receipt')

assert items == ['ticket', 'receipt']
assert alias is items
```

Both names refer to the same list, so mutation through either name is visible
through the other. This matters whenever an object receives or returns a
mutable collection.

Every Python object has three relevant properties:

- **Identity:** which particular object it is; compare with `is`.
- **Type:** what operations and behavior it supports.
- **Value:** the logical content used by `==` when equality is defined.

Use `is` for identity questions, most commonly `value is None`. Enum members
are also singletons, so identity comparison is valid when used deliberately.
Use `==` for strings, numbers, domain values, and ordinary value equality.

#### Mutation versus reassignment

```python
def add_spot(spots: list[str]) -> None:
    spots.append('S2')       # mutates the caller's list


def replace_spots(spots: list[str]) -> None:
    spots = ['S9']           # only rebinds the local name
```

Passing an object to a function passes another reference to that object.
Reassignment changes the local binding. Mutation changes the shared object.

#### Shallow and deep copies

- `list(original)` and `copy.copy(original)` create a shallow outer copy.
- Nested mutable objects remain shared after a shallow copy.
- `copy.deepcopy(original)` recursively copies supported nested objects.
- Deep copying a domain graph blindly can duplicate identity-bearing entities
  and external-resource handles incorrectly.

Prefer explicit domain copy operations, immutable values, or controlled
snapshots when ownership matters.

### 1.2 Class fundamentals

#### Instance attributes and class attributes

Instance attributes belong to one object. Class attributes are shared through
the class unless an instance shadows them.

```python
class BrokenCart:
    items: list[str] = []  # shared by every instance


class Cart:
    def __init__(self) -> None:
        self._items: list[str] = []  # independent per instance
```

Use class attributes for genuine class-wide constants or deliberately shared
state, not as accidental mutable defaults.

Use `ClassVar` to tell dataclasses and type checkers that a declared attribute
belongs to the class rather than each instance:

```python
from typing import ClassVar


class Ticket:
    MINIMUM_BILLING_MINUTES: ClassVar[int] = 60
```

#### Constructors should establish validity

An object should be usable immediately after successful construction.

```python
class ParkingFloor:
    def __init__(self, floor_id: str) -> None:
        if not floor_id.strip():
            raise ValueError('Floor ID cannot be empty')
        self.floor_id = floor_id
        self._spots: dict[str, ParkingSpot] = {}
```

Avoid two-step initialization in which callers can forget to invoke `setup()`
or temporarily observe missing required fields.

#### Instance, class, and static methods

| Form | Receives | Good use |
|---|---|---|
| Instance method | `self` | Behavior using object state |
| `@classmethod` | `cls` | Named alternative constructor or class-aware behavior |
| `@staticmethod` | Nothing implicit | Small stateless helper strongly related to the class |
| Module function | Nothing implicit | Stateless behavior not owned by one class |

```python
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class Membership:
    member_id: str
    expires_on: date

    def __post_init__(self) -> None:
        if not self.is_valid_id(self.member_id):
            raise ValueError('Member ID cannot be empty')

    @classmethod
    def trial(cls, member_id: str, start: date) -> 'Membership':
        return cls(member_id, start + timedelta(days=30))

    @staticmethod
    def is_valid_id(member_id: str) -> bool:
        return bool(member_id.strip())
```

A named constructor expresses intent better than a long constructor filled
with flags. A static method should not be used merely to place every helper
inside a class.

Strictly, `__new__` creates an instance and `__init__` initializes the already
created instance. Normal LLD code rarely needs to override `__new__`; the
important rule is that successful initialization leaves a valid object.

#### Properties

A property exposes inexpensive, field-like derived state while retaining a
method boundary.

```python
class CashDrawer:
    def __init__(self, notes: dict[int, int]) -> None:
        self._notes = dict(notes)

    @property
    def total_cash(self) -> int:
        return sum(value * count for value, count in self._notes.items())
```

Do not hide expensive I/O, network calls, or surprising side effects behind a
property. Such operations deserve explicit method names.

#### Python visibility conventions

- `name` is public API.
- `_name` means internal implementation by convention.
- `__name` triggers name mangling mainly to avoid accidental subclass clashes.
- Neither underscore form is a security boundary.

Encapsulation in Python is achieved through a small documented API and control
over mutation, not through pretending that internal attributes are impossible
to access.

#### Overriding versus overloading

Python supports overriding: a subclass can provide a compatible implementation
of an inherited method.

Python does not provide Java-style runtime method overloading by parameter
signature. A later definition replaces an earlier method with the same name.
`typing.overload` describes alternative signatures to a static type checker; it
does not implement runtime dispatch.

Prefer explicit method names, named constructors, default arguments, or a
single method that accepts a well-defined union.

### 1.3 Encapsulation

Encapsulation places behavior beside the state and rules that behavior must
protect. Mechanical getters and setters are not enough.

```python
class ParkingSpot:
    def __init__(self, spot_id: str) -> None:
        if not spot_id.strip():
            raise ValueError('Spot ID cannot be empty')
        self.spot_id = spot_id
        self._vehicle: Vehicle | None = None

    @property
    def is_occupied(self) -> bool:
        return self._vehicle is not None

    def assign(self, vehicle: 'Vehicle') -> None:
        if self.is_occupied:
            raise SpotOccupiedError(self.spot_id)
        self._vehicle = vehicle

    def vacate(self, vehicle: 'Vehicle') -> None:
        if self._vehicle != vehicle:
            raise VehicleMismatchError(self.spot_id)
        self._vehicle = None
```

The caller requests `assign` or `vacate`; it does not coordinate two public
fields and hope they stay consistent.

Strong encapsulation means:

- Constructors establish invariants.
- State changes happen through intention-revealing behavior.
- Validation occurs before mutation.
- Internal mutable collections are not returned directly.
- One object owns each source of truth.
- Invalid intermediate states are avoided.

```python
class Cart:
    def __init__(self) -> None:
        self._items: list[str] = []

    def add(self, item_id: str) -> None:
        if not item_id.strip():
            raise ValueError('Item ID cannot be empty')
        self._items.append(item_id)

    @property
    def items(self) -> tuple[str, ...]:
        return tuple(self._items)
```

Returning a tuple prevents callers from modifying the internal list through
the returned value.

### 1.4 Abstraction and contracts

Abstraction exposes what a collaborator can do while hiding how it does it. A
good contract is narrow, behavior-oriented, and stable enough for clients to
depend on.

Python provides three common choices:

| Choice | Strength | Prefer when |
|---|---|---|
| Duck typing | Minimal ceremony | The collaboration is local and obvious |
| `ABC` | Explicit nominal contract and incomplete-class prevention | Implementations should deliberately join a hierarchy |
| `Protocol` | Structural contract checked by type tools | Existing or external classes should conform without inheriting |

#### Abstract base class

```python
from abc import ABC, abstractmethod
from decimal import Decimal


class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, reference_id: str, amount: Decimal) -> str:
        raise NotImplementedError
```

An `ABC` communicates an explicit family and prevents direct instantiation
until abstract methods are implemented. It does not runtime-check that an
override's type signature is compatible. Keep the interface focused; clients
should not be forced to depend on unrelated operations.

#### Structural protocol

```python
from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now()
```

`SystemClock` satisfies the protocol structurally without inheriting from it.
Type annotations do not enforce the protocol at runtime unless additional
runtime checking is explicitly requested. `@runtime_checkable` enables limited
presence-based `isinstance` and `issubclass` checks; it does not validate full
method signatures or annotations.

Use the least powerful mechanism that makes the contract clear. Do not create
an abstraction for every class when no alternative implementation, testing
boundary, or dependency direction requires one.

### 1.5 Inheritance and polymorphism

Inheritance expresses a genuine substitutable **is-a** relationship. It is not
merely a shortcut for copying methods from another class.

```python
class PricingPolicy(ABC):
    @abstractmethod
    def fee(self, parked_minutes: int) -> Decimal:
        raise NotImplementedError


class HourlyPricing(PricingPolicy):
    def fee(self, parked_minutes: int) -> Decimal:
        hours = max(1, (parked_minutes + 59) // 60)
        return Decimal(hours * 20)


class FlatPricing(PricingPolicy):
    def fee(self, parked_minutes: int) -> Decimal:
        return Decimal('100')


def quote(policy: PricingPolicy, parked_minutes: int) -> Decimal:
    return policy.fee(parked_minutes)
```

Polymorphism lets `quote` call one contract while the runtime object supplies
the behavior. Client code should not branch on concrete types:

```python
# Avoid this when the types already share a meaningful contract.
if isinstance(policy, HourlyPricing):
    ...
elif isinstance(policy, FlatPricing):
    ...
```

A useful hierarchy is substitutable: client code can use any subtype through
the base contract without needing concrete-type knowledge or receiving a
different fundamental promise. Topic 5 will cover the formal substitution
principle and its precondition/postcondition reasoning.

Know that Python uses a method resolution order and supports multiple
inheritance. For interview designs, prefer shallow hierarchies. Use mixins only
for narrow, orthogonal behavior and avoid complicated inheritance graphs.

When a base class owns required initialization, call it cooperatively with
`super()`:

```python
class Account:
    def __init__(self, account_id: str) -> None:
        if not account_id.strip():
            raise ValueError('Account ID cannot be empty')
        self._account_id = account_id

    @property
    def account_id(self) -> str:
        return self._account_id


class Member(Account):
    def __init__(self, account_id: str, borrowing_limit: int) -> None:
        super().__init__(account_id)
        if borrowing_limit <= 0:
            raise ValueError('Borrowing limit must be positive')
        self.borrowing_limit = borrowing_limit
```

`super()` follows the method resolution order, which matters if cooperative
multiple inheritance is ever used. It does not simply mean direct parent.

### 1.6 Composition and dependency injection

Composition builds behavior by giving an object collaborators and delegating
work to them. It expresses **has-a** or **uses-a** relationships.

Here, **object composition** means assembling behavior from collaborators. In
strict UML relationship terminology, a retained collaborator may instead be an
association or aggregation if the receiving object does not own its lifecycle.
The distinction is made explicit in the next section.

```python
class CheckoutService:
    def __init__(
        self,
        payment_gateway: PaymentGateway,
        clock: Clock,
    ) -> None:
        self._payment_gateway = payment_gateway
        self._clock = clock

    def checkout(self, booking_id: str, amount: Decimal) -> str:
        requested_at = self._clock.now()
        payment_id = self._payment_gateway.charge(booking_id, amount)
        return f'{payment_id}@{requested_at.isoformat()}'
```

The service receives its dependencies instead of constructing a concrete
gateway or reading the system clock directly. This is constructor injection.

Use method injection when a dependency is required only for one operation and
does not belong to the object's ongoing state. Use a composition root such as
`main.py` to construct concrete objects and wire them together.

#### Composition versus inheritance

| Question | Inheritance | Composition |
|---|---|---|
| Relationship | Is-a | Has-a or uses-a |
| Binding | Coupled to the base contract; may also reuse implementation | Delegates through a collaborator contract |
| Variation | Override a related behavior | Swap or combine independent behaviors |
| Runtime replacement | Awkward | Natural |
| Typical risk | Fragile or deep hierarchy | Too many tiny abstractions |

Prefer composition when requirements introduce independent axes of variation,
such as pricing plus discounting plus notification. Inheritance remains useful
when subtypes genuinely fulfill the same semantic contract.

### 1.7 Object relationships and ownership

Python represents these relationships with ordinary references, but their
domain meanings differ.

| Relationship | Meaning | Lifecycle example |
|---|---|---|
| Dependency | An object temporarily uses another | A service receives a validator for one call |
| Association | An object retains a reference without owning it | A booking refers to a customer |
| Aggregation | A whole groups parts that can exist independently | A team contains existing members |
| Composition | A whole owns parts as part of its lifecycle | An order owns its order lines |
| Inheritance | A subtype fulfills the same semantic contract | Hourly pricing is a pricing policy |

The garbage collector does not decide whether a relationship is aggregation or
composition. Ownership comes from domain lifecycle rules:

- Who creates the part?
- Can the part exist independently?
- May another object share it?
- Who is allowed to mutate it?
- What happens to it when the whole is removed?

Also identify basic cardinality: one-to-one, one-to-many, and many-to-many.
Detailed relationship modeling and aggregate boundaries belong to Topic 3.

Avoid storing the same mutable fact in both directions unless one operation
updates both consistently. A duplicated source of truth eventually disagrees.

### 1.8 Dataclasses, enums, and object roles

#### Regular class versus dataclass

Use a regular class when custom construction, behavior, hidden state, or
carefully controlled equality dominates. Use a dataclass when the class is
primarily a declared group of fields and generated initialization,
representation, or equality is correct for its semantics.

```python
from dataclasses import dataclass, field


@dataclass
class Group:
    group_id: str
    member_ids: set[str] = field(default_factory=set)
```

`default_factory` creates a new set for every instance. Never write
`member_ids: set[str] = set()` as a dataclass or function default.
This minimal snippet demonstrates default creation only; its public mutable set
is not the encapsulation model to copy for a rule-bearing domain object.

Useful dataclass options include:

- `frozen=True`: blocks ordinary field assignment.
- `eq=False`: disables generated field-wise equality.
- `order=True`: generates ordering; use only when domain ordering is real.
- `slots=True`: removes the normal instance dictionary and can reduce accidental
  attributes and memory use.
- `repr=False` on a field: omits sensitive or noisy data from generated output.

`frozen=True` is shallow. A frozen object containing a list still exposes a
mutable list.

```python
@dataclass(frozen=True)
class UnsafeSnapshot:
    values: list[int]


snapshot = UnsafeSnapshot([1])
snapshot.values.append(2)  # allowed: the nested list is still mutable
```

Use immutable nested values such as tuples when effective immutability matters.

#### Enums

An `Enum` represents a closed set of meaningful domain values.

```python
from enum import Enum


class TicketStatus(Enum):
    ACTIVE = 'active'
    PAID = 'paid'
    CANCELLED = 'cancelled'
```

Using enums in contracts makes the closed set explicit and invalid categories
harder to express. Type hints still do not reject a wrong runtime value by
themselves. An enum alone also does not enforce which state transitions are
legal.

#### Identity-bearing objects and value-like objects

Topic 3 will model these roles in depth. For Python mechanics, remember:

| Role | Equality intuition | Typical mutability |
|---|---|---|
| Identity-bearing object | Same stable identity even if attributes change | Often mutable |
| Value-like object | Equal when all meaningful values are equal | Prefer immutable |
| Stateless collaborator | Equality is usually irrelevant | Prefer stateless |

A dataclass is not automatically a value object, and a value object does not
have to be a dataclass.

### 1.9 Equality, hashing, and immutability

Equality and hashing form a contract:

```text
if a == b, then hash(a) must equal hash(b)
```

The reverse is not required because different objects may collide. Any state
used to calculate a hash must remain stable while the object is stored in a set
or used as a dictionary key.

An immutable identifier is a safe value-key example:

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BookId:
    isbn: str

    def __post_init__(self) -> None:
        normalized = self.isbn.replace('-', '')
        if len(normalized) not in (10, 13) or not normalized.isdigit():
            raise ValueError('ISBN must contain 10 or 13 digits')
        object.__setattr__(self, 'isbn', normalized)
```

The generated `__eq__` and `__hash__` use the normalized immutable field.
This intentionally simplified example accepts numeric 10- or 13-digit IDs;
production ISBN validation would also implement its checksum and the ISBN-10
`X` case.

An entity-like object usually compares by a stable ID, not by every mutable
attribute:

```python
class BookCopy:
    def __init__(self, copy_id: str, book_id: BookId, shelf: str) -> None:
        if not copy_id.strip():
            raise ValueError('Copy ID cannot be empty')
        self._copy_id = copy_id
        self.book_id = book_id
        self.shelf = shelf

    @property
    def copy_id(self) -> str:
        return self._copy_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BookCopy):
            return NotImplemented
        return self.copy_id == other.copy_id

    __hash__ = None
```

This mutable entity is deliberately unhashable. If domain code truly requires
hashable entities, hash only immutable identity and guarantee that the identity
never changes.

Important distinctions:

- `NotImplemented` is a special return value used by binary operations to let
  Python try another implementation.
- `NotImplementedError` is an exception commonly raised by deliberately
  incomplete methods.
- Dataclass equality normally compares the same concrete class field by field.
  That is often wrong for identity-bearing entities.
- Not every immutable object is hashable; every component contributing to the
  hash must also be hashable.

### 1.10 Type hints, collection contracts, and basic generics

Type hints communicate contracts to readers and static-analysis tools.

```python
from collections.abc import Callable, Iterable, Mapping, Sequence


def total_seats(rows: Sequence[int]) -> int:
    return sum(rows)


def enabled_features(config: Mapping[str, bool]) -> set[str]:
    return {name for name, enabled in config.items() if enabled}


def send_all(recipients: Iterable[str], send: Callable[[str], None]) -> None:
    for recipient in recipients:
        send(recipient)
```

Accept the least-specific contract the implementation needs:

- `Iterable[T]` when one pass is enough.
- `Collection[T]` when size and membership are needed.
- `Sequence[T]` when ordered indexed access is needed.
- `Mapping[K, V]` when read-only key lookup is needed.
- Concrete `list`, `dict`, `set`, or `deque` when their mutation or exact
  operations are part of the contract.

Use `T | None` when absence is meaningful. `Optional[T]` means the same as
`T | None`; it does not mean a function parameter has a default value.

`Mapping` is non-mutating from the consumer's interface; it does not guarantee
that the underlying object is immutable or cannot change elsewhere.

#### A basic generic contract

```python
from typing import Generic, Protocol, TypeVar


T = TypeVar('T')


class Lookup(Protocol, Generic[T]):
    def get(self, item_id: str) -> T | None:
        ...


class InMemoryLookup(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def add(self, item_id: str, item: T) -> None:
        self._items[item_id] = item

    def get(self, item_id: str) -> T | None:
        return self._items.get(item_id)
```

Generics preserve type information without duplicating the same container for
every domain type. Advanced variance rules are not required at this stage.

Type annotations are not runtime validation. `typing.cast()` also performs no
conversion or validation; it only informs a type checker. Validate untrusted
input at runtime.

Avoid exposing mutable collection internals. Depending on the contract, return
a tuple, iterator, read-only abstraction, or defensive copy.

### 1.11 Invariants and exception mechanics

Validate all inputs and required state before performing a multi-field
mutation.

```python
class AccountError(Exception):
    pass


class InsufficientFundsError(AccountError):
    pass


class BankAccount:
    def __init__(self, account_id: str, opening_balance_cents: int = 0) -> None:
        if not account_id.strip():
            raise ValueError('Account ID cannot be empty')
        if opening_balance_cents < 0:
            raise ValueError('Opening balance cannot be negative')
        self._account_id = account_id
        self._balance_cents = opening_balance_cents
        self._transactions: list[int] = []

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def balance_cents(self) -> int:
        return self._balance_cents

    @property
    def transactions(self) -> tuple[int, ...]:
        return tuple(self._transactions)

    def deposit(self, cents: int) -> None:
        if cents <= 0:
            raise ValueError('Deposit must be positive')
        self._balance_cents += cents
        self._transactions.append(cents)

    def withdraw(self, cents: int) -> None:
        if cents <= 0:
            raise ValueError('Withdrawal must be positive')
        if cents > self._balance_cents:
            raise InsufficientFundsError('Insufficient funds')
        self._balance_cents -= cents
        self._transactions.append(-cents)
```

The withdrawal checks every precondition before changing balance or history.

Exception guidelines for this topic:

- Use a standard exception such as `ValueError` for simple invalid arguments.
- Introduce a small custom exception when callers need to distinguish a domain
  failure and recover meaningfully.
- Raise at the layer that understands why the condition is invalid.
- Catch at a layer capable of recovery, translation, cleanup, or compensation.
- Preserve a lower-level cause with `raise DomainError(...) from error`.
- Avoid broad `except Exception`, silent failure, and ambiguous `None` unless
  absence is an explicit part of the contract.

Detailed error taxonomies and result objects belong to Topic 10.

### 1.12 Modules and dependency direction

A small LLD solution might use this structure:

```text
problem/
|-- main.py              # composition root and demonstration
|-- models/              # state and domain behavior
|-- services/            # use-case coordination
|-- contracts/           # stable collaborator interfaces when useful
|-- adapters/            # concrete external integrations
`-- tests/               # executable requirements
```

This is a guide, not a rule that every class needs its own file. Prefer cohesive
modules and a clear dependency direction over folder ceremony.

Practical rules:

- Keep module-level mutable state out of business logic.
- Construct concrete dependencies in `main.py` or another composition root.
- Inject clocks, gateways, ID generators, and other nondeterministic services.
- Avoid circular imports by clarifying ownership and dependency direction.
- Use a quoted annotation or `from __future__ import annotations` for self and
  later-defined references in Python 3.10.
- Use `if TYPE_CHECKING:` for genuinely type-only imports when needed; first
  question whether an import cycle reflects tangled ownership.
- Export a small intentional public API.
- Keep business behavior testable without starting infrastructure.

## 2. Recognize

Use prompt and code signals to select the relevant OOP mechanism.

| Signal | Mechanism to consider |
|---|---|
| State must never become inconsistent | Encapsulated behavior and validation |
| Several implementations perform the same role | Polymorphic contract |
| External service or nondeterministic clock | Injected dependency |
| Behavior varies independently of object identity | Composed collaborator |
| Stable is-a relationship with one semantic promise | Inheritance |
| Object is defined entirely by its values | Immutable value semantics |
| Object changes but remains the same conceptual thing | Stable identity semantics |
| Caller needs only iteration or lookup | Abstract collection input contract |
| Returned collection must not be changed externally | Tuple, view, iterator, or copy |
| Closed set of categories or states | `Enum` |
| Construction needs a meaningful variant | Named classmethod constructor |
| Caller must recover differently from one failure | Specific exception type |

### Warning signals in code

- A mutable list, dictionary, or set declared on the class.
- A mutable function or dataclass default.
- `is` used for string or numeric value comparison.
- Public code changing several fields that represent one invariant.
- Methods returning internal mutable collections directly.
- Client code branching on every concrete subtype.
- A domain service constructing a concrete gateway internally.
- A deep inheritance tree created only for method reuse.
- A frozen dataclass containing mutable nested collections.
- A mutable object used as a dictionary key.
- Broad exception handling that converts every failure to `None`.
- Type annotations treated as runtime validation.

### Decision questions

Before adding a class, base class, or interface, ask:

1. What state or behavior does this object own?
2. Which invariant does its public API protect?
3. Is this relationship really is-a, or is it has-a/uses-a?
4. Must implementations inherit, or is structural compatibility enough?
5. Does this object have identity or value equality?
6. Can callers mutate state through an exposed reference?
7. Is an abstraction justified by variation, dependency direction, or testing?
8. Can the object be constructed in an invalid state?
9. Can failure occur after partial mutation?
10. Where are concrete dependencies created?

## 3. Model

This topic models object mechanics from an already supplied specification. It
does not repeat the discovery process from Topic 1.

### 3.1 Small parking-domain classification

Given the bounded Parking Lot requirements, classify candidate objects before
coding:

| Candidate | Primary semantics | State/contract decision |
|---|---|---|
| Vehicle identifier | Value-like | Immutable and structurally equal |
| Parking spot | Identity-bearing | Owns occupancy state and guards assign/vacate |
| Ticket | Identity-bearing | Changes over a parking session |
| Pricing collaborator | Behavioral contract | Multiple implementations calculate a fee |
| Payment gateway | External contract | Injected and replaceable with a fake |
| Parking service | Coordinator | Composes collaborators for entry and exit |

This is not yet a final domain model. It is enough to decide which Python
mechanics are appropriate.

### 3.2 Relationship sketch

```text
ParkingService
  uses -> PricingPolicy
  uses -> PaymentGateway
  coordinates -> ParkingSpot and Ticket

ParkingSpot
  retains -> current Vehicle or no vehicle

Ticket
  refers to -> Vehicle identifier and ParkingSpot identifier
```

Questions to resolve before implementation:

- Does a ticket retain entire objects or stable identifiers?
- Which object alone may change spot occupancy?
- Is pricing stateless and shareable?
- Does the service own the gateway lifecycle or merely collaborate with it?
- Which collections can callers inspect, and in what form?

### 3.3 Contract sketch

```python
class PricingPolicy(Protocol):
    def fee(self, entry_time: datetime, exit_time: datetime) -> Decimal:
        ...


class PaymentGateway(Protocol):
    def charge(self, ticket_id: str, amount: Decimal) -> str:
        ...
```

The names communicate behavior. The contracts do not expose database tables,
HTTP libraries, or concrete payment-provider details.

### 3.4 Ownership review

For each mutable fact, choose exactly one owner:

| Mutable fact | Proposed owner |
|---|---|
| Current vehicle in a spot | Parking spot |
| Ticket lifecycle state | Ticket |
| Active-ticket index | Parking service or later repository boundary |
| Gateway connection details | Concrete adapter, outside domain objects |

The single-owner decision prevents two public fields or collections from
becoming competing sources of truth.

## 4. Implement

The following small examples isolate the Python/OOP mechanics. They are not
intended to be full interview case studies.

### 4.1 Immutable identity records held by a mutable object

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, eq=False)
class Track:
    track_id: str
    title: str
    duration_seconds: int

    def __post_init__(self) -> None:
        if not self.track_id.strip() or not self.title.strip():
            raise ValueError('Track ID and title are required')
        if self.duration_seconds <= 0:
            raise ValueError('Duration must be positive')

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        return self.track_id == other.track_id

    def __hash__(self) -> int:
        return hash(self.track_id)


class Playlist:
    def __init__(self, playlist_id: str) -> None:
        if not playlist_id.strip():
            raise ValueError('Playlist ID cannot be empty')
        self.playlist_id = playlist_id
        self._tracks: list[Track] = []

    @property
    def tracks(self) -> tuple[Track, ...]:
        return tuple(self._tracks)

    @property
    def total_duration_seconds(self) -> int:
        return sum(track.duration_seconds for track in self._tracks)

    def add(self, track: Track) -> None:
        if any(existing.track_id == track.track_id for existing in self._tracks):
            raise ValueError(f'Track {track.track_id!r} is already present')
        self._tracks.append(track)

    def remove(self, track_id: str) -> Track:
        for index, track in enumerate(self._tracks):
            if track.track_id == track_id:
                return self._tracks.pop(index)
        raise KeyError(f'Track {track_id!r} is not present')
```

This example demonstrates:

- Immutable track records with stable ID-based equality and hashing.
- Independent instance-owned mutable state.
- Validation at construction and mutation boundaries.
- Aggregation and delegation rather than subclassing.
- Read-only collection exposure.
- Intention-revealing behavior instead of a public list.

### 4.2 Overriding and dynamic dispatch

```python
from abc import ABC, abstractmethod
from collections.abc import Iterable
from math import isfinite, pi


class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        raise NotImplementedError


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        if not isfinite(radius) or radius <= 0:
            raise ValueError('Radius must be positive')
        self._radius = radius

    def area(self) -> float:
        return pi * self._radius ** 2


class Rectangle(Shape):
    def __init__(self, width: float, height: float) -> None:
        if (
            not isfinite(width)
            or not isfinite(height)
            or width <= 0
            or height <= 0
        ):
            raise ValueError('Dimensions must be positive')
        self._width = width
        self._height = height

    def area(self) -> float:
        return self._width * self._height


def total_area(shapes: Iterable[Shape]) -> float:
    return sum((shape.area() for shape in shapes), 0.0)
```

`total_area` depends on one promise and uses dynamic dispatch. It does not need
type checks for `Circle` or `Rectangle`.

### 4.3 Structural contracts and testable dependencies

```python
from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        ...


class Notifier(Protocol):
    def send(self, recipient: str, message: str) -> None:
        ...


class ExpiryNotifier:
    def __init__(self, clock: Clock, notifier: Notifier) -> None:
        self._clock = clock
        self._notifier = notifier

    def notify_if_expired(self, recipient: str, expires_at: datetime) -> bool:
        if not recipient.strip():
            raise ValueError('Recipient cannot be empty')
        if expires_at > self._clock.now():
            return False
        self._notifier.send(recipient, f'Expired at {expires_at.isoformat()}')
        return True
```

A test fake only needs the required behavior:

```python
class FixedClock:
    def __init__(self, current: datetime) -> None:
        self._current = current

    def now(self) -> datetime:
        return self._current


class RecordingNotifier:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def send(self, recipient: str, message: str) -> None:
        self.messages.append((recipient, message))
```

The service can be tested without sleeping or contacting a real provider.
Dependency-inversion reasoning and detailed test-double taxonomy come later;
the foundation here is explicit replaceable collaboration.

### 4.4 Validate, then mutate

For an operation that changes several facts:

```text
1. Validate input shape.
2. Validate current object state.
3. Ask required collaborators for a result.
4. Apply the state change as one conceptual operation.
5. Publish or return the outcome.
```

If step 3 can cause external side effects, later topics will discuss
transactions, idempotency, compensation, and concurrency. At this stage, never
mutate half the local state before checking all locally knowable rules.

## 5. Test

Tests should prove object semantics, not only method outputs.

### 5.1 Instance isolation

```python
import unittest


class PlaylistIsolationTest(unittest.TestCase):
    def test_playlists_do_not_share_tracks(self) -> None:
        first = Playlist('P1')
        second = Playlist('P2')
        first.add(Track('T1', 'First', 120))

        self.assertEqual(1, len(first.tracks))
        self.assertEqual((), second.tracks)
```

This catches shared class attributes and shared mutable defaults.

### 5.2 Encapsulation and invariant preservation

```python
import unittest


class PlaylistInvariantTest(unittest.TestCase):
    def test_returned_tracks_cannot_mutate_playlist(self) -> None:
        playlist = Playlist('P1')
        playlist.add(Track('T1', 'First', 120))

        returned = playlist.tracks

        self.assertIsInstance(returned, tuple)
        self.assertEqual(1, len(playlist.tracks))

    def test_duplicate_track_is_rejected_without_mutation(self) -> None:
        playlist = Playlist('P1')
        track = Track('T1', 'First', 120)
        playlist.add(track)

        with self.assertRaises(ValueError):
            playlist.add(track)

        self.assertEqual((track,), playlist.tracks)
```

The failure test also verifies that state remains unchanged.

### 5.3 Equality and hashing

```python
import unittest


class BookIdTest(unittest.TestCase):
    def test_equal_values_have_equal_hashes(self) -> None:
        first = BookId('978-0132350884')
        second = BookId('9780132350884')

        self.assertIsNot(first, second)
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertEqual(1, len({first, second}))

    def test_mutable_entity_is_unhashable(self) -> None:
        copy = BookCopy('COPY-1', BookId('9780132350884'), 'A-1')

        with self.assertRaises(TypeError):
            hash(copy)
```

### 5.4 Polymorphism

```python
import unittest
from math import pi


class ShapeTest(unittest.TestCase):
    def test_total_area_uses_each_shape_implementation(self) -> None:
        shapes: list[Shape] = [Rectangle(2, 3), Circle(1)]

        self.assertAlmostEqual(6 + pi, total_area(shapes))
```

The consumer test should remain unchanged when another valid subtype is added.

### 5.5 Injected fake

```python
import unittest
from datetime import datetime, timedelta


class ExpiryNotifierTest(unittest.TestCase):
    def test_future_expiry_does_not_notify(self) -> None:
        now = datetime(2026, 1, 1, 9, 0)
        notifier = RecordingNotifier()
        service = ExpiryNotifier(FixedClock(now), notifier)

        sent = service.notify_if_expired('user-1', now + timedelta(hours=1))

        self.assertFalse(sent)
        self.assertEqual([], notifier.messages)

    def test_expiry_equal_to_now_notifies(self) -> None:
        now = datetime(2026, 1, 1, 9, 0)
        notifier = RecordingNotifier()
        service = ExpiryNotifier(FixedClock(now), notifier)

        sent = service.notify_if_expired('user-1', now)

        self.assertTrue(sent)
        self.assertEqual(
            [('user-1', 'Expired at 2026-01-01T09:00:00')],
            notifier.messages,
        )
```

### Object-foundation test checklist

- Every instance owns independent mutable state.
- Constructors reject invalid required values.
- Public methods preserve invariants.
- Failed operations do not partially mutate state.
- Returned collections cannot mutate internals accidentally.
- Equal value objects have equal hashes.
- Mutable identity-bearing objects are not unsafe hash keys.
- Subtypes can be consumed through their common contract.
- Fakes can replace nondeterministic or external dependencies.
- Tests do not reach into internal attributes unless intentionally documenting
  a trade-off.

## 6. Adapt

### Adaptation A: add a triangle

Requirement: support triangles in `total_area`.

```python
class Triangle(Shape):
    def __init__(self, base: float, height: float) -> None:
        if (
            not isfinite(base)
            or not isfinite(height)
            or base <= 0
            or height <= 0
        ):
            raise ValueError('Dimensions must be positive')
        self._base = base
        self._height = height

    def area(self) -> float:
        return self._base * self._height / 2
```

`total_area` must not change. If it contains type branches, the original
polymorphic boundary was not working.

### Adaptation B: add an SMS notifier

Create an `SmsNotifier` with the same `send` behavior. `ExpiryNotifier` should
not change because it depends on the narrow notifier contract.

### Adaptation C: expose playlist ordering safely

Add `move(track_id, new_index)` without returning the internal list. Keep
duplicate, missing-track, and index rules inside `Playlist`, then prove that a
failed move preserves the old order.

### Adaptation D: optional preview of independent pricing modifiers

Suppose base price, weekend surcharge, and customer discount can change
independently. A subclass for every combination grows rapidly. Recognize that
independent behavior should be composed. The exact structural pattern will be
covered later. This preview is not part of the Topic 2 mastery score.

### Adaptation review

For every change, ask:

1. Did the public contract need to change?
2. Did the owner of the invariant remain clear?
3. Could a new collaborator satisfy an existing contract?
4. Did any caller start branching on concrete types?
5. Did the change expose internal mutable state?
6. Do old tests still pass unchanged?

## Common mistakes

### Shared mutable class attributes

```python
class Cart:
    items = []
```

All instances share one list. Put mutable instance state in `__init__` or use a
dataclass `default_factory`.

### Mutable default arguments

```python
def __init__(self, items: list[str] = []):
    self.items = items
```

Function defaults are evaluated once when the function is defined. Use `None`
and create a new collection inside, or use `default_factory` for a dataclass.

### Time evaluated too early

`created_at: datetime = datetime.now()` in a dataclass evaluates once at class
definition. Use `field(default_factory=datetime.now)`.

### Incorrect identity comparison

String or integer interning can make `a is b` appear to work. It is not a value
comparison guarantee. Use `==`. Use `is` for `None` and, deliberately, for
singleton enum members.

### Leaking internal collections

Returning a live list or dictionary lets callers bypass validation. Return an
appropriate immutable form, view, iterator, or copy.

### Assuming frozen means deeply immutable

`frozen=True` blocks assigning the field; it does not freeze a list stored in
that field.

### Field-wise equality for an entity

A default dataclass comparison may say that two snapshots of the same user are
different because an email changed, or that two different entities are equal
because all visible fields happen to match. Choose semantics intentionally.

### Mutating a hash key

Changing a field used in `__hash__` can make an object unreachable in its set or
dictionary bucket. Prefer immutable value keys.

### Inheritance for code reuse

An is-a relationship must be semantically substitutable. Reusing three methods
is not enough justification for a deep hierarchy.

### Calling overridable behavior during base initialization

A subclass override may run before the subclass state exists. Constructors
should establish their own state without relying on open-ended overridden
methods.

### Misunderstanding `super()`

`super()` follows Python's method resolution order; it does not simply mean
call my direct parent. Cooperative multiple inheritance requires compatible
method signatures and consistent `super()` use.

### Concrete dependencies hidden inside services

Constructing `StripeGateway()` or calling `datetime.now()` deep inside business
logic hides dependencies and makes tests nondeterministic.

### Abstracting everything

An ABC with exactly one implementation and no dependency-boundary purpose may
add ceremony without clarity. Abstractions need a reason.

### Type hints treated as validators

Python will still call an annotated function with a wrong runtime value unless
some code or framework validates it.

### Expensive properties

A property that makes a database or network request looks like cheap field
access and surprises callers. Use an explicit method.

### Partial mutation

Updating balance before checking a limit, or occupying a spot before verifying
compatibility, can leave an invalid object after failure. Validate first.

### Broad exception swallowing

Catching every exception and returning `None` hides programming defects and
removes the caller's ability to respond meaningfully.

### Circular object graphs and imports

Unnecessary bidirectional relationships create synchronization and import
problems. Prefer one ownership direction and IDs when a full object reference
is unnecessary.

### Anemic objects and a god coordinator

Do not make every model a public data bag while one service manually edits all
fields. Put rules with the state they protect. Responsibility modeling is
covered fully in Topic 3.

## Existing repository examples

### Strong examples

- [Location value-like model](../../solutions/food-delivery/models/location.py) uses a
  frozen dataclass, constructor-time coordinate validation, and generated value
  equality and hashing.
- [Expense](../../solutions/splitwise/models/expense.py) and
  [Split](../../solutions/splitwise/models/split.py) are frozen, and `Expense` stores its
  nested `Split` values in a tuple, avoiding a frozen shell around a mutable
  list.
- [Parking allocation contract](../../solutions/parking-lot/strategies/allocation.py) has an
  explicit ABC with two substitutable implementations.
- [Parking Lot service](../../solutions/parking-lot/services/parking_lot.py) receives its
  allocation, pricing, and payment collaborators through its constructor.
- [Hotel pricing contract](../../solutions/hotel-management/strategies/pricing_strategy.py),
  [standard pricing](../../solutions/hotel-management/strategies/standard_pricing_strategy.py),
  and [weekend pricing composition](../../solutions/hotel-management/strategies/weekend_pricing_decorator.py)
  demonstrate abstraction, overriding, polymorphism, and delegation.
- [Hotel clock contract](../../solutions/hotel-management/services/clock.py),
  [payment contract](../../solutions/hotel-management/services/payment_gateway.py), and
  [booking service](../../solutions/hotel-management/services/booking_service.py) demonstrate
  injected collaborators. Tests inject a mutable clock and the controllable
  in-memory payment gateway.
- [Split calculation contract](../../solutions/splitwise/strategies/split_strategy.py) accepts
  `Mapping` rather than unnecessarily requiring a concrete dictionary.
- [Money conversion boundary](../../solutions/atm/models/money.py) demonstrates a type alias,
  runtime conversion, narrow exception handling, and exception chaining.
- [Authentication error](../../solutions/atm/models/errors.py) carries domain-specific context;
  [ATM orchestration](../../solutions/atm/services/atm.py) conditionally clears the session
  when `end_session` is true and then re-raises the error.

### Examples to review critically

Real interview code contains trade-offs. Use these to practise design review:

- [Library member hierarchy](../../solutions/library-management/models/member.py) with
  [student](../../solutions/library-management/models/student_member.py) and
  [faculty](../../solutions/library-management/models/faculty_member.py) clearly demonstrates
  inheritance and overriding. Ask whether borrowing policy may vary
  independently and whether public mutable collections weaken encapsulation.
- [ATM Card](../../solutions/atm/models/card.py) demonstrates a named constructor, static
  helpers, and behavior beside state, but several mutable or sensitive fields
  remain public.
- [Cash Dispenser](../../solutions/atm/services/cash_dispenser.py) validates and defensively
  copies its initial inventory, but then exposes the inventory publicly.
- [Parking Spot](../../solutions/parking-lot/models/parking_spots.py) owns assignment and
  vacancy behavior, but its occupancy fields can still be edited directly.
- [Splitwise User](../../solutions/splitwise/models/user.py) is frozen and hashable, but
  generated equality compares every field even though a user is identity-like.

Do not label every existing implementation perfect. Explain which requirement
or interview-time trade-off justifies its simplicity and how production
boundaries might be stricter.

## Practice exercises

Exercises 1-7 are core. Exercises 5 and 6 also contain the timed adaptation
gates. Exercise 8 is an optional preview. Exercises 9 and 10 are fixed
recognition and modeling assessments.

### Exercise 1 - Core: Python object-semantics bug clinic

Use this fixed starter fixture:

```python
from typing import Protocol


class TitleProvider(Protocol):
    def load_title(self) -> str:
        ...


class BrokenPlaylist:
    tracks: list[str] = []

    def __init__(self, name: str, tags: list[str] = []) -> None:
        self.name = name
        self.tags = tags

    def add(self, track: str) -> None:
        self.tracks.append(track)

    def has_name(self, candidate: str) -> bool:
        return self.name is candidate

    def exposed_tracks(self) -> list[str]:
        return self.tracks


class PremiumPlaylist(BrokenPlaylist):
    def __init__(self, name: str) -> None:
        self.level = 'premium'


class MutableKey:
    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MutableKey) and self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


def load_title(provider: TitleProvider) -> str | None:
    try:
        return provider.load_title()
    except Exception:
        return None
```

Find, test, fix, and explain all seven defect categories:

1. Shared mutable class state.
2. Mutable default argument.
3. `is` used for value comparison.
4. Required base initialization skipped.
5. Live mutable collection exposed.
6. Mutable hash-participating state.
7. Broad exception swallowing.

The corrected design must give every playlist independent state, defensively
copy a caller-supplied tag collection, return a read-only track representation,
use stable equality semantics, and expose a defined provider failure rather
than hiding every exception. Include an aliasing test that mutates the caller's
original tag list after construction. Expose tags and tracks as tuples, and let
the provider's exception propagate instead of converting every failure to
`None`. Target time: 30 minutes. Score one point per defect only when the
explanation and regression test are both correct; pass at 7/7.

### Exercise 2 - Core: encapsulated BankAccount

Implement this exact contract using integer cents:

```text
BankAccount(account_id: str, opening_balance_cents: int = 0)
.account_id -> str                       # read-only
.balance_cents -> int                    # read-only
.transactions -> tuple[int, ...]         # read-only snapshot
.deposit(cents: int) -> None
.withdraw(cents: int) -> None
```

Rules:

- Empty account ID and negative opening balance raise `ValueError`.
- Deposit and withdrawal amounts must be positive or raise `ValueError`.
- Insufficient balance raises `InsufficientFundsError`.
- A deposit records positive cents; a withdrawal records negative cents.
- Every failed operation leaves balance and history unchanged.

Required tests: valid construction, invalid construction, deposit, withdrawal,
zero/negative amount, insufficient funds, protected history, and unchanged
state after failure. Target time: 25 minutes.

### Exercise 3 - Core: immutable DateRange

Implement this exact contract with `datetime.date` values:

```text
DateRange(start: date, end: date)         # frozen and hashable
.contains(value: date) -> bool
.overlaps(other: DateRange) -> bool
```

Use half-open intervals `[start, end)`. Require `start < end`; otherwise raise
`ValueError`. Two ranges that only touch at one boundary do not overlap.

Required tests: invalid range, equal values and hashes, start included, end
excluded, interior value, before/after value, overlap, containment, and touching
non-overlap. Target time: 20 minutes.

### Exercise 4 - Core: declared identity and value semantics

The semantics are supplied here; discovering them belongs to Topic 3.

- `ISBN` is immutable, structurally equal, and hashable after normalization.
- `BookCopy` has a stable `copy_id`, a mutable shelf, equality by `copy_id`, and
  is deliberately unhashable.
- Two copies may contain equal ISBN values but remain different entities.

Implement those semantics and tests for `is` versus `==`, equal ISBN hashes,
copy equality across shelf changes, two different copies of one ISBN, and
rejection of `BookCopy` as a set member. Target time: 20 minutes.

### Exercise 5 - Core and timed adaptation: polymorphic shapes

Implement:

```text
Shape(ABC).area() -> float
Circle(radius: float)
Rectangle(width: float, height: float)
total_area(shapes: Iterable[Shape]) -> float
```

Zero, negative, NaN, or infinite dimensions raise `ValueError`. `total_area`
must contain no `type()` or `isinstance()` branch. Compare floating results with
`assertAlmostEqual` or `math.isclose`.

Adaptation gate: add `Triangle(base, height)` in ten minutes without modifying
`total_area`; all previous tests must stay green.

### Exercise 6 - Core and timed adaptation: composition and collections

Implement:

```text
Track(track_id: str, title: str, duration_seconds: int)  # frozen
Playlist(playlist_id: str)
.tracks -> tuple[Track, ...]
.total_duration_seconds -> int
.add(track: Track) -> None
.remove(track_id: str) -> Track
```

Rules:

- IDs and title are non-empty; duration is positive.
- Tracks compare and hash by immutable `track_id`.
- Track IDs are unique inside one playlist.
- Duplicate add raises `ValueError` without changing order.
- Missing removal raises `KeyError` without changing order.
- Separate playlists never share their collections.

Adaptation gate: add `move(track_id: str, new_index: int) -> None` in fifteen
minutes. Missing track raises `KeyError`; an index outside
`0 <= new_index < len(tracks)` raises `IndexError`; failure preserves the old
order. Existing tests must remain unchanged and green.

### Exercise 7 - Core: injected Clock and Notifier

Implement these structural contracts and service:

```text
Clock.now() -> datetime
Notifier.send(recipient: str, message: str) -> None
ExpiryNotifier(clock: Clock, notifier: Notifier)
.notify_if_expired(recipient: str, expires_at: datetime) -> bool
```

If `expires_at > clock.now()`, return `False` and send nothing. Otherwise send
exactly `Expired at <ISO timestamp>` and return `True`. Empty recipient raises
`ValueError` before the notifier is called.

For this foundation exercise, use naive `datetime` values interpreted in one
agreed timezone. Timezone-aware domain modeling is covered in a later reusable
building-blocks topic.

Use `FixedClock` and `RecordingNotifier` fakes. Required tests: future, equal to
now, past, empty recipient, exact message, and no real clock or network use.
Target time: 25 minutes.

### Exercise 8 - Optional preview: inheritance-to-composition review

Take the library member hierarchy in this repository. Write two short designs:

1. Keep inheritance because member subtype owns stable borrowing rules.
2. Compose a replaceable borrowing policy because those rules change
   independently.

Compare change impact without naming a GoF pattern. This previews Topics 3 and
5 and is not part of the Topic 2 mastery score.

### Exercise 9 - Recognition gate: fixed ten-case audit

For each case, name the defect or mechanism and the corrective direction. Score
one point only when both parts are correct.

| Case | Code or situation |
|---:|---|
| 1 | `class Bag: items = []` |
| 2 | `def add(item, items=[]): ...` |
| 3 | `status is 'paid'` |
| 4 | A frozen dataclass contains `values: list[int]` |
| 5 | `return self._orders` exposes a list |
| 6 | A mutable dataclass uses generated field-wise equality as a user entity |
| 7 | `CheckoutService.__init__` constructs `RealPaymentGateway()` internally |
| 8 | A consumer branches with `isinstance` for every pricing implementation |
| 9 | `raw_id = cast(int, request.value)` is treated as conversion |
| 10 | A function requires `list[int]` but only iterates once |

<details>
<summary>Recognition key</summary>

1. Shared class state; create instance state.
2. Reused mutable default; use `None` or `default_factory` as applicable.
3. Incorrect identity comparison; use `==` for string value.
4. Frozen is shallow; store an immutable nested representation such as a tuple,
   or keep private mutable storage and expose only protected snapshots.
5. Collection leak; return an immutable form, view, iterator, or copy.
6. Equality may not match identity; define stable identity semantics and avoid
   unsafe hashing.
7. Hidden concrete dependency; inject a narrow collaborator.
8. Missing useful polymorphic boundary; call shared behavior through a contract.
9. `cast` performs no runtime conversion; parse and validate the value.
10. Over-specific input; accept `Iterable[int]`.

</details>

Pass threshold: 8/10, with cases 1-5 all correct.

### Exercise 10 - Modeling gate: supplied object semantics

Given this fixed specification:

- `ProductCode` is an immutable value used as a dictionary key.
- `InventoryItem` has stable identity and owns mutable available quantity.
- `PriceRule` is replaceable behavior with no identity or mutable state.
- `PaymentGateway` is external and must be faked in tests.
- `CheckoutService` coordinates a price rule, inventory items, and gateway.

Produce a table with each candidate's Python representation, equality/hash
choice, mutability, and relationship to `CheckoutService`. Then name the sole
owner of product-code normalization, available quantity, price calculation,
payment execution, and checkout sequencing.

<details>
<summary>Modeling key</summary>

| Candidate | Expected mechanics |
|---|---|
| ProductCode | Frozen value-like class; structural equality and stable hash |
| InventoryItem | Mutable identity-bearing class; equality by stable ID; unhashable by default |
| PriceRule | Narrow `Protocol` or `ABC`; stateless implementation |
| PaymentGateway | Injected narrow `Protocol` or `ABC`; fake permitted |
| CheckoutService | Mutable or stateless coordinator composed with the two contracts |

| Mutable fact or behavior | Sole owner |
|---|---|
| Product-code normalization | ProductCode |
| Available quantity | InventoryItem |
| Price calculation | PriceRule implementation |
| Payment execution | PaymentGateway implementation |
| Checkout sequencing | CheckoutService |

</details>

Score one point for each correct candidate classification and one for each sole
owner. Pass threshold: 8/10, with ProductCode and InventoryItem mechanics both
correct.

## Interview self-check

Answer these without notes:

1. What does it mean that Python names are bound to objects?
2. How do mutation and reassignment differ?
3. When should `is` be used instead of `==`?
4. Why is a mutable class attribute dangerous?
5. Why are mutable function defaults reused?
6. What does `__init__` do, and what does it not do?
7. When is a classmethod better than another constructor flag?
8. When should a property remain a method instead?
9. What do one and two leading underscores mean in Python?
10. Why is encapsulation more than getters and setters?
11. How do abstraction and an abstract base class differ?
12. When would you choose `ABC` over `Protocol`?
13. Does polymorphism require inheritance?
14. What makes inheritance substitutable?
15. Why is composition useful for independent variations?
16. How do aggregation and composition differ if both use references?
17. What does `frozen=True` guarantee, and what does it not guarantee?
18. Why might generated dataclass equality be wrong for an entity?
19. What is the equality/hash contract?
20. When is an object unsafe as a dictionary key?
21. Why accept `Sequence` or `Mapping` instead of a concrete collection?
22. What does `T | None` mean?
23. Do type hints validate runtime input?
24. What is the difference between `NotImplemented` and `NotImplementedError`?
25. Why should validation usually occur before mutation?
26. Where should concrete gateways and clocks be constructed?
27. Why can returning an internal list break invariants?
28. Why does Python not support Java-style signature overloading?
29. What does an `Enum` guarantee, and what must code still validate?

Score one point when an answer contains the minimum idea below. Core questions
are 1-5, 10, 13-20, 25, 27, and 29; all core answers must be correct.

<details>
<summary>Self-check scoring key</summary>

1. Names hold references to objects; two names may refer to the same object.
2. Mutation changes the referenced object; reassignment changes one name's
   binding.
3. Use `is` for identity such as `None` or a deliberate singleton enum; use
   `==` for ordinary value comparison.
4. A mutable class attribute may be shared by every instance.
5. Function defaults are evaluated once at function definition.
6. `__new__` creates the instance; `__init__` initializes that existing
   instance.
7. A classmethod can give a construction variant a clear name and may construct
   the receiving subclass through `cls`.
8. Expensive work, I/O, or meaningful side effects should use an explicit
   method rather than field-like property syntax.
9. `_name` is an internal-use convention; `__name` is name mangling, not
   security.
10. Encapsulation owns state changes and preserves invariants while hiding
    representation; getters and setters alone do not achieve that.
11. Abstraction is the concept of exposing essential behavior; an ABC is one
    nominal Python mechanism for expressing it.
12. Use an ABC for explicit nominal membership and incomplete-subclass
    prevention; use a Protocol for structural compatibility without inheritance.
13. No. Duck typing and Protocols also support polymorphism.
14. A subtype honors the base contract's valid inputs and promised outcomes so
    clients need no concrete-type knowledge.
15. Composition lets independent behaviors be replaced or combined without a
    subclass for every combination.
16. Both use references; composition implies lifecycle ownership, whereas an
    aggregated part can exist independently.
17. Frozen blocks ordinary field assignment but does not recursively freeze
    nested mutable objects.
18. Generated equality compares fields, which may conflict with stable entity
    identity across attribute changes.
19. Equal hashable objects must have equal hashes, and hash-participating state
    must remain stable.
20. An object is unsafe when equality/hash-relevant state can change while it is
    stored as a key or set member.
21. The narrowest required abstraction admits more valid callers and avoids
    promising mutation or indexing that is not needed.
22. The value may be `T` or `None`; it says nothing about a default argument.
23. No. Hints guide people and tools; runtime boundaries still require
    validation.
24. `NotImplemented` is a binary-operation return sentinel;
    `NotImplementedError` is an exception.
25. Validation first prevents failure from leaving partial or invalid state.
26. In a composition root such as `main.py`, outside core business behavior.
27. A caller could mutate it directly and bypass the owning object's rules.
28. A later same-name method replaces an earlier one; `typing.overload` adds
    static signatures but no runtime dispatch.
29. An enum declares a closed set of named members; runtime boundary values and
    allowed transitions still require validation.

</details>

## Quick review checklist

- [ ] I understand identity, equality, mutability, aliasing, and copying.
- [ ] I use instance state rather than accidental shared class state.
- [ ] Constructors create valid objects.
- [ ] I can use instance methods, classmethods, static methods, and properties
  appropriately.
- [ ] I understand Python visibility conventions and their limits.
- [ ] Public behavior protects state and invariants.
- [ ] Internal mutable collections are not leaked.
- [ ] I can define and implement an `ABC` or `Protocol` contract.
- [ ] I can override behavior and rely on dynamic dispatch.
- [ ] I can justify inheritance versus composition in Python terms.
- [ ] I understand object relationships as ownership and lifecycle decisions.
- [ ] I choose dataclass and enum semantics intentionally.
- [ ] I can distinguish identity-bearing and value-like equality.
- [ ] Equal hashable objects have equal stable hashes.
- [ ] I use narrow collection annotations and understand basic generics.
- [ ] I know that annotations and `cast()` do not validate input.
- [ ] I validate before mutation and use meaningful exceptions.
- [ ] Dependencies are explicit and concrete wiring stays at the boundary.
- [ ] I can test with controlled collaborators.
- [ ] I can identify the common Python/OOP failure modes in unfamiliar code.

## Mastery gate

Topic 2 is complete only when all of the following are true:

- [ ] I score at least 25 out of 29 on the self-check without notes and answer
  every designated core question correctly.
- [ ] I score at least 8 out of 10 on the fixed recognition gate, including all
  five critical cases.
- [ ] I score at least 8 out of 10 on the fixed modeling gate, including the
  required ProductCode and InventoryItem decisions.
- [ ] I find, fix, test, and explain all seven defects in the object-semantics
  clinic within 30 minutes.
- [ ] My BankAccount, DateRange, BookCopy/ISBN, shapes, Playlist, and expiry
  notifier exercises satisfy every stated contract and required test.
- [ ] I use no unintended shared class state or mutable defaults.
- [ ] My public methods preserve invariants and do not leak mutable internals.
- [ ] I correctly demonstrate identity, equality, safe hashing, and shallow
  versus effective immutability.
- [ ] I demonstrate dynamic dispatch without type-condition branches.
- [ ] I replace an injected collaborator with a fake in a test.
- [ ] I add `Triangle` in under ten minutes without modifying `total_area` or
  breaking existing tests.
- [ ] I add `Playlist.move` in under fifteen minutes while all old and new tests
  remain green and every failed move preserves the previous order.
- [ ] I explain `ABC` versus `Protocol`, inheritance versus composition, and
  identity versus value semantics using code I wrote.
- [ ] All core exercise tests pass with no shared-state, hash-instability,
  collection-leak, partial-mutation, or hidden-dependency defect.

The readiness sentence for this topic is:

> I can express identity, state, behavior, invariants, ownership, and replaceable
> collaborations cleanly in Python, test them, and explain every important
> language and OOP choice.

## Next topic

[**Topic 3 - Domain Modeling and Responsibility Assignment**](./03-domain-modeling-and-responsibility-assignment.md)
covers domain vocabulary, entities, value objects, services, responsibilities,
collaborators, cardinality, lifecycle, invariants, state, ownership, and
change-oriented model review.
