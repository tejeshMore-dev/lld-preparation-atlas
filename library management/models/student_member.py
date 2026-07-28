from models.member import Member

class StudentMember(Member):
    MAX_BOOKS = 5
    LOAN_PERIOD_DAYS = 14

    def get_max_books(self) -> int:
        return self.MAX_BOOKS

    def get_loan_period(self) -> int:
        return self.LOAN_PERIOD_DAYS
