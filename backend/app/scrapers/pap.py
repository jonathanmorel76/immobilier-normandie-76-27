"""
Scraper PAP.fr pour les ventes immobilières en Seine-Maritime (76) et Eure (27).
PAP est moins protégé contre le scraping → httpx + BeautifulSoup.
"""
import asyncio
import re
from typing import Optional, List, Tuple
import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, PropertyData

# Codes géo PAP.fr (trouvés via /json/ac-geo)
SEARCH_URLS = {
    "76": "https://www.pap.fr/annonce/ventes-immobilieres-seine-maritime-g440",
    "27": "https://www.pap.fr/annonce/ventes-immobilieres-eure-g391",
}

BASE_URL = "https://www.pap.fr"
MAX_PAGES = 3
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class PapScraper(BaseScraper):
    """Scrape les annonces immobilières de PAP.fr pour le 76 et le 27."""

    async def scrape(self) -> List[PropertyData]:
        results = []
        async with httpx.AsyncClient(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            for dept, url in SEARCH_URLS.items():
                dept_results = await self._scrape_department(client, url, dept)
                results.extend(dept_results)
                await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)
        return results

    async def _scrape_department(
        self, client: httpx.AsyncClient, base_url: str, dept: str
    ) -> List[PropertyData]:
        results = []
        for page_num in range(1, MAX_PAGES + 1):
            url = base_url if page_num == 1 else f"{base_url}?page={page_num}"
            try:
                resp = await client.get(url)
                print(f"[PAP] Fetched {url} -> status {resp.status_code}")
                resp.raise_for_status()
                listings = self._parse_listing_page(resp.text, dept)
                print(f"[PAP] Page {page_num} dept {dept}: {len(listings)} annonces")
            except Exception as e:
                print(f"[PAP] Erreur page {page_num} dept {dept}: {e}")
                break

            if not listings:
                break

            for prop in listings:
                results.append(prop)

            await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

        return results

    def _parse_listing_page(self, html: str, dept: str) -> List[PropertyData]:
        """Extrait les annonces depuis la page de résultats."""
        soup = BeautifulSoup(html, "html.parser")
        results = []

        for item in soup.select(".search-list-item-alt"):
            try:
                prop = self._parse_item(item, dept)
                if prop and prop.title:
                    results.append(prop)
            except Exception as e:
                print(f"[PAP] Erreur parsing item: {e}")

        return results

    def _parse_item(self, item, dept: str) -> Optional[PropertyData]:
        """Parse un élément de la liste de résultats."""
        # Lien vers l'annonce
        link_el = item.select_one("a.item-thumb-link, a.item-title")
        if not link_el:
            return None
        href = link_el.get("href", "")
        if not href or "/annonces/" not in href:
            return None

        full_url = BASE_URL + href if href.startswith("/") else href

        prop = PropertyData()
        prop.source = "pap"
        prop.source_url = full_url
        prop.department = dept

        # Extraire le type de bien et la ville depuis l'URL
        # ex: /annonces/maison-bonsecours-76240-r459902609
        url_match = re.search(r"/annonces/([a-z\-]+?)-(\d{5})-r\d+", href)
        if url_match:
            slug = url_match.group(1)
            postal = url_match.group(2)
            parts = slug.split("-")
            prop.property_type = parts[0].capitalize() if parts else None
            # Ville = tout sauf le type de bien
            if len(parts) > 1:
                prop.city = " ".join(p.capitalize() for p in parts[1:])
            prop.postal_code = postal
        else:
            # Essayer sans code postal: /annonces/maison-saint-marcel-r459501250
            url_match2 = re.search(r"/annonces/([a-z\-]+?)-r\d+", href)
            if url_match2:
                slug = url_match2.group(1)
                parts = slug.split("-")
                prop.property_type = parts[0].capitalize() if parts else None
                if len(parts) > 1:
                    prop.city = " ".join(p.capitalize() for p in parts[1:])

        # Prix
        price_el = item.select_one(".item-price")
        if price_el:
            prop.price = self.parse_price(price_el.get_text())

        # Localisation (ville + code postal depuis le texte de l'annonce)
        body_el = item.select_one(".item-body, .item-title")
        if body_el:
            body_text = body_el.get_text(" ", strip=True)
            # Chercher pattern "Ville (XXXXX)" ou "VILLE (XXXXX)"
            loc_match = re.search(r"([\wÀ-ÿ\-]+(?:\s[\wÀ-ÿ\-]+)*)\s*\((\d{5})\)", body_text)
            if loc_match:
                prop.city = loc_match.group(1).strip()
                prop.postal_code = loc_match.group(2)

        # Tags (pièces, chambres, surface, terrain)
        for tag in item.select(".item-tags li"):
            text = tag.get_text(strip=True).lower()
            if "pièce" in text:
                m = re.search(r"(\d+)", text)
                if m:
                    prop.rooms = int(m.group(1))
            elif "chambre" in text:
                m = re.search(r"(\d+)", text)
                if m:
                    prop.bedrooms = int(m.group(1))
            elif "terrain" in text:
                prop.exterior_surface = self.parse_surface(text)
            elif "m²" in text and "terrain" not in text:
                prop.surface = self.parse_surface(text)

        # Description
        desc_el = item.select_one(".item-description")
        if desc_el:
            prop.description = desc_el.get_text(strip=True)[:2000]

        # Titre composé
        parts = []
        if prop.property_type:
            parts.append(prop.property_type)
        if prop.surface:
            parts.append(f"{prop.surface:.0f} m²")
        if prop.city:
            parts.append(prop.city)
        prop.title = " - ".join(parts) if parts else "Bien immobilier"

        return prop
