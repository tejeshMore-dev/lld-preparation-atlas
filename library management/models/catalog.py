from dataclasses import dataclass, field

from models.book import Book


@dataclass
class Catalog:
    books: list[Book] = field(default_factory=list)

    def add_book(self, book: Book) -> None:
        if self.search_by_isbn(book.isbn) is not None:
            raise ValueError(f'A book with ISBN "{book.isbn}" already exists')
        self.books.append(book)

    def search_by_title(self, title: str) -> list[Book]:
        return [
            book
            for book in self.books
            if title.lower() in book.title.lower()
        ]

    def search_by_author(self, author_name: str) -> list[Book]:
        return [
            book
            for book in self.books
            if author_name.lower() in book.author.name.lower()
        ]

    def search_by_category(self, category: str) -> list[Book]:
        return [
            book
            for book in self.books
            if category.lower() == book.category.lower()
        ]

    def search_by_isbn(self, isbn: str) -> Book | None:
        for book in self.books:
            if book.isbn == isbn:
                return book
        return None
