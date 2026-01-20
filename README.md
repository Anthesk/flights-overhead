# Flights Overhead

A specialized flight tracking system that monitors aircraft in a specific bounding box and serves fresh flight data via a REST API. It uses OpenSky Network and ADSBDB for data enrichment.

## 🚀 Features

- **Real-time Monitoring**: Tracks aircraft within a configurable geographical zone.
- **Data Enrichment**:
  - **Manufacturer/Model**: Identifies aircraft types.
  - **Routes**: Retrieves Departure and Arrival airports.
  - **Airlines**: Resolves airline names from callsigns.
- **Smart Sync**: Only serves "new" flights via API. Once a flight is consumed by the client, it is marked as processed.
- **Auto-Cleanup**: Automatically removes flights that have left the zone.
- **Dockerized**: Ready for deployment with Docker Compose (PostgreSQL included).

## 🏗 Architecture

The system consists of two main components running in parallel:

1.  **Background Worker** (`app/worker.py`):
    - Polls OpenSky API every 10 minutes.
    - Enriches data using ADSBDB.
    - Updates the database (inserts new flights, updates positions).
    - Cleans up stale flights (older than 15 mins).

2.  **API Server** (`app/api.py`):
    - Exposes a `GET /flights` endpoint.
    - Returns flights that haven't been sent yet.
    - Marks returned flights as `processed`.

## 🛠️ Installation

### Option A: Docker (Recommended)

1.  **Clone the repository**
2.  **Configure Environment**
    Create a `.env` file (see Configuration section).
3.  **Run with Docker Compose**
    ```bash
    docker-compose up --build -d
    ```
    This starts the API, Worker, and a PostgreSQL database.

### Option B: Local Setup

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configure Environment**
    Create a `.env` file.
3.  **Run the Worker**
    ```bash
    python3 -m app.worker
    ```
4.  **Run the API** (in a separate terminal)
    ```bash
    uvicorn app.api:app --reload
    ```

## ⚙️ Configuration

Create a `.env` file in the root directory:

```ini
# OpenSky Credentials (Optional but recommended for better rate limits)
OPENSKY_CLIENT_ID=your_username
OPENSKY_CLIENT_SECRET=your_password

# Database URL
# For Docker: postgresql://user:password@db:5432/flights
# For Local: sqlite:///flights.db
DATABASE_URL=sqlite:///flights.db
```

## 📡 Usage

### Get New Flights

**Endpoint**: `GET /flights`

Returns a list of aircraft currently in the zone that haven't been fetched before.

```bash
curl http://localhost:8000/flights
```

**Response Example:**

```json
{
  "count": 1,
  "flights": [
    {
      "icao24": "4d2288",
      "text": "✈️  Vol: RYR767Z (Ryanair)\n    Avion: Boeing 737NG 8AS/W...\n...",
      "raw": {
        "callsign": "RYR767Z",
        "airline": "Ryanair",
        "route": "EGSS -> LIRA"
      }
    }
  ]
}
```

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
