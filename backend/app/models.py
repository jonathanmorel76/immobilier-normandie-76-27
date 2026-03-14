from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    surface: Mapped[Optional[float]] = mapped_column(Float, nullable=True)         # m² habitables
    exterior_surface: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # m² extérieur
    rooms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)    # "76" | "27"
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    images: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)            # liste d'URLs
    source: Mapped[str] = mapped_column(String(50))                                # "leboncoin" | "pap"
    source_url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    property_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # maison, appartement...
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Transport (mis en cache lors du scraping)
    nearest_train_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nearest_train_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    nearest_bus_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nearest_bus_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    nearest_tram_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nearest_tram_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending|running|done|error
    source: Mapped[str] = mapped_column(String(50), default="all")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    properties_found: Mapped[int] = mapped_column(Integer, default=0)
    properties_new: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
