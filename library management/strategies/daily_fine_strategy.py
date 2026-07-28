from models.loan import Loan

from strategies.fine_strategy import FineStrategy

class DailyFineStrategy(FineStrategy):
    DAILY_FINE = 2.0

    def calculate_fine(self, loan: Loan) -> float:
        if loan.return_date is None:
            raise ValueError("Fine cannot be calculated before the book is returned")

        overdue_days = (loan.return_date.date() - loan.due_date.date()).days
        overdue_days = max(0, overdue_days)

        return self.DAILY_FINE * overdue_days
