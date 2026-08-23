class AuthenticationError(ValueError):
    def __init__(self, message: str, end_session: bool = False) -> None:
        super().__init__(message)
        self.end_session = end_session
