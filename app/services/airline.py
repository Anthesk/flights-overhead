from typing import Dict


class AirlineLookup:
    """Handles airline name resolution."""

    AIRLINES: Dict[str, str] = {
        "AFR": "Air France",
        "BAW": "British Airways",
        "DLH": "Lufthansa",
        "EZY": "EasyJet",
        "RYR": "Ryanair",
        "KLM": "KLM Royal Dutch Airlines",
        "IBE": "Iberia",
        "VLG": "Vueling",
        "TAP": "TAP Air Portugal",
        "SWR": "Swiss International Air Lines",
        "AZA": "Alitalia (ITA Airways)",
        "UAE": "Emirates",
        "QTR": "Qatar Airways",
        "DAL": "Delta Air Lines",
        "UAL": "United Airlines",
        "AAL": "American Airlines",
        "WZZ": "Wizz Air",
        "TUI": "TUI fly",
        "TVF": "Transavia",
        "BEL": "Brussels Airlines",
    }

    @classmethod
    def get_name(cls, callsign: str) -> str:
        """
        Resolves the airline name from a callsign using a static dictionary.

        Args:
            callsign (str): The flight callsign (e.g. "AFR123").

        Returns:
            str: The full airline name or "Inconnu" / "Unknown (XYZ)".
        """
        if not callsign or len(callsign) < 3:
            return "Inconnu"
        prefix = callsign[:3].upper()
        return cls.AIRLINES.get(prefix, f"Unknown ({prefix})")
