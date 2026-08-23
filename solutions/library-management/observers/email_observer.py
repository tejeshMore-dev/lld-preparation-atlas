from observers.observer import Observer

class EmailObserver(Observer):
    def update(self, event: str, data: dict) -> None:
        handlers = {
            "BOOK_BORROWED": self._book_borrowed,
            "BOOK_RETURNED": self._book_returned,
            "RESERVATION_AVAILABLE": self._reservation_available,
            "FINE_PAID": self._fine_paid,
        }
        handler = handlers.get(event)
        if handler is not None:
            handler(data)

    def _book_borrowed(self, data: dict) -> None:
        print(
            f'[EMAIL] Book "{data["title"]}" was borrowed by '
            f'{data["member"]}; due on {data["due_date"].date()}.'
        )

    def _book_returned(self, data: dict) -> None:
        print(
            f'[EMAIL] Book "{data["title"]}" was returned by '
            f'{data["member"]}.'
        )

    def _reservation_available(self, data: dict) -> None:
        print(
            f'[EMAIL] Book "{data["title"]}" is now available for '
            f'{data["member"]}.'
        )

    def _fine_paid(self, data: dict) -> None:
        print(f'[EMAIL] {data["member"]} paid a fine of ${data["amount"]:.2f}.')
