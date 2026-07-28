from datetime import datetime, timedelta

from factories.member_factory import MemberFactory
from models.author import Author
from models.book import Book
from models.book_item import BookItem
from models.catalog import Catalog
from models.enum import MemberType
from observers.email_observer import EmailObserver
from observers.logger_observer import LoggerObserver
from services.library_service import LibraryService
from services.notification_service import NotificationService
from strategies.daily_fine_strategy import DailyFineStrategy


def main() -> None:
    library = LibraryService(
        catalog=Catalog(),
        book_items=[],
        loans=[],
        notification_service=NotificationService(),
        fine_strategy=DailyFineStrategy(),
    )
    library.attach(EmailObserver())
    library.attach(LoggerObserver())

    author = Author(author_id="author-1", name="J.K. Rowling")
    book = Book(
        title="Harry Potter and the Sorcerer's Stone",
        author=author,
        category="Fantasy",
        isbn="978-0439708180",
        publisher="Scholastic",
    )
    book_item = BookItem(
        book=book,
        barcode="1234567890",
        shelf_location="Section A",
    )
    library.add_book(book)
    library.add_book_item(book_item)

    student = MemberFactory.create_member(
        account_id="student-1",
        name="Aarav",
        email="aarav@example.com",
        phone="+91-9000000001",
        member_type=MemberType.STUDENT,
    )
    faculty = MemberFactory.create_member(
        account_id="faculty-1",
        name="Dr. Mehta",
        email="mehta@example.com",
        phone="+91-9000000002",
        member_type=MemberType.FACULTY,
    )

    loan = library.borrow_book(student, book.isbn)
    library.reserve_book(faculty, book.isbn)

    # Make the demo return overdue so the fine workflow is visible.
    loan.due_date = datetime.now() - timedelta(days=2)
    _, fine = library.return_book(book_item.barcode)
    if fine:
        library.pay_fine(student, fine)

    library.borrow_book(faculty, book.isbn)


if __name__ == "__main__":
    main()
