from dataclasses import dataclass, field


@dataclass
class Group:
    group_id: str
    name: str
    created_by_id: str
    member_ids: set[str] = field(default_factory=set)
    expense_ids: list[str] = field(default_factory=list)

    def add_member(self, user_id: str) -> None:
        if user_id in self.member_ids:
            raise ValueError("User is already a member of this group")
        self.member_ids.add(user_id)
