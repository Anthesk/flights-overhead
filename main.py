from dotenv import load_dotenv
from app.services.tracker import FlightTracker

if __name__ == "__main__":
    # Load .env file using python-dotenv
    load_dotenv()

    # Run application
    app = FlightTracker()
    app.run()
