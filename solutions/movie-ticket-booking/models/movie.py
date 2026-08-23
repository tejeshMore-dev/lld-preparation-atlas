from dataclasses import dataclass


@dataclass(frozen=True)
class Movie:
    movie_id: str
    title: str
    duration_minutes: int
    language: str
    genre: str
    certificate: str
