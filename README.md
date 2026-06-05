# Flights Overhead

A flight tracking system that monitors aircraft in a specific bounding box and serves fresh flight data via a REST API. It uses OpenSky Network and ADSBDB for data enrichment.

You can then connect its API to a Discord bot for example, and get info about all the flights passing over your house, quasi-live !

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

You will need a personal access token from Github (PAT).

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

### Option C: Deployment

1.  **GitHub Action**: Pushing a semver tag `v*.*` will automatically trigger a build of the Docker image.
2.  **Setup**: Copy [docker-compose.yaml](docker-compose.yaml) and [deploy.sh](deploy.sh).
3.  **Secrets**: Replace users and passwords in the [docker-compose.yaml](docker-compose.yaml) file with new values.
4.  **Configuration**: See [Configuration](#%EF%B8%8F-configuration).
5.  **Deployment**:
    Run the deployment script:
    ```bash
    ./deploy.sh
    ```
    This script will pull the latest images, rebuild the containers, and restart the services.

## ⚙️ Configuration

Create a `.env` file in the root directory:

```ini
# OpenSky Credentials (Optional but recommended for better rate limits)
OPENSKY_CLIENT_ID=your_username
OPENSKY_CLIENT_SECRET=your_password

# Bounding Box (Optional - Defaults to Paris area)
FLIGHTS_LAT_MIN=49
FLIGHTS_LAT_MAX=51
FLIGHTS_LON_MIN=2.5
FLIGHTS_LON_MAX=3.5

# Worker Configuration (Optional)
WORKER_START_HOUR=7        # Worker starts at 7 AM
WORKER_END_HOUR=23         # Worker stops at 11 PM
WORKER_FREQUENCY=60        # Worker runs every 60 seconds
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
      "message": "➖➖➖➖➖➖➖➖➖➖\n✈️ [RYR767Z](<https://www.flightradar24.com/RYR767Z>) ✈️\n➖➖➖➖➖➖➖➖➖➖\n🛫 EGSS ➡️ 🛬 LIRA\n🧭 135° | 📏 32,000ft | 💨 450kts\n➖➖➖➖➖➖➖➖➖➖\n🛩️  [Boeing 737-800](<https://en.wikipedia.org/wiki/Boeing_737>)\n🏢  [Ryanair](<https://en.wikipedia.org/wiki/Ryanair>)\n🌍 From: London (Stansted Airport)\n📍 To:   Rome (Ciampino–G. B. Pastine International Airport)",
      "aircraft_wiki": "https://en.wikipedia.org/wiki/Boeing_737",
      "airline_wiki": "https://en.wikipedia.org/wiki/Ryanair",
      "flight_radar_link": "https://www.flightradar24.com/RYR767Z"
    }
  ]
}
```

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
