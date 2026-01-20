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
        # 2. Format output (recreating the style from models.py)
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
        vel_str = (
            f"{int(flight.velocity * 3.6)} km/h"
            if flight.velocity is not None
            else "N/A"
        )
        heading_str = f"{flight.heading}°" if flight.heading is not None else "N/A"

        formatted_text = (
            f"✈️  Vol: {callsign_str} ({airline_str})\n"
            f"    Avion: {airframe} [ICAO: {flight.icao24}]\n"
            f"    Route: {dep} -> {arr}\n"
            f"    Cap: {heading_str} | Alt: {alt_str} | Vit: {vel_str}\n"
            f"    Pays: {flight.origin_country}\n"
            f"{'-' * 40}"
        )

        results.append(
            {
                "icao24": flight.icao24,
                "text": formatted_text,
                "raw": {
                    "callsign": flight.callsign,
                    "airline": flight.airline,
                    "route": f"{dep} -> {arr}",
                },
            }
        )

        # 3. Mark as processed
        flight.processed = True

    # 4. Commit changes
    db.commit()

    return {"count": len(results), "flights": results}
