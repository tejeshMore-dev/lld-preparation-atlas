from datetime import datetime
from dataclasses import dataclass

from models.member import Member

@dataclass
class Notification:
    notification_id: str
    member: Member
    message: str
    created_at: datetime
    is_read: bool = False