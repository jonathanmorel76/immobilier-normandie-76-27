"""
Scraper PAP.fr pour les ventes immobilières en Seine-Maritime (76) et Eure (27).
Utilise Playwright pour contourner les blocages IP de datacenter.
"""
import asyncio
import re
from typing import Optional, List
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper, PropertyData

SEARCH_URLS = {
    "76": "https://www.pap.fr/annonce/ventes-immobilieres-seine-maritime-g440",
    "27": "https://www.pap.fr/annonce/ventes-immobilieres-eure-g391",
}

BASE_URL = "https://www.pap.fr"
MAX_PAGES = 3


class PapScraper(BaseScraper):
    """Scrape les annonces immobilières de PAP.fr pour le 76 et le 27."""

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
                    print(f"[PAP] Dept {dept}: {len(dept_results)} annonces")
                    await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

                await browser.close()
        except Exception as e:
            print(f"[PAP] Erreur globale: {e}")

        return results

    async def _scrape_department(
        self, context, base_url: str, dept: str
    ) -> List[PropertyData]:
        results = []

        for page_num in range(1, MAX_PAGES + 1):
            url = base_url if page_num == 1 else f"{base_url}?page={page_num}"
            page = await context.new_page()

            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                status = resp.status if resp else 0
                print(f"[PAP] Fetched {url} -> status {status}")
                await asyncio.sleep(4)

                # Accepter les cookies
                for sel in [
                    "#didomi-notice-agree-button",
                    "button[class*='accept']",
                    ".btn-accept-cookies",
                ]:
                    try:
                        await page.click(sel, timeout=2000)
                        await asyncio.sleep(1)
                        break
                    except Exception:
                        continue

                # Extraire les annonces depuis le DOM
                listings = await page.evaluate("""() => {
                    const results = [];
                    const items = document.querySelectorAll('.search-list-item-alt');

                    items.forEach(item => {
                        const data = {};

                        // Lien
                        const link = item.querySelector('a.item-thumb-link') || item.querySelector('a.item-title') || item.querySelector('a[href*="/annonces/"]');
                        data.href = link ? (link.getAttribute('href') || '') : '';

                        // Prix
                        const priceEl = item.querySelector('.item-price');
                        data.price = priceEl ? priceEl.textContent.trim() : '';

                        // Localisation
                        const bodyEl = item.querySelector('.item-body') || item.querySelector('.item-title');
                        data.bodyText = bodyEl ? bodyEl.textContent.trim() : '';

                        // Tags
                        const tags = item.querySelectorAll('.item-tags li');
                        data.tags = Array.from(tags).map(t => t.textContent.trim());

                        // Description
                        const descEl = item.querySelector('.item-description');
                        data.description = descEl ? descEl.textContent.trim().substring(0, 2000) : '';

                        if (data.href && data.href.includes('/annonces/')) {
                            results.push(data);
                        }
                    });

                    return results;
                }""")

                print(f"[PAP] Page {page_num} dept {dept}: {len(listings)} annonces")

                if not listings:
                    await page.close()
                    break

                for item in listings:
                    prop = self._parse_item(item, dept)
                    if prop and prop.title:
                        results.append(prop)

            except Exception as e:
                print(f"[PAP] Erreur page {page_num} dept {dept}: {e}")
            finally:
                await page.close()

            await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

        return results

    def _parse_item(self, item: dict, dept: str) -> Optional[PropertyData]:
        """Parse un élément extrait du DOM."""
        href = item.get("href", "")
        if not href:
            return None

        full_url = BASE_URL + href if href.startswith("/") else href

        prop = PropertyData()
        prop.source = "pap"
        prop.source_url = full_url
        prop.department = dept

        # Extraire type + ville + code postal depuis l'URL
        # ex: /annonces/maison-bonsecours-76240-r459902609
        url_match = re.search(r"/annonces/([a-z\-]+?)-(\d{5})-r\d+", href)
        if url_match:
            slug = url_match.group(1)
            postal = url_match.group(2)
            parts = slug.split("-")
            prop.property_type = parts[0].capitalize() if parts else None
            if len(parts) > 1:
                prop.city = " ".join(p.capitalize() for p in parts[1:])
            prop.postal_code = postal
        else:
            url_match2 = re.search(r"/annonces/([a-z\-]+?)-r\d+", href)
            if url_match2:
                slug = url_match2.group(1)
                parts = slug.split("-")
                prop.property_type = parts[0].capitalize() if parts else None
                if len(parts) > 1:
                    prop.city = " ".join(p.capitalize() for p in parts[1:])

        # Prix
        price_text = item.get("price", "")
        if price_text:
            prop.price = self.parse_price(price_text)

        # Localisation depuis le texte
        body_text = item.get("bodyText", "")
        if body_text:
            loc_match = re.search(
                r"([\wÀ-ÿ\-]+(?:\s[\wÀ-ÿ\-]+)*)\s*\((\d{5})\)", body_text
            )
            if loc_match:
                prop.city = loc_match.group(1).strip()
                prop.postal_code = loc_match.group(2)

        # Tags (pièces, chambres, surface, terrain)
        for tag in item.get("tags", []):
            text = tag.lower()
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
        desc = item.get("description", "")
        if desc:
            prop.description = desc[:2000]

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
