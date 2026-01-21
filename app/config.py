import os

# Bounding box
LAT_MIN = float(os.getenv("FLIGHTS_LAT_MIN", 49))
LAT_MAX = float(os.getenv("FLIGHTS_LAT_MAX", 51))
LON_MIN = float(os.getenv("FLIGHTS_LON_MIN", 2.5))
LON_MAX = float(os.getenv("FLIGHTS_LON_MAX", 3.5))

# API Urls
OPENSKY_BASE_URL = "https://opensky-network.org/api"
OPENSKY_AUTH_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
ADSBDB_BASE_URL = "https://api.adsbdb.com/v0"
