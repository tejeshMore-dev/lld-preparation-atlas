from models.loan import Loan
from strategies.fine_strategy import FineStrategy


class NoFineStrategy(FineStrategy):
    def calculate_fine(self, loan: Loan) -> float:
        return 0.0
