from abc import ABC, abstractmethod

from models.loan import Loan

class FineStrategy(ABC):
    @abstractmethod
    def calculate_fine(self, loan: Loan) -> float:
        raise NotImplementedError
