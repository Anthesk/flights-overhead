from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime
from app.database import Base


class Flight(Base):
    """
    SQLAlchemy model for storing flight data.
    """

    __tablename__ = "flights"

    icao24 = Column(String, primary_key=True, index=True)
    callsign = Column(String)
    airline = Column(String)
    manufacturer = Column(String)
    model = Column(String)
    departure = Column(String)
    arrival = Column(String)
    heading = Column(Float)
    altitude = Column(Float)
    velocity = Column(Float)
    origin_country = Column(String)

    # Internal tracking
    last_seen = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
