import os
from app.clients.opensky import OpenSkyClient
from app.clients.adsbdb import AdsbdbClient
from app.config import LAT_MIN, LAT_MAX, LON_MIN, LON_MAX


class FlightTracker:
    """Main application controller."""

    def __init__(self):
        """
        Initializes the Flight Tracker.

        Sets up the API clients using credentials from environment variables
        and defines the geographical bounding box for tracking.
        """
        client_id = os.getenv("OPENSKY_CLIENT_ID")
        client_secret = os.getenv("OPENSKY_CLIENT_SECRET")

        if not client_id or not client_secret:
            print("Note: Missing OpenSky authentification.")

        self.opensky = OpenSkyClient(client_id, client_secret)
        self.adsbdb = AdsbdbClient()
        self.bbox = (LAT_MIN, LAT_MAX, LON_MIN, LON_MAX)

    def get_flights(self):
        """
        Fetches and enriches flight data.

        Returns:
            List[Aircraft]: A list of enriched Aircraft objects.
        """
        print(f"Looking for flights in the bounding box...")
        aircraft_list = self.opensky.get_states(self.bbox)

        if not aircraft_list:
            print("No aircraft detected.")
            return []

        print(f"--- {len(aircraft_list)} aircraft(s) detected ---")

        for aircraft in aircraft_list:
            # 1. Fetch Aircraft Details (Manufacturer/Model)
            man, model = self.adsbdb.get_details(aircraft.icao24)
            aircraft.manufacturer = man
            aircraft.model = model

            # 2. Fetch Flight Route & Airline from ADSBDB
            flight_info = self.adsbdb.get_flight_info(aircraft.callsign)

            if "departure" in flight_info:
                aircraft.departure = flight_info["departure"]
            if "arrival" in flight_info:
                aircraft.arrival = flight_info["arrival"]
            if "airline" in flight_info:
                aircraft.airline = flight_info["airline"]

        return aircraft_list

    def run(self):
        """
        Executes the main tracking logic (Fetch & Print).

        1. Fetches current aircraft states from OpenSky.
        2. Iterates through each aircraft to fetch additional details (Model, Route) from ADSBDB.
        3. Prints the enriched flight information to the console.
        """
        aircraft_list = self.get_flights()
        for aircraft in aircraft_list:
            print(aircraft)
