from datetime import datetime
from dataclasses import dataclass

from models.book import Book
from models.member import Member
from models.enum import ReservationStatus

@dataclass
class Reservation:
    reservation_id: str
    book: Book
    member: Member
    reservation_date: datetime
    status: ReservationStatus = ReservationStatus.WAITING
