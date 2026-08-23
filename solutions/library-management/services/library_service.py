import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta

from models.book import Book
from models.book_item import BookItem
from models.catalog import Catalog
from models.enum import AccountStatus, BookStatus, ReservationStatus
from models.loan import Loan
from models.member import Member
from models.notification import Notification
from models.reservation import Reservation
from observers.subject import Subject
from services.notification_service import NotificationService
from strategies.fine_strategy import FineStrategy


class LibraryService(Subject):
    def __init__(
        self,
        catalog: Catalog,
        book_items: list[BookItem],
        loans: list[Loan],
        notification_service: NotificationService,
        fine_strategy: FineStrategy,
    ) -> None:
        super().__init__()
        self.catalog = catalog
        self.book_items = book_items
        self.loans = loans
        self.reservations: dict[str, deque[Reservation]] = defaultdict(deque)
        self.reservation_history: list[Reservation] = []
        self.notification_service = notification_service
        self.fine_strategy = fine_strategy

    def add_book(self, book: Book) -> None:
        self.catalog.add_book(book)

    def add_book_item(self, book_item: BookItem) -> None:
        catalog_book = self.catalog.search_by_isbn(book_item.book.isbn)
        if catalog_book is None:
            raise ValueError("Add the book to the catalog before adding its copy")
        if catalog_book != book_item.book:
            raise ValueError("Book copy metadata does not match the catalog")
        if any(item.barcode == book_item.barcode for item in self.book_items):
            raise ValueError(f'Book copy "{book_item.barcode}" already exists')
        self.book_items.append(book_item)

    def search_by_title(self, title: str) -> list[Book]:
        return self.catalog.search_by_title(title)

    def search_by_author(self, author: str) -> list[Book]:
        return self.catalog.search_by_author(author)

    def search_by_category(self, category: str) -> list[Book]:
        return self.catalog.search_by_category(category)

    def search_by_isbn(self, isbn: str) -> Book | None:
        return self.catalog.search_by_isbn(isbn)

    def _ensure_active_member(self, member: Member) -> None:
        if member.account_status != AccountStatus.ACTIVE:
            raise ValueError("Only active members can perform this operation")

    def _find_available_copy(self, book: Book) -> BookItem | None:
        return next(
            (
                item
                for item in self.book_items
                if item.book == book and item.status == BookStatus.AVAILABLE
            ),
            None,
        )

    def _find_borrowable_copy(
        self,
        book: Book,
        member: Member,
    ) -> BookItem | None:
        reserved_copy = next(
            (
                item
                for item in self.book_items
                if item.book == book
                and item.status == BookStatus.RESERVED
                and item.reserved_for_id == member.account_id
            ),
            None,
        )
        return reserved_copy or self._find_available_copy(book)

    def borrow_book(self, member: Member, isbn: str) -> Loan:
        self._ensure_active_member(member)

        if len(member.borrowed_books) >= member.get_max_books():
            raise ValueError("Member has reached the borrowing limit")

        book = self.search_by_isbn(isbn)
        if book is None:
            raise ValueError("Book not found")

        book_item = self._find_borrowable_copy(book, member)
        if book_item is None:
            raise ValueError("Book copy not available")

        was_reserved = book_item.status == BookStatus.RESERVED
        borrowed_at = datetime.now()
        loan = Loan(
            loan_id=str(uuid.uuid4()),
            member=member,
            book_item=book_item,
            borrow_date=borrowed_at,
            due_date=borrowed_at + timedelta(days=member.get_loan_period()),
        )

        book_item.status = BookStatus.ISSUED
        book_item.borrower_id = member.account_id
        book_item.reserved_for_id = None
        self.loans.append(loan)
        member.borrowed_books.append(book_item)

        if was_reserved:
            self._complete_ready_reservation(member, book)

        self.notify(
            "BOOK_BORROWED",
            {
                "title": book.title,
                "barcode": book_item.barcode,
                "member": member.name,
                "due_date": loan.due_date,
            },
        )
        return loan

    def _complete_ready_reservation(self, member: Member, book: Book) -> None:
        reservation = next(
            (
                item
                for item in self.reservation_history
                if item.book == book
                and item.member.account_id == member.account_id
                and item.status == ReservationStatus.READY
            ),
            None,
        )
        if reservation is not None:
            reservation.status = ReservationStatus.COMPLETED
        if book in member.reserved_books:
            member.reserved_books.remove(book)

    def _find_active_loan(self, barcode: str) -> Loan | None:
        return next(
            (
                loan
                for loan in self.loans
                if loan.book_item.barcode == barcode and loan.return_date is None
            ),
            None,
        )

    def return_book(self, barcode: str) -> tuple[Loan, float]:
        loan = self._find_active_loan(barcode)
        if loan is None:
            raise ValueError("Active loan not found")

        loan.return_date = datetime.now()
        fine = self.fine_strategy.calculate_fine(loan)
        loan.member.total_fine += fine

        book_item = loan.book_item
        book_item.borrower_id = None
        book_item.reserved_for_id = None
        book_item.status = BookStatus.AVAILABLE
        if book_item in loan.member.borrowed_books:
            loan.member.borrowed_books.remove(book_item)

        self.notify(
            "BOOK_RETURNED",
            {
                "title": book_item.book.title,
                "barcode": barcode,
                "member": loan.member.name,
                "fine": fine,
            },
        )
        self._process_reservations(book_item.book.isbn, book_item)
        return loan, fine

    def reserve_book(self, member: Member, isbn: str) -> Reservation:
        self._ensure_active_member(member)

        book = self.search_by_isbn(isbn)
        if book is None:
            raise ValueError("Book not found")
        if self._find_available_copy(book) is not None:
            raise ValueError("Book is available and does not need a reservation")

        duplicate = any(
            reservation.book == book
            and reservation.member.account_id == member.account_id
            and reservation.status
            in (ReservationStatus.WAITING, ReservationStatus.READY)
            for reservation in self.reservation_history
        )
        if duplicate:
            raise ValueError("Member already has an active reservation for this book")

        reservation = Reservation(
            reservation_id=str(uuid.uuid4()),
            book=book,
            member=member,
            reservation_date=datetime.now(),
        )
        self.reservations[isbn].append(reservation)
        self.reservation_history.append(reservation)
        member.reserved_books.append(book)

        self.notify(
            "BOOK_RESERVED",
            {
                "title": book.title,
                "member": member.name,
                "reservation_id": reservation.reservation_id,
            },
        )
        return reservation

    def cancel_reservation(self, member: Member, isbn: str) -> Reservation:
        reservation = next(
            (
                item
                for item in self.reservation_history
                if item.book.isbn == isbn
                and item.member.account_id == member.account_id
                and item.status
                in (ReservationStatus.WAITING, ReservationStatus.READY)
            ),
            None,
        )
        if reservation is None:
            raise ValueError("Active reservation not found")

        available_item: BookItem | None = None
        if reservation.status == ReservationStatus.WAITING:
            self.reservations[isbn].remove(reservation)
        else:
            available_item = next(
                (
                    item
                    for item in self.book_items
                    if item.book == reservation.book
                    and item.status == BookStatus.RESERVED
                    and item.reserved_for_id == member.account_id
                ),
                None,
            )
            if available_item is not None:
                available_item.status = BookStatus.AVAILABLE
                available_item.reserved_for_id = None

        reservation.status = ReservationStatus.CANCELLED
        if reservation.book in member.reserved_books:
            member.reserved_books.remove(reservation.book)
        if available_item is not None:
            self._process_reservations(isbn, available_item)
        return reservation

    def _process_reservations(
        self,
        isbn: str,
        book_item: BookItem,
    ) -> Reservation | None:
        queue = self.reservations.get(isbn)
        if not queue:
            return None

        reservation = queue.popleft()
        reservation.status = ReservationStatus.READY
        book_item.status = BookStatus.RESERVED
        book_item.reserved_for_id = reservation.member.account_id

        notification = Notification(
            notification_id=str(uuid.uuid4()),
            member=reservation.member,
            message=f'Your reserved book "{reservation.book.title}" is now available.',
            created_at=datetime.now(),
        )
        self.notification_service.send(notification)
        self.notify(
            "RESERVATION_AVAILABLE",
            {
                "title": reservation.book.title,
                "member": reservation.member.name,
                "reservation_id": reservation.reservation_id,
            },
        )
        return reservation

    def pay_fine(self, member: Member, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero")
        if amount > member.total_fine:
            raise ValueError("Payment amount exceeds the outstanding fine")

        member.total_fine -= amount
        self.notify(
            "FINE_PAID",
            {
                "member": member.name,
                "amount": amount,
                "remaining_fine": member.total_fine,
            },
        )
        return member.total_fine
