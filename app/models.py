from dataclasses import dataclass, field
from typing import Optional
from app.services.airline import AirlineLookup


@dataclass
class Aircraft:
    """Represents an aircraft state."""

    icao24: str
    callsign: str
    origin_country: str
    altitude: Optional[float]
    velocity: Optional[float]
    heading: Optional[float]

    # Enriched data
    airline: str = field(init=False)
    manufacturer: str = "N/A"
    model: str = ""
    departure: str = "?"
    arrival: str = "?"

    def __post_init__(self):
        """Initializes the airline name based on the callsign after object creation."""
        self.airline = AirlineLookup.get_name(self.callsign)

    @property
    def airframe(self) -> str:
        """
        Constructs a human-readable airframe string.

        Returns:
             str: "Manufacturer Model" or "N/A" if unknown.
        """
        if self.manufacturer == "N/A" and not self.model:
            return "N/A"
        return f"{self.manufacturer} {self.model}".strip()

    def __str__(self) -> str:
        """
        Returns a formatted string representation of the flight info (Card view).
        """
        callsign_str = self.callsign if self.callsign else "N/A"
        alt_str = f"{int(self.altitude)}m" if self.altitude is not None else "N/A"
        vel_str = (
            f"{int(self.velocity * 3.6)} km/h" if self.velocity is not None else "N/A"
        )
        heading_str = f"{self.heading}°" if self.heading is not None else "N/A"

        return (
            f"✈️  Vol: {callsign_str} ({self.airline})\n"
            f"    Avion: {self.airframe} [ICAO: {self.icao24}]\n"
            f"    Route: {self.departure} -> {self.arrival}\n"
            f"    Cap: {heading_str} | Alt: {alt_str} | Vit: {vel_str}\n"
            f"    Pays: {self.origin_country}\n"
            f"{'-' * 40}"
        )
