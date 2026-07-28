from dataclasses import dataclass

from models.author import Author

@dataclass
class Book:
    title: str
    isbn: str
    author: Author
    category: str
    publisher: str
