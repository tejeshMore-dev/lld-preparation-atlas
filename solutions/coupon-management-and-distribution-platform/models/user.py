from dataclasses import dataclass, field


@dataclass(frozen=True)
class User:
    user_id: str
    name: str
    email: str
    segments: frozenset[str] = field(default_factory=frozenset)
    loyalty_points: int = 0
