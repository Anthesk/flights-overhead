from typing import List, Dict
from functools import lru_cache
import requests
import airportsdata
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.db_models import Flight

app = FastAPI(title="Flights Overhead API")

# Load Airport Data (ICAO keys)
airports = airportsdata.load("ICAO")


def get_airport_details(icao_code: str) -> str:
    """Returns 'City (Name)' or just the code if not found."""
    if not icao_code or icao_code == "?" or icao_code == "N/A":
        return "?"

    apr = airports.get(icao_code)
    if apr:
        # e.g. "Paris (Charles de Gaulle International Airport)"
        return f"{apr['city']} ({apr['name']})"
    return icao_code


@lru_cache(maxsize=1024)
def get_wiki_url(query: str) -> str:
    """
    Searches Wikipedia for the best matching article.
    Uses Opensearch first, then full-text search.
    Falls back to a search result page URL.
    Results are cached to improve performance.
    """
    if not query or query == "N/A" or query == "Unknown":
        return "N/A"

    session = requests.Session()
    session.headers.update({"User-Agent": "FlightsOverhead/1.0"})

    # 1. Try Opensearch (Good for direct hits/redirects)
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": query,
            "limit": 1,
            "namespace": 0,
            "format": "json",
        }
        res = session.get(url, params=params, timeout=2)
        if res.status_code == 200:
            data = res.json()
            # data content: [query, [titles], [descriptions], [urls]]
            if data[3]:
                return data[3][0]  # Return the direct URL
    except Exception:
        pass

    # 2. Try Standard Search (Good for "Embraer EMB-175" -> "Embraer E-Jet family")
    try:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 1,
            "format": "json",
        }
        res = session.get(url, params=params, timeout=2)
        if res.status_code == 200:
            data = res.json()
            if data["query"]["search"]:
                title = data["query"]["search"][0]["title"]
                safe_title = title.replace(" ", "_")
                return f"https://en.wikipedia.org/wiki/{safe_title}"
    except Exception:
        pass

    # 3. Fallback to Search Page
    safe_query = query.replace(" ", "+")
    return f"https://en.wikipedia.org/w/index.php?search={safe_query}"


@app.get("/flights")
def get_new_flights(db: Session = Depends(get_db)):
    """
    Retrieves flights that have not been processed yet.
    Marks them as processed immediately after retrieval.
    """
    # 1. Query pending flights
    flights = db.query(Flight).filter(Flight.processed == False).all()

    results = []

    for flight in flights:
        # 2. Format output
        # Handle N/A logic
        callsign_str = flight.callsign if flight.callsign else "N/A"
        airline_str = flight.airline if flight.airline else "Unknown"

        man = flight.manufacturer if flight.manufacturer else "N/A"
        mod = flight.model if flight.model else ""
        airframe = f"{man} {mod}".strip()
        if not airframe:
            airframe = "N/A"

        # Airport Lookup
        dep_code = flight.departure if flight.departure else "?"
        arr_code = flight.arrival if flight.arrival else "?"

        dep_str = get_airport_details(dep_code)
        arr_str = get_airport_details(arr_code)

        # 1 m = 3.28084 ft
        alt_str = (
            f"{int(flight.altitude * 3.28084):,}ft"
            if flight.altitude is not None
            else "N/A"
        )
        heading_val = f"{int(flight.heading)}°" if flight.heading is not None else "N/A"
        # 1 m/s = 1.94384 knots
        speed_knots = (
            int(flight.velocity * 1.94384) if flight.velocity is not None else 0
        )

        # Wikipedia Links (Smart Lookup)
        wiki_model = "N/A"
        if airframe != "N/A":
            wiki_model = get_wiki_url(airframe)

        wiki_airline = "N/A"
        if airline_str != "Unknown":
            wiki_airline = get_wiki_url(airline_str)

        # FlightRadar24 Link
        fr24_link = "N/A"
        if callsign_str != "N/A":
            fr24_link = f"https://www.flightradar24.com/{callsign_str}"

        # Requested Format
        message_text = (
            f"➖➖➖➖➖➖➖➖➖➖\n"
            f"✈️ [{callsign_str}](<{fr24_link}>) ✈️\n"
            f"➖➖➖➖➖➖➖➖➖➖\n"
            f"🛫 {dep_code} ➡️ 🛬 {arr_code}\n"
            f"🧭 {heading_val} | 📏 {alt_str} | 💨 {speed_knots}kts\n"
            f"➖➖➖➖➖➖➖➖➖➖\n"
            f"🛩️  [{airframe}](<{wiki_model}>)\n"
            f"🏢  [{airline_str}](<{wiki_airline}>)\n"
            f"🌍 From: {dep_str}\n"
            f"📍 To:   {arr_str}"
        )
        results.append(
            {
                "icao24": flight.icao24,
                "message": message_text,
                "aircraft_wiki": wiki_model,
                "airline_wiki": wiki_airline,
                "flight_radar_link": fr24_link,
            }
        )

        # 3. Mark as processed
        flight.processed = True

    # 4. Commit changes
    db.commit()

    return {"count": len(results), "flights": results}
