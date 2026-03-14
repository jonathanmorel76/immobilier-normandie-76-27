"""
Scraper ParuVendu.fr pour les ventes immobilières en Seine-Maritime (76) et Eure (27).
Utilise Playwright pour charger les pages et parser le DOM.
"""
import asyncio
import re
from typing import Optional, List
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper, PropertyData

SEARCH_URLS = {
    "76": "https://www.paruvendu.fr/immobilier/vente/seine-maritime-76/",
    "27": "https://www.paruvendu.fr/immobilier/vente/eure-27/",
}

MAX_PAGES = 3
BASE_URL = "https://www.paruvendu.fr"


class ParuVenduScraper(BaseScraper):
    """Scrape les annonces immobilières de ParuVendu pour le 76 et le 27."""

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
                    print(f"[ParuVendu] Dept {dept}: {len(dept_results)} annonces")
                    await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

                await browser.close()
        except Exception as e:
            print(f"[ParuVendu] Erreur globale: {e}")

        return results

    async def _scrape_department(
        self, context, base_url: str, dept: str
    ) -> List[PropertyData]:
        results = []

        for page_num in range(1, MAX_PAGES + 1):
            url = base_url if page_num == 1 else f"{base_url}?p={page_num}"
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(4)

                # Accepter cookies ParuVendu
                try:
                    await page.evaluate("cmp_pv.cookie.saveConsent(true)")
                    await asyncio.sleep(1)
                except Exception:
                    pass

                # Extraire les annonces depuis les .blocAnnonce
                listings = await page.evaluate("""() => {
                    const blocs = document.querySelectorAll('.blocAnnonce');
                    return Array.from(blocs).map(bloc => {
                        const data = {};

                        // Liens (le 3e lien contient souvent type + surface + ville)
                        const links = bloc.querySelectorAll('a');
                        const allLinks = Array.from(links).map(a => ({
                            href: a.href,
                            text: a.textContent.trim()
                        }));
                        data.links = allLinks;

                        // URL de l'annonce (premier lien vers une page détail)
                        for (const link of allLinks) {
                            if (link.href.includes('/immobilier/vente/') && link.href.match(/[A-Z0-9]{10,}/)) {
                                data.url = link.href;
                                break;
                            }
                        }

                        // Texte complet pour parsing
                        data.fullText = bloc.innerText;

                        return data;
                    });
                }""")

                print(f"[ParuVendu] Page {page_num} dept {dept}: {len(listings)} annonces")

                for item in listings:
                    prop = self._parse_item(item, dept)
                    if prop and prop.title:
                        results.append(prop)

            except Exception as e:
                print(f"[ParuVendu] Erreur page {page_num} dept {dept}: {e}")
            finally:
                await page.close()

            await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

        return results

    def _parse_item(self, item: dict, dept: str) -> Optional[PropertyData]:
        """Parse un élément blocAnnonce."""
        prop = PropertyData()
        prop.source = "paruvendu"
        prop.department = dept

        # URL
        prop.source_url = item.get("url", "")
        if not prop.source_url:
            return None

        text = item.get("fullText", "")
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # Prix — pattern "128 000 €" ou "128 000 € *"
        # Attention : le nombre de photos apparaît sur une ligne séparée juste avant
        # On cherche un prix réaliste (> 10 000€)
        for line in lines:
            if "€" in line:
                cleaned = re.sub(r"[^\d\s]", "", line.split("€")[0])
                val = self.parse_price(cleaned)
                if val and val > 10000:
                    prop.price = val
                    break

        # Type de bien + surface + ville
        # Pattern typique dans les liens : "Appartement\n52 m2\nMont-Saint-Aignan (76)"
        for link_data in item.get("links", []):
            link_text = link_data.get("text", "")
            # Pattern: "Type\nSurface m2\nVille (dept)"
            type_match = re.match(
                r"(Appartement|Maison|Terrain|Studio|Propriété/château|Commerce|"
                r"Immeuble|Parking|Bureau|Ferme|Loft|Local|Programme)\s*\n\s*"
                r"(\d+)\s*m2\s*\n\s*(.+)",
                link_text,
                re.IGNORECASE,
            )
            if type_match:
                prop.property_type = type_match.group(1).capitalize()
                prop.surface = float(type_match.group(2))
                loc = type_match.group(3).strip()
                # Extraire ville et code postal : "Mont-Saint-Aignan (76)"
                loc_match = re.match(r"(.+?)\s*\((\d+)\)", loc)
                if loc_match:
                    prop.city = loc_match.group(1).strip()
                else:
                    prop.city = loc
                break

        # Pièces et chambres
        rooms_match = re.search(r"(\d+)\s*pièce", text)
        if rooms_match:
            prop.rooms = int(rooms_match.group(1))

        bedrooms_match = re.search(r"(\d+)\s*chambre", text)
        if bedrooms_match:
            prop.bedrooms = int(bedrooms_match.group(1))

        # Terrain
        terrain_match = re.search(r"[Tt]errain\s+(\d[\d\s]*)\s*m", text)
        if terrain_match:
            prop.exterior_surface = float(terrain_match.group(1).replace(" ", ""))

        # Code postal depuis le département
        if not prop.postal_code and prop.city:
            # Chercher un pattern "Ville (76XXX)" ou "(76)" dans le texte
            pc_match = re.search(r"\((" + dept + r"\d{3})\)", text)
            if pc_match:
                prop.postal_code = pc_match.group(1)

        # Description
        desc_match = re.search(
            r"DPE\s*:\s*\w?\s*\n?\s*(.{20,})",
            text,
            re.DOTALL,
        )
        if desc_match:
            prop.description = desc_match.group(1).strip()[:2000]
        else:
            # Fallback: dernière partie longue du texte
            for line in lines:
                if len(line) > 50 and "€" not in line:
                    prop.description = line[:2000]
                    break

        # Titre
        parts = []
        if prop.property_type:
            parts.append(prop.property_type)
        if prop.surface:
            parts.append(f"{prop.surface:.0f} m²")
        if prop.city:
            parts.append(prop.city)
        prop.title = " - ".join(parts) if parts else None

        return prop if prop.title else None
