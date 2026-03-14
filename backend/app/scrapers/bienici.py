"""
Scraper BienIci.com pour les ventes immobilières en Seine-Maritime (76) et Eure (27).
BienIci expose une API JSON accessible via Playwright (intercept réseau).
"""
import asyncio
import json
from typing import Optional, List
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper, PropertyData

SEARCH_URLS = {
    "76": "https://www.bienici.com/recherche/achat/seine-maritime-76",
    "27": "https://www.bienici.com/recherche/achat/eure-27",
}

MAX_ADS_PER_DEPT = 48  # 2 pages de 24


class BienIciScraper(BaseScraper):
    """Scrape les annonces immobilières de BienIci pour le 76 et le 27."""

    async def scrape(self) -> List[PropertyData]:
        results = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/127.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 800},
                    locale="fr-FR",
                )

                for dept, url in SEARCH_URLS.items():
                    dept_results = await self._scrape_department(context, url, dept)
                    results.extend(dept_results)
                    print(f"[BienIci] Dept {dept}: {len(dept_results)} annonces")
                    await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

                await browser.close()
        except Exception as e:
            print(f"[BienIci] Erreur globale: {e}")

        return results

    async def _scrape_department(
        self, context, url: str, dept: str
    ) -> List[PropertyData]:
        """Charge la page de recherche et intercepte l'API JSON."""
        captured_ads = []

        async def on_response(response):
            if "realEstateAds.json" in response.url and response.status == 200:
                try:
                    data = await response.json()
                    ads = data.get("realEstateAds", [])
                    captured_ads.extend(ads)
                except Exception:
                    pass

        page = await context.new_page()
        page.on("response", on_response)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(6)

            # Accepter les cookies si nécessaire
            try:
                await page.click("#didomi-notice-agree-button", timeout=3000)
                await asyncio.sleep(1)
            except Exception:
                pass

            # Scroller pour déclencher le chargement de plus d'annonces
            if len(captured_ads) < MAX_ADS_PER_DEPT:
                for _ in range(5):
                    await page.evaluate("window.scrollBy(0, 1000)")
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"[BienIci] Erreur chargement {url}: {e}")
        finally:
            await page.close()

        # Convertir les annonces JSON en PropertyData
        results = []
        for ad in captured_ads[:MAX_ADS_PER_DEPT]:
            prop = self._parse_ad(ad, dept)
            if prop:
                results.append(prop)

        return results

    @staticmethod
    def _first(val):
        """Extrait le premier élément si c'est une liste (programmes neufs BienIci)."""
        if isinstance(val, list):
            return val[0] if val else None
        return val

    def _parse_ad(self, ad: dict, dept: str) -> Optional[PropertyData]:
        """Convertit une annonce JSON BienIci en PropertyData."""
        prop = PropertyData()
        prop.source = "bienici"
        prop.department = dept

        # ID et URL
        ad_id = ad.get("id", "")
        prop.source_url = f"https://www.bienici.com/annonce/achat/{ad_id}"

        # Titre
        prop.title = ad.get("title", "Bien immobilier")

        # Champs numériques (peuvent être des listes [min, max] pour les programmes neufs)
        prop.price = self._first(ad.get("price"))
        prop.surface = self._first(ad.get("surfaceArea"))
        prop.exterior_surface = self._first(ad.get("landSurfaceArea"))
        prop.rooms = self._first(ad.get("roomsQuantity"))
        prop.bedrooms = self._first(ad.get("bedroomsQuantity"))

        # Localisation
        prop.city = ad.get("city")
        prop.postal_code = ad.get("postalCode")

        # Coordonnées GPS (BienIci fournit des coordonnées floutées)
        geo = ad.get("blurredGeoPoint") or {}
        if geo.get("lat") and geo.get("lng"):
            prop.latitude = geo["lat"]
            prop.longitude = geo["lng"]

        # Type de bien
        prop_type = ad.get("propertyType", "")
        type_map = {
            "flat": "Appartement",
            "house": "Maison",
            "parking": "Parking",
            "land": "Terrain",
            "shop": "Commerce",
            "office": "Bureau",
            "loft": "Loft",
            "building": "Immeuble",
            "castle": "Château",
        }
        prop.property_type = type_map.get(prop_type, prop_type.capitalize() if prop_type else None)

        # Description
        desc = ad.get("description", "")
        prop.description = desc[:2000] if desc else None

        # Photos
        photos = ad.get("photos", [])
        prop.images = [
            p.get("url", "") for p in photos[:8] if p.get("url")
        ]

        return prop if prop.title else None
