import unittest
from datetime import datetime, timedelta

from factories.member_factory import MemberFactory
from models.author import Author
from models.book import Book
from models.book_item import BookItem
from models.catalog import Catalog
from models.enum import (
    AccountStatus,
    BookStatus,
    MemberType,
    ReservationStatus,
)
from observers.observer import Observer
from services.library_service import LibraryService
from services.notification_service import NotificationService
from strategies.daily_fine_strategy import DailyFineStrategy


class SilentNotificationService(NotificationService):
    def send(self, notification) -> None:
        self.sent_notifications.append(notification)


class RecordingObserver(Observer):
    def __init__(self) -> None:
        self.events: list[str] = []

    def update(self, event: str, data: dict) -> None:
        self.events.append(event)


class LibraryServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.author = Author(author_id="author-1", name="Test Author")
        self.book = Book(
            title="Domain Design",
            isbn="isbn-1",
            author=self.author,
            category="Technology",
            publisher="Test Publisher",
        )
        self.book_item = BookItem(
            book=self.book,
            barcode="barcode-1",
            shelf_location="A-1",
        )
        self.notifications = SilentNotificationService()
        self.library = LibraryService(
            catalog=Catalog(),
            book_items=[],
            loans=[],
            notification_service=self.notifications,
            fine_strategy=DailyFineStrategy(),
        )
        self.library.add_book(self.book)
        self.library.add_book_item(self.book_item)
        self.observer = RecordingObserver()
        self.library.attach(self.observer)

        self.student = self.make_member("student-1", MemberType.STUDENT)
        self.faculty = self.make_member("faculty-1", MemberType.FACULTY)

    @staticmethod
    def make_member(account_id: str, member_type: MemberType):
        return MemberFactory.create_member(
            account_id=account_id,
            name=account_id,
            email=f"{account_id}@example.com",
            phone="1234567890",
            member_type=member_type,
        )

    def test_catalog_search_and_duplicate_isbn(self) -> None:
        self.assertEqual(self.library.search_by_title("domain"), [self.book])
        self.assertEqual(self.library.search_by_author("test"), [self.book])
        self.assertEqual(
            self.library.search_by_category("technology"),
            [self.book],
        )
        self.assertIs(self.library.search_by_isbn("isbn-1"), self.book)
        with self.assertRaises(ValueError):
            self.library.add_book(self.book)

    def test_borrow_uses_member_period_and_updates_copy(self) -> None:
        loan = self.library.borrow_book(self.student, self.book.isbn)

        self.assertEqual(self.book_item.status, BookStatus.ISSUED)
        self.assertEqual(self.book_item.borrower_id, self.student.account_id)
        self.assertIn(self.book_item, self.student.borrowed_books)
        self.assertEqual((loan.due_date - loan.borrow_date).days, 14)
        self.assertIn("BOOK_BORROWED", self.observer.events)

    def test_inactive_member_and_borrow_limit_are_rejected(self) -> None:
        self.student.account_status = AccountStatus.BLOCKED
        with self.assertRaises(ValueError):
            self.library.borrow_book(self.student, self.book.isbn)

        self.student.account_status = AccountStatus.ACTIVE
        self.student.borrowed_books = [self.book_item] * self.student.get_max_books()
        with self.assertRaises(ValueError):
            self.library.borrow_book(self.student, self.book.isbn)

    def test_return_makes_reservation_ready_for_correct_member(self) -> None:
        self.library.borrow_book(self.student, self.book.isbn)
        reservation = self.library.reserve_book(self.faculty, self.book.isbn)

        self.library.return_book(self.book_item.barcode)

        self.assertEqual(reservation.status, ReservationStatus.READY)
        self.assertEqual(self.book_item.status, BookStatus.RESERVED)
        self.assertEqual(
            self.book_item.reserved_for_id,
            self.faculty.account_id,
        )
        self.assertEqual(len(self.notifications.sent_notifications), 1)
        with self.assertRaises(ValueError):
            self.library.borrow_book(self.student, self.book.isbn)

        self.library.borrow_book(self.faculty, self.book.isbn)
        self.assertEqual(reservation.status, ReservationStatus.COMPLETED)
        self.assertNotIn(self.book, self.faculty.reserved_books)

    def test_overdue_fine_can_be_paid(self) -> None:
        loan = self.library.borrow_book(self.student, self.book.isbn)
        loan.due_date = datetime.now() - timedelta(days=3)

        _, fine = self.library.return_book(self.book_item.barcode)

        self.assertEqual(fine, 6.0)
        self.assertEqual(self.student.total_fine, 6.0)
        remaining = self.library.pay_fine(self.student, 4.0)
        self.assertEqual(remaining, 2.0)
        self.assertIn("FINE_PAID", self.observer.events)

    def test_cancelling_ready_reservation_advances_queue(self) -> None:
        second_student = self.make_member("student-2", MemberType.STUDENT)
        self.library.borrow_book(self.student, self.book.isbn)
        first = self.library.reserve_book(self.faculty, self.book.isbn)
        second = self.library.reserve_book(second_student, self.book.isbn)
        self.library.return_book(self.book_item.barcode)

        self.library.cancel_reservation(self.faculty, self.book.isbn)

        self.assertEqual(first.status, ReservationStatus.CANCELLED)
        self.assertEqual(second.status, ReservationStatus.READY)
        self.assertEqual(
            self.book_item.reserved_for_id,
            second_student.account_id,
        )


if __name__ == "__main__":
    unittest.main()
