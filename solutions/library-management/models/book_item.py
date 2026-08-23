from dataclasses import dataclass
from typing import Optional

from models.book import Book
from models.enum import BookStatus

@dataclass
class BookItem:
    book: Book
    barcode: str
    shelf_location: str
    status: BookStatus = BookStatus.AVAILABLE
    borrower_id: Optional[str] = None
    reserved_for_id: Optional[str] = None
