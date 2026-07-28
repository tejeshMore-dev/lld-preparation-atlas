from dataclasses import dataclass

from models.account import Account

@dataclass
class Librarian(Account):
    employee_id: str
