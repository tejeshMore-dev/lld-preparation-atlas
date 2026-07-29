from abc import ABC, abstractmethod
from datetime import datetime


class Clock(ABC):
    """Time source abstraction that makes expiry behavior deterministic in tests."""

    @abstractmethod
    def now(self) -> datetime:
        raise NotImplementedError


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now()
