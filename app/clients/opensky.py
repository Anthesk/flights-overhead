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
        self.token = None
        self.token_expiry = 0
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
                expires_in = data.get("expires_in", 3600)
                if token:
                    self.token = token
                    # Set expiry time with a 60-second safety margin
                    self.token_expiry = time.time() + expires_in - 60
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                    print("Successfully authenticated with OpenSky.")
                else:
                    self.token = None
                    self.token_expiry = 0
                    print("OpenSky authentication failure: No access token in response.")
                    self.session.headers.pop("Authorization", None)
            else:
                self.token = None
                self.token_expiry = 0
                print(
                    f"WARNING: OpenSky API credentials are invalid (Status {response.status_code}). "
                    f"Falling back to anonymous mode with severely restricted rate limits. "
                    f"Error: {response.text}"
                )
                self.session.headers.pop("Authorization", None)
        except Exception as e:
            self.token = None
            self.token_expiry = 0
            print(f"OpenSky authentication error: {e}")
            self.session.headers.pop("Authorization", None)

    def _ensure_authenticated(self):
        """
        Ensures we have a valid auth token if credentials are provided.
        Re-authenticates if the token is close to expiry or not yet obtained.
        """
        if not self.client_id or not self.client_secret:
            return

        if not self.token or time.time() >= self.token_expiry:
            print("Token expired or missing. Re-authenticating with OpenSky...")
            self._authenticate()

    def get_states(self, bbox: Tuple[float, float, float, float]) -> List[Aircraft]:
        """
        Retrieves the state vectors of all aircraft within a bounding box.

        Args:
            bbox (Tuple[float, float, float, float]): Bounding box (min_lat, max_lat, min_lon, max_lon).

        Returns:
            List[Aircraft]: A list of Aircraft objects representing the flights in the area.
        """
        self._ensure_authenticated()
        url = f"{OPENSKY_BASE_URL}/states/all"
        params = {
            "lamin": bbox[0],
            "lamax": bbox[1],
            "lomin": bbox[2],
            "lomax": bbox[3],
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            
            # If we get a 401 Unauthorized and have credentials, our token might have expired.
            # We try to re-authenticate once and retry.
            if response.status_code == 401 and self.client_id and self.client_secret:
                print("OpenSky request returned 401 Unauthorized. Retrying authentication...")
                self.token = None
                self.token_expiry = 0
                self._ensure_authenticated()
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
