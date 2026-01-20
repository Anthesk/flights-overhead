import requests
import time
from typing import List, Tuple, Optional
from app.models import Aircraft
from app.config import OPENSKY_BASE_URL, OPENSKY_AUTH_URL


class OpenSkyClient:
    """Interacts with OpenSky Network API."""

    def __init__(
        self, client_id: Optional[str] = None, client_secret: Optional[str] = None
    ):
        """
        Initializes the OpenSky client.

        Args:
            client_id (Optional[str]): OpenSky API Client ID.
            client_secret (Optional[str]): OpenSky API Client Secret.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = requests.Session()
        self._authenticate()

    def _authenticate(self):
        """
        Authenticates with the OpenSky API using the Client Credentials flow.

        Obtains a JWT token and updates the session headers.
        Requires client_id and client_secret to be set.
        """
        if not self.client_id or not self.client_secret:
            return

        try:
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            response = requests.post(OPENSKY_AUTH_URL, data=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                if token:
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
            else:
                print(
                    f"OpenSky authentication failure: {response.status_code} - {response.text}"
                )
        except Exception as e:
            print(f"OpenSky authentication error: {e}")

    def get_states(self, bbox: Tuple[float, float, float, float]) -> List[Aircraft]:
        """
        Retrieves the state vectors of all aircraft within a bounding box.

        Args:
            bbox (Tuple[float, float, float, float]): Bounding box (min_lat, max_lat, min_lon, max_lon).

        Returns:
            List[Aircraft]: A list of Aircraft objects representing the flights in the area.
        """
        url = f"{OPENSKY_BASE_URL}/states/all"
        params = {
            "lamin": bbox[0],
            "lamax": bbox[1],
            "lomin": bbox[2],
            "lomax": bbox[3],
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code != 200:
                print(f"OpenSky States API error: {response.status_code}")
                return []

            data = response.json()

            if not data or data["states"] is None:
                return []

            aircraft_list = []
            for state in data["states"]:
                # State vector indices:
                # 0: icao24, 1: callsign, 2: origin_country, 7: baro_altitude, 9: velocity, 10: true_track
                aircraft = Aircraft(
                    icao24=state[0],
                    callsign=state[1].strip(),
                    origin_country=state[2],
                    altitude=state[7] if state[7] is not None else 0.0,
                    velocity=state[9] if state[9] is not None else 0.0,
                    heading=state[10],
                )
                aircraft_list.append(aircraft)
            return aircraft_list

        except Exception as e:
            print(f"OpenSky States API error: {e}")
            return []

    # Kept for reference but not used in favor of ADSBDB
    def get_route(self, icao24: str) -> Tuple[str, str]:
        """
        [Deprecated] Retrieves estimated departure and arrival airports from OpenSky.
        Now superseded by AdsbdbClient.get_flight_info.

        Args:
            icao24 (str): The unique ICAO 24-bit address.

        Returns:
            Tuple[str, str]: (Departure Airport ICAO, Arrival Airport ICAO).
        """
        url = f"{OPENSKY_BASE_URL}/flights/aircraft"
        end_time = int(time.time())
        start_time = end_time - 7200

        params = {"icao24": icao24, "begin": start_time, "end": end_time}

        try:
            response = self.session.get(url, params=params, timeout=5)
            if response.status_code == 200:
                flights = response.json()
                if flights:
                    latest = flights[-1]
                    dep = latest.get("estDepartureAirport") or "?"
                    arr = latest.get("estArrivalAirport") or "?"
                    return dep, arr
        except Exception:
            pass
        return "?", "?"
