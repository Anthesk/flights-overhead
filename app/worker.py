import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.db_models import Flight
from app.services.tracker import FlightTracker
from app.config import WORKER_START_HOUR, WORKER_END_HOUR

# Ensure tables exist
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def update_flights(tracker: FlightTracker):
    """Fetches flights and syncs them with the database."""
    print(f"[{datetime.now()}] Starting update cycle...")

    # Get fresh data
    aircraft_list = tracker.get_flights()

    db = SessionLocal()
    try:
        current_time = datetime.utcnow()

        for aircraft in aircraft_list:
            # Check if exists
            db_flight = (
                db.query(Flight).filter(Flight.icao24 == aircraft.icao24).first()
            )

            if db_flight:
                # Update existing
                db_flight.last_seen = current_time
                db_flight.altitude = aircraft.altitude
                db_flight.velocity = aircraft.velocity
                db_flight.heading = aircraft.heading
                # Update details if they changed or were missing
                if aircraft.departure != "?":
                    db_flight.departure = aircraft.departure
                if aircraft.arrival != "?":
                    db_flight.arrival = aircraft.arrival
                if aircraft.airline:
                    db_flight.airline = aircraft.airline
                if aircraft.manufacturer != "N/A":
                    db_flight.manufacturer = aircraft.manufacturer
                if aircraft.model:
                    db_flight.model = aircraft.model
            else:
                # Insert new
                new_flight = Flight(
                    icao24=aircraft.icao24,
                    callsign=aircraft.callsign,
                    airline=aircraft.airline,
                    manufacturer=aircraft.manufacturer,
                    model=aircraft.model,
                    departure=aircraft.departure,
                    arrival=aircraft.arrival,
                    heading=aircraft.heading,
                    altitude=aircraft.altitude,
                    velocity=aircraft.velocity,
                    origin_country=aircraft.origin_country,
                    last_seen=current_time,
                    processed=False,
                )
                db.add(new_flight)

        db.commit()
        print(f"[{datetime.now()}] Synced {len(aircraft_list)} flights.")

    except Exception as e:
        print(f"Error in update cycle: {e}")
        db.rollback()
    finally:
        db.close()


def cleanup_stale_flights():
    """Removes flights that haven't been seen for > 15 minutes."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=15)
        deleted = db.query(Flight).filter(Flight.last_seen < cutoff).delete()
        db.commit()
        if deleted > 0:
            print(f"[{datetime.now()}] Cleaned up {deleted} stale flights.")
    except Exception as e:
        print(f"Error cleaning up: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    tracker = FlightTracker()

    while True:
        current_hour = datetime.now().hour
        if WORKER_START_HOUR <= current_hour < WORKER_END_HOUR:
            try:
                update_flights(tracker)
                cleanup_stale_flights()
            except Exception as e:
                print(f"Worker crashed: {e}")

            # Sleep 1 minute (60 seconds)
            print("Sleeping for 1 minute...")
        time.sleep(60)
