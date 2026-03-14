"""
Scraper immobilier.notaires.fr pour les ventes immobilières en Seine-Maritime (76) et Eure (27).
Utilise Playwright pour intercepter l'API JSON paginée.
Source officielle des notaires de France - très fiable.
"""
import asyncio
import json
from typing import Optional, List
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper, PropertyData

SEARCH_URLS = {
    "76": "https://www.immobilier.notaires.fr/fr/annonces-immobilieres?typeTransaction=VENTE&departement=76",
    "27": "https://www.immobilier.notaires.fr/fr/annonces-immobilieres?typeTransaction=VENTE&departement=27",
}

MAX_PAGES = 5  # 12 annonces par page = 60 par département max
BASE_URL = "https://www.immobilier.notaires.fr"

TYPE_MAP = {
    "APP": "Appartement",
    "MAI": "Maison",
    "TER": "Terrain",
    "IMM": "Immeuble",
    "GAR": "Parking",
    "FON": "Commerce",
    "LOC": "Local",
    "AGR": "Bien agricole",
    "VIT": "Bien viticole",
}


class NotairesScraper(BaseScraper):
    """Scrape les annonces immobilières de immobilier.notaires.fr pour le 76 et le 27."""

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
                    print(f"[Notaires] Dept {dept}: {len(dept_results)} annonces")
                    await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

                await browser.close()
        except Exception as e:
            print(f"[Notaires] Erreur globale: {e}")

        return results

    async def _scrape_department(
        self, context, url: str, dept: str
    ) -> List[PropertyData]:
        """Charge la page et intercepte les réponses API JSON paginées."""
        all_ads = []

        for page_num in range(1, MAX_PAGES + 1):
            captured_ads = []

            async def on_response(response):
                if "annonces?offset" in response.url and response.status == 200:
                    try:
                        data = await response.json()
                        ads = data.get("annonceResumeDto", [])
                        captured_ads.extend(ads)
                    except Exception:
                        pass

            page = await context.new_page()
            page.on("response", on_response)

            try:
                page_url = url if page_num == 1 else f"{url}&page={page_num}"
                await page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(5)

                # Accepter cookies
                if page_num == 1:
                    for sel in [
                        "#didomi-notice-agree-button",
                        "#tarteaucitronPersonalize2",
                        "button[class*='accept']",
                    ]:
                        try:
                            await page.click(sel, timeout=2000)
                            await asyncio.sleep(1)
                            break
                        except Exception:
                            continue

                print(
                    f"[Notaires] Page {page_num} dept {dept}: "
                    f"{len(captured_ads)} annonces interceptées"
                )

                all_ads.extend(captured_ads)

                if not captured_ads:
                    await page.close()
                    break

            except Exception as e:
                print(f"[Notaires] Erreur page {page_num} dept {dept}: {e}")
            finally:
                await page.close()

            await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

        # Convertir en PropertyData
        results = []
        for ad in all_ads:
            prop = self._parse_ad(ad, dept)
            if prop:
                results.append(prop)

        return results

    def _parse_ad(self, ad: dict, dept: str) -> Optional[PropertyData]:
        """Convertit une annonce JSON des Notaires en PropertyData."""
        prop = PropertyData()
        prop.source = "notaires"
        prop.department = dept

        # URL
        prop.source_url = ad.get("urlDetailAnnonceFr", "")
        if not prop.source_url:
            annonce_id = ad.get("annonceId", "")
            prop.source_url = f"{BASE_URL}/fr/annonce-immo/vente/{annonce_id}"

        # Prix (prixTotal inclut les frais notaire, prixAffiche = hors frais)
        prop.price = ad.get("prixAffiche") or ad.get("prixTotal")

        # Surface
        prop.surface = ad.get("surface")

        # Pièces
        prop.rooms = ad.get("nbPieces")

        # Chambres
        prop.bedrooms = ad.get("nbChambres")

        # Localisation
        prop.city = ad.get("communeNom") or ad.get("localiteNom")
        prop.postal_code = ad.get("codePostal")

        # Type de bien
        type_code = ad.get("typeBien", "")
        prop.property_type = TYPE_MAP.get(type_code, type_code)

        # Description
        desc = ad.get("descriptionFr", "")
        prop.description = desc[:2000] if desc else None

        # Surface terrain
        surface_terrain = ad.get("surfaceTerrain")
        if surface_terrain:
            prop.exterior_surface = surface_terrain

        # Photos
        photo_url = ad.get("urlPhotoPrincipale", "")
        if photo_url:
            prop.images = [photo_url]

        # Titre
        parts = []
        if prop.property_type:
            parts.append(prop.property_type)
        if prop.rooms:
            parts.append(f"{prop.rooms} pièces")
        if prop.surface:
            parts.append(f"{prop.surface:.0f} m²")
        if prop.city:
            parts.append(prop.city)
        prop.title = " - ".join(parts) if parts else ad.get("descriptionFr", "Bien immobilier")

        return prop if prop.title else None
