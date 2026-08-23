from models.member import Member

class FacultyMember(Member):
    MAX_BOOKS = 20
    LOAN_PERIOD_DAYS = 30

    def get_max_books(self) -> int:
        return self.MAX_BOOKS

    def get_loan_period(self) -> int:
        return self.LOAN_PERIOD_DAYS
