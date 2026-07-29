from models.enums import RoomStatus
from models.guest import Guest
from models.hotel import Hotel
from models.money import to_money
from models.room import Room


class CatalogService:
    """Manages stable guest, hotel, and physical room information."""

    def __init__(self) -> None:
        self.guests: dict[str, Guest] = {}
        self.hotels: dict[str, Hotel] = {}

    def add_guest(self, guest: Guest) -> None:
        if guest.guest_id in self.guests:
            raise ValueError(f"Guest '{guest.guest_id}' already exists")
        if any(existing.email.casefold() == guest.email.casefold() for existing in self.guests.values()):
            raise ValueError(f"Email '{guest.email}' is already registered")
        self.guests[guest.guest_id] = guest

    def add_hotel(self, hotel: Hotel) -> None:
        if hotel.hotel_id in self.hotels:
            raise ValueError(f"Hotel '{hotel.hotel_id}' already exists")
        self.hotels[hotel.hotel_id] = hotel

    def add_room(self, hotel_id: str, room: Room) -> None:
        room.nightly_rate = to_money(room.nightly_rate)
        self.get_hotel(hotel_id).add_room(room)

    def set_room_status(self, hotel_id: str, room_id: str, status: RoomStatus) -> Room:
        room = self.get_room(hotel_id, room_id)
        room.status = status
        return room

    def search_hotels(self, city: str) -> list[Hotel]:
        city_key = city.strip().casefold()
        return sorted(
            (
                hotel
                for hotel in self.hotels.values()
                if hotel.city.strip().casefold() == city_key
            ),
            key=lambda hotel: hotel.name.casefold(),
        )

    def get_guest(self, guest_id: str) -> Guest:
        try:
            return self.guests[guest_id]
        except KeyError as error:
            raise ValueError(f"Guest '{guest_id}' does not exist") from error

    def get_hotel(self, hotel_id: str) -> Hotel:
        try:
            return self.hotels[hotel_id]
        except KeyError as error:
            raise ValueError(f"Hotel '{hotel_id}' does not exist") from error

    def get_room(self, hotel_id: str, room_id: str) -> Room:
        hotel = self.get_hotel(hotel_id)
        try:
            return hotel.rooms[room_id]
        except KeyError as error:
            raise ValueError(f"Room '{room_id}' does not exist in hotel '{hotel_id}'") from error
