from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from models.member import Member
from models.book_item import BookItem

@dataclass
class Loan:
    loan_id: str
    member: Member
    book_item: BookItem
    borrow_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
