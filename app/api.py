from typing import List, Dict
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.db_models import Flight

app = FastAPI(title="Flights Overhead API")


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

        dep = flight.departure if flight.departure else "?"
        arr = flight.arrival if flight.arrival else "?"

        alt_str = f"{int(flight.altitude)}m" if flight.altitude is not None else "N/A"
        heading_val = f"{flight.heading}°" if flight.heading is not None else "N/A"

        # Conversions
        # 1 m/s = 1.94384 knots
        speed_knots = (
            int(flight.velocity * 1.94384) if flight.velocity is not None else 0
        )

        # Wikipedia Links (Best effort generation)
        wiki_model = "N/A"
        if airframe != "N/A":
            safe_model = airframe.replace(" ", "_")
            wiki_model = f"https://en.wikipedia.org/wiki/{safe_model}"

        wiki_airline = "N/A"
        if airline_str != "Unknown":
            safe_airline = airline_str.replace(" ", "_")
            wiki_airline = f"https://en.wikipedia.org/wiki/{safe_airline}"

        # Requested Format:
        # "Flight {flight number} from {departure} to {arrival}: {heading} at {altitude}, {speed} (knots).
        # {aircraft model} from {airline}
        # {link to wikipedia page of the aircraft model}
        # {link to wikipedia page of airline}"

        formatted_text = (
            f"Flight {callsign_str} from {dep} to {arr}: {heading_val} at {alt_str}, {speed_knots} (knots).\n"
            f"{airframe} from {airline_str}\n"
            f"{wiki_model}\n"
            f"{wiki_airline}"
        )

        results.append(
            {
                "icao24": flight.icao24,
                "text": formatted_text,
                "raw": {
                    "callsign": flight.callsign,
                    "airline": flight.airline,
                    "route": f"{dep} -> {arr}",
                    "speed_knots": speed_knots,
                    "wiki_model": wiki_model,
                    "wiki_airline": wiki_airline,
                },
            }
        )

        # 3. Mark as processed
        flight.processed = True

    # 4. Commit changes
    db.commit()

    return {"count": len(results), "flights": results}
