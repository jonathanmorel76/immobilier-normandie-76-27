"""
Module de calcul de proximité aux transports en commun.
Utilise l'API Overpass (OpenStreetMap) pour trouver les arrêts proches,
puis calcule le temps de marche à pied (5 km/h ≈ 83 m/min).
"""
import math
import asyncio
import httpx
from typing import Optional, Tuple

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
WALKING_SPEED_M_PER_MIN = 83.0  # 5 km/h en m/min
SEARCH_RADIUS_M = 5000           # 5 km de rayon max


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Retourne la distance en mètres entre deux coordonnées GPS."""
    R = 6371000  # rayon Terre en mètres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def distance_to_walk_minutes(distance_m: float) -> float:
    """Convertit une distance en mètres en minutes de marche."""
    return round(distance_m / WALKING_SPEED_M_PER_MIN, 1)


async def find_nearest_transport(lat: float, lon: float) -> dict:
    """
    Interroge l'API Overpass pour trouver les arrêts de transport
    les plus proches d'une position donnée.

    Retourne un dict avec nearest_train_*, nearest_bus_*, nearest_tram_*
    """
    query = f"""
    [out:json][timeout:15];
    (
      node["railway"="station"](around:{SEARCH_RADIUS_M},{lat},{lon});
      node["railway"="halt"](around:{SEARCH_RADIUS_M},{lat},{lon});
      node["highway"="bus_stop"](around:{SEARCH_RADIUS_M},{lat},{lon});
      node["railway"="tram_stop"](around:{SEARCH_RADIUS_M},{lat},{lon});
    );
    out body;
    """

    result = {
        "nearest_train_min": None,
        "nearest_train_name": None,
        "nearest_bus_min": None,
        "nearest_bus_name": None,
        "nearest_tram_min": None,
        "nearest_tram_name": None,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return result

    elements = data.get("elements", [])

    trains = []
    buses = []
    trams = []

    for el in elements:
        node_lat = el.get("lat")
        node_lon = el.get("lon")
        if node_lat is None or node_lon is None:
            continue

        tags = el.get("tags", {})
        name = tags.get("name", tags.get("ref", "Arrêt inconnu"))
        dist = haversine_distance(lat, lon, node_lat, node_lon)

        railway = tags.get("railway", "")
        highway = tags.get("highway", "")

        if railway in ("station", "halt"):
            trains.append((dist, name))
        elif highway == "bus_stop":
            buses.append((dist, name))
        elif railway == "tram_stop":
            trams.append((dist, name))

    if trains:
        trains.sort()
        result["nearest_train_min"] = distance_to_walk_minutes(trains[0][0])
        result["nearest_train_name"] = trains[0][1]

    if buses:
        buses.sort()
        result["nearest_bus_min"] = distance_to_walk_minutes(buses[0][0])
        result["nearest_bus_name"] = buses[0][1]

    if trams:
        trams.sort()
        result["nearest_tram_min"] = distance_to_walk_minutes(trams[0][0])
        result["nearest_tram_name"] = trams[0][1]

    return result


async def geocode_city(city: str, postal_code: Optional[str] = None) -> Optional[Tuple[float, float]]:
    """Geocode une ville via Nominatim (OSM). Retourne (lat, lon) ou None."""
    query = city
    if postal_code:
        query = f"{postal_code} {city}, France"
    else:
        query = f"{city}, Normandie, France"

    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": "ImmobilierNormandie/1.0"},
            timeout=10.0,
        ) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "json", "limit": 1},
            )
            resp.raise_for_status()
            results = resp.json()
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass
    return None
