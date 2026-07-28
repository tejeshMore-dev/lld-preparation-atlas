from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from models.account import Account
from models.book_item import BookItem
from models.book import Book
from models.enum import MemberType

@dataclass
class Member(Account, ABC):
    member_type: MemberType
    borrowed_books: list[BookItem] = field(default_factory=list)
    reserved_books: list[Book] = field(default_factory=list)
    total_fine: float = 0.0

    @abstractmethod
    def get_max_books(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_loan_period(self) -> int:
        raise NotImplementedError
