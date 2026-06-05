import requests
from typing import Tuple, Dict
from app.config import ADSBDB_BASE_URL


class AdsbdbClient:
    """Interacts with ADSBDB API with in-memory caching."""

    def __init__(self):
        self._details_cache = {}
        self._route_cache = {}

    def get_details(self, icao24: str) -> Tuple[str, str]:
        """
        Retrieves aircraft details (manufacturer and model) from ADSBDB.
        Caches results to prevent redundant API queries.

        Args:
            icao24 (str): The unique ICAO 24-bit address of the aircraft.

        Returns:
            Tuple[str, str]: A tuple containing (manufacturer, model).
                             Returns ("N/A", "") if lookup fails.
        """
        if not icao24:
            return "N/A", ""

        icao24 = icao24.lower().strip()
        if icao24 in self._details_cache:
            return self._details_cache[icao24]

        url = f"{ADSBDB_BASE_URL}/aircraft/{icao24}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "response" in data and "aircraft" in data["response"]:
                    aircraft = data["response"]["aircraft"]
                    res = (aircraft.get("manufacturer", "N/A"), aircraft.get("type", ""))
                    self._details_cache[icao24] = res
                    return res
            elif response.status_code == 404:
                # Cache the negative result so we don't poll the API repeatedly for unknown aircraft
                self._details_cache[icao24] = ("N/A", "")
                return "N/A", ""
        except Exception:
            pass
        return "N/A", ""

    def get_flight_info(self, callsign: str) -> Dict[str, str]:
        """
        Fetches route and airline information based on the flight callsign.
        Caches results to prevent redundant API queries.

        Args:
            callsign (str): The flight callsign (e.g., "KLM93Z").

        Returns:
            Dict[str, str]: A dictionary containing available info:
                            - 'airline': Name of the airline.
                            - 'departure': ICAO code of departure airport.
                            - 'arrival': ICAO code of arrival airport.
                            Returns empty dict if lookup fails or not found.
        """
        if not callsign:
            return {}

        callsign = callsign.upper().strip()
        if callsign in self._route_cache:
            return self._route_cache[callsign]

        url = f"{ADSBDB_BASE_URL}/callsign/{callsign}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "response" in data and "flightroute" in data["response"]:
                    route = data["response"]["flightroute"]

                    info = {}

                    # Airline
                    if "airline" in route and route["airline"]:
                        info["airline"] = route["airline"].get("name")

                    # Origin
                    if "origin" in route and route["origin"]:
                        info["departure"] = route["origin"].get("icao_code")

                    # Destination
                    if "destination" in route and route["destination"]:
                        info["arrival"] = route["destination"].get("icao_code")

                    self._route_cache[callsign] = info
                    return info
            elif response.status_code == 404:
                # Cache the negative result so we don't poll the API repeatedly for unknown routes
                self._route_cache[callsign] = {}
                return {}
        except Exception:
            pass
        return {}
