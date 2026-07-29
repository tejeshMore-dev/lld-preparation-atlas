from datetime import date, datetime, timedelta

from models.money import to_money
from models.movie import Movie
from models.screen import Screen
from models.show import Show, ShowSeat
from models.theatre import Theatre
from models.user import User


class CatalogService:
    """Owns relatively stable catalog data and creates scheduled shows."""

    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.movies: dict[str, Movie] = {}
        self.theatres: dict[str, Theatre] = {}
        self.shows: dict[str, Show] = {}

    def add_user(self, user: User) -> None:
        if user.user_id in self.users:
            raise ValueError(f"User '{user.user_id}' already exists")
        if any(existing.email.lower() == user.email.lower() for existing in self.users.values()):
            raise ValueError(f"Email '{user.email}' is already registered")
        self.users[user.user_id] = user

    def add_movie(self, movie: Movie) -> None:
        if movie.movie_id in self.movies:
            raise ValueError(f"Movie '{movie.movie_id}' already exists")
        if movie.duration_minutes <= 0:
            raise ValueError("Movie duration must be positive")
        self.movies[movie.movie_id] = movie

    def add_theatre(self, theatre: Theatre) -> None:
        if theatre.theatre_id in self.theatres:
            raise ValueError(f"Theatre '{theatre.theatre_id}' already exists")
        self.theatres[theatre.theatre_id] = theatre

    def add_screen(self, theatre_id: str, screen: Screen) -> None:
        self.get_theatre(theatre_id).add_screen(screen)

    def create_show(
        self,
        show_id: str,
        movie_id: str,
        theatre_id: str,
        screen_id: str,
        start_time: datetime,
        prices: dict,
    ) -> Show:
        if show_id in self.shows:
            raise ValueError(f"Show '{show_id}' already exists")
        movie = self.get_movie(movie_id)
        theatre = self.get_theatre(theatre_id)
        screen = theatre.screens.get(screen_id)
        if screen is None:
            raise ValueError(f"Screen '{screen_id}' does not exist in theatre '{theatre_id}'")
        if not screen.seats:
            raise ValueError("A show cannot be created on a screen without seats")

        normalized_prices = {}
        for seat in screen.seats.values():
            if seat.seat_type not in prices:
                raise ValueError(f"Missing price for seat type {seat.seat_type.name}")
            normalized_prices[seat.seat_type] = to_money(prices[seat.seat_type])
            if normalized_prices[seat.seat_type] <= 0:
                raise ValueError("Seat prices must be positive")

        end_time = start_time + timedelta(minutes=movie.duration_minutes)
        for existing in self.shows.values():
            same_screen = (
                existing.theatre_id == theatre_id and existing.screen_id == screen_id
            )
            overlaps = start_time < existing.end_time and existing.start_time < end_time
            if same_screen and overlaps:
                raise ValueError(f"Show overlaps with existing show '{existing.show_id}'")

        show = Show(
            show_id=show_id,
            movie_id=movie_id,
            theatre_id=theatre_id,
            screen_id=screen_id,
            start_time=start_time,
            end_time=end_time,
            prices=normalized_prices,
            seats={seat_id: ShowSeat(seat) for seat_id, seat in screen.seats.items()},
        )
        self.shows[show_id] = show
        return show

    def search_shows(
        self,
        city: str,
        movie_id: str | None = None,
        show_date: date | None = None,
    ) -> list[Show]:
        city_key = city.strip().casefold()
        results = []
        for show in self.shows.values():
            theatre = self.theatres[show.theatre_id]
            if theatre.city.strip().casefold() != city_key:
                continue
            if movie_id is not None and show.movie_id != movie_id:
                continue
            if show_date is not None and show.start_time.date() != show_date:
                continue
            results.append(show)
        return sorted(results, key=lambda show: show.start_time)

    def get_user(self, user_id: str) -> User:
        try:
            return self.users[user_id]
        except KeyError as error:
            raise ValueError(f"User '{user_id}' does not exist") from error

    def get_movie(self, movie_id: str) -> Movie:
        try:
            return self.movies[movie_id]
        except KeyError as error:
            raise ValueError(f"Movie '{movie_id}' does not exist") from error

    def get_theatre(self, theatre_id: str) -> Theatre:
        try:
            return self.theatres[theatre_id]
        except KeyError as error:
            raise ValueError(f"Theatre '{theatre_id}' does not exist") from error

    def get_show(self, show_id: str) -> Show:
        try:
            return self.shows[show_id]
        except KeyError as error:
            raise ValueError(f"Show '{show_id}' does not exist") from error
