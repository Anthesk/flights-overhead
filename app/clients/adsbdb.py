import requests
from typing import Tuple, Dict
from app.config import ADSBDB_BASE_URL


class AdsbdbClient:
    """Interacts with ADSBDB API."""

    def get_details(self, icao24: str) -> Tuple[str, str]:
        """
        Retrieves aircraft details (manufacturer and model) from ADSBDB.

        Args:
            icao24 (str): The unique ICAO 24-bit address of the aircraft.

        Returns:
            Tuple[str, str]: A tuple containing (manufacturer, model).
                             Returns ("N/A", "") if lookup fails.
        """
        url = f"{ADSBDB_BASE_URL}/aircraft/{icao24}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "response" in data and "aircraft" in data["response"]:
                    aircraft = data["response"]["aircraft"]
                    return aircraft.get("manufacturer", "N/A"), aircraft.get("type", "")
        except Exception:
            pass
        return "N/A", ""

    def get_flight_info(self, callsign: str) -> Dict[str, str]:
        """
        Fetches route and airline information based on the flight callsign.

        Args:
            callsign (str): The flight callsign (e.g., "KLM93Z").

        Returns:
            Dict[str, str]: A dictionary containing available info:
                            - 'airline': Name of the airline.
                            - 'departure': ICAO code of departure airport.
                            - 'arrival': ICAO code of arrival airport.
                            Returns empty dict if lookup fails.
        """
        if not callsign:
            return {}

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

                    return info
        except Exception:
            pass
        return {}
