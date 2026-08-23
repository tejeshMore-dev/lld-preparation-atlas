from dataclasses import dataclass

from models.person import Person
from models.enum import AccountStatus

@dataclass
class Account(Person):
    account_id: str
    account_status: AccountStatus
