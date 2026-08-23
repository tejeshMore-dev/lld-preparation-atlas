from datetime import date, datetime

from models.aircraft import Aircraft
from models.airline import Airline
from models.airport import Airport
from models.enums import FlightStatus
from models.flight import Flight, FlightSeat
from models.money import to_money
from models.passenger import Passenger


class CatalogService:
    """Owns stable aviation data and scheduled flight instances."""

    def __init__(self) -> None:
        self.airports: dict[str, Airport] = {}
        self.airlines: dict[str, Airline] = {}
        self.passengers: dict[str, Passenger] = {}
        self.flights: dict[str, Flight] = {}

    def add_airport(self, airport: Airport) -> None:
        code = airport.code.strip().upper()
        if len(code) != 3 or not code.isalpha():
            raise ValueError("Airport code must contain exactly three letters")
        if code in self.airports:
            raise ValueError(f"Airport '{code}' already exists")
        self.airports[code] = airport

    def add_airline(self, airline: Airline) -> None:
        if airline.airline_id in self.airlines:
            raise ValueError(f"Airline '{airline.airline_id}' already exists")
        if any(existing.code.casefold() == airline.code.casefold() for existing in self.airlines.values()):
            raise ValueError(f"Airline code '{airline.code}' already exists")
        self.airlines[airline.airline_id] = airline

    def add_aircraft(self, airline_id: str, aircraft: Aircraft) -> None:
        if any(
            existing.registration_number == aircraft.registration_number
            for airline in self.airlines.values()
            for existing in airline.aircraft.values()
        ):
            raise ValueError(
                f"Aircraft registration '{aircraft.registration_number}' already exists"
            )
        self.get_airline(airline_id).add_aircraft(aircraft)

    def add_passenger(self, passenger: Passenger) -> None:
        if passenger.passenger_id in self.passengers:
            raise ValueError(f"Passenger '{passenger.passenger_id}' already exists")
        if any(
            existing.passport_number.casefold() == passenger.passport_number.casefold()
            for existing in self.passengers.values()
        ):
            raise ValueError("Passport number is already registered")
        self.passengers[passenger.passenger_id] = passenger

    def create_flight(
        self,
        flight_id: str,
        flight_number: str,
        airline_id: str,
        aircraft_id: str,
        origin_code: str,
        destination_code: str,
        departure_time: datetime,
        arrival_time: datetime,
        prices: dict,
        gate: str | None = None,
    ) -> Flight:
        if flight_id in self.flights:
            raise ValueError(f"Flight '{flight_id}' already exists")
        if arrival_time <= departure_time:
            raise ValueError("Arrival time must be after departure time")
        origin = self.get_airport(origin_code)
        destination = self.get_airport(destination_code)
        if origin.code.strip().upper() == destination.code.strip().upper():
            raise ValueError("Origin and destination must be different")
        airline = self.get_airline(airline_id)
        aircraft = airline.aircraft.get(aircraft_id)
        if aircraft is None:
            raise ValueError(f"Aircraft '{aircraft_id}' does not belong to airline '{airline_id}'")

        normalized_prices = {}
        for seat in aircraft.seats.values():
            if seat.cabin_class not in prices:
                raise ValueError(f"Missing fare for cabin {seat.cabin_class.name}")
            normalized_prices[seat.cabin_class] = to_money(prices[seat.cabin_class])
            if normalized_prices[seat.cabin_class] <= 0:
                raise ValueError("Cabin fares must be positive")

        for existing in self.flights.values():
            same_aircraft = (
                existing.airline_id == airline_id and existing.aircraft_id == aircraft_id
            )
            overlaps = (
                departure_time < existing.arrival_time
                and existing.departure_time < arrival_time
            )
            if same_aircraft and overlaps and existing.status is not FlightStatus.CANCELLED:
                raise ValueError(f"Aircraft schedule overlaps flight '{existing.flight_id}'")

        flight = Flight(
            flight_id=flight_id,
            flight_number=flight_number,
            airline_id=airline_id,
            aircraft_id=aircraft_id,
            origin_code=origin.code.strip().upper(),
            destination_code=destination.code.strip().upper(),
            departure_time=departure_time,
            arrival_time=arrival_time,
            prices=normalized_prices,
            seats={seat_id: FlightSeat(seat) for seat_id, seat in aircraft.seats.items()},
            gate=gate,
        )
        self.flights[flight_id] = flight
        return flight

    def find_flights(
        self,
        origin_code: str,
        destination_code: str,
        departure_date: date,
    ) -> list[Flight]:
        origin = origin_code.strip().upper()
        destination = destination_code.strip().upper()
        return sorted(
            (
                flight
                for flight in self.flights.values()
                if flight.origin_code == origin
                and flight.destination_code == destination
                and flight.departure_time.date() == departure_date
                and flight.status is FlightStatus.SCHEDULED
            ),
            key=lambda flight: flight.departure_time,
        )

    def get_airport(self, code: str) -> Airport:
        normalized = code.strip().upper()
        try:
            return self.airports[normalized]
        except KeyError as error:
            raise ValueError(f"Airport '{normalized}' does not exist") from error

    def get_airline(self, airline_id: str) -> Airline:
        try:
            return self.airlines[airline_id]
        except KeyError as error:
            raise ValueError(f"Airline '{airline_id}' does not exist") from error

    def get_passenger(self, passenger_id: str) -> Passenger:
        try:
            return self.passengers[passenger_id]
        except KeyError as error:
            raise ValueError(f"Passenger '{passenger_id}' does not exist") from error

    def get_flight(self, flight_id: str) -> Flight:
        try:
            return self.flights[flight_id]
        except KeyError as error:
            raise ValueError(f"Flight '{flight_id}' does not exist") from error
