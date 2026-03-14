"""Classe de base pour tous les scrapers immobiliers."""
import asyncio
import re
from abc import ABC, abstractmethod
from typing import Optional, List


class PropertyData:
    """Données brutes extraites d'une annonce."""

    def __init__(self):
        self.title: Optional[str] = None
        self.price: Optional[float] = None
        self.surface: Optional[float] = None
        self.exterior_surface: Optional[float] = None
        self.rooms: Optional[int] = None
        self.bedrooms: Optional[int] = None
        self.address: Optional[str] = None
        self.city: Optional[str] = None
        self.postal_code: Optional[str] = None
        self.department: Optional[str] = None
        self.latitude: Optional[float] = None
        self.longitude: Optional[float] = None
        self.description: Optional[str] = None
        self.images: List[str] = []
        self.source: str = ""
        self.source_url: str = ""
        self.property_type: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "price": self.price,
            "surface": self.surface,
            "exterior_surface": self.exterior_surface,
            "rooms": self.rooms,
            "bedrooms": self.bedrooms,
            "address": self.address,
            "city": self.city,
            "postal_code": self.postal_code,
            "department": self.department,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "description": self.description,
            "images": self.images,
            "source": self.source,
            "source_url": self.source_url,
            "property_type": self.property_type,
        }


class BaseScraper(ABC):
    """Interface abstraite pour les scrapers."""

    DELAY_BETWEEN_REQUESTS = 3.0  # secondes entre requêtes

    @abstractmethod
    async def scrape(self) -> List[PropertyData]:
        """Lance le scraping et retourne la liste des biens trouvés."""
        ...

    @staticmethod
    def parse_price(text: str) -> Optional[float]:
        """Extrait un prix depuis une chaîne comme '245 000 €'."""
        if not text:
            return None
        cleaned = re.sub(r"[^\d]", "", text)
        return float(cleaned) if cleaned else None

    @staticmethod
    def parse_surface(text: str) -> Optional[float]:
        """Extrait une surface depuis '85 m²' ou '85m²'."""
        if not text:
            return None
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*m", text)
        if match:
            return float(match.group(1).replace(",", "."))
        return None

    @staticmethod
    def extract_department(postal_code: str) -> Optional[str]:
        """Extrait le numéro de département depuis un code postal."""
        if postal_code and len(postal_code) >= 2:
            dept = postal_code[:2]
            if dept in ("76", "27"):
                return dept
        return None

    @staticmethod
    def extract_postal_code(text: str) -> Optional[str]:
        """Extrait un code postal français depuis un texte."""
        match = re.search(r"\b(76|27)\d{3}\b", text)
        return match.group(0) if match else None
