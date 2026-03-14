"""
Scraper Logic-Immo.com pour les ventes immobilières en Seine-Maritime (76) et Eure (27).
Utilise Playwright pour charger les pages et parser le HTML rendu.
"""
import asyncio
import re
from typing import Optional, List
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper, PropertyData

SEARCH_URLS = {
    "76": "https://www.logic-immo.com/vente-immobilier-seine-maritime-departement,76_99/options/groupprptypesaliasaliasaliasaliasaliasaliasaliasaliasalias=1,2,6,7,12,3,4,5,9",
    "27": "https://www.logic-immo.com/vente-immobilier-eure-departement,27_99/options/groupprptypesaliasaliasaliasaliasaliasaliasaliasaliasalias=1,2,6,7,12,3,4,5,9",
}

MAX_PAGES = 3
BASE_URL = "https://www.logic-immo.com"


class LogicImmoScraper(BaseScraper):
    """Scrape les annonces immobilières de Logic-Immo pour le 76 et le 27."""

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
                    print(f"[LogicImmo] Dept {dept}: {len(dept_results)} annonces")
                    await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

                await browser.close()
        except Exception as e:
            print(f"[LogicImmo] Erreur globale: {e}")

        return results

    async def _scrape_department(
        self, context, base_url: str, dept: str
    ) -> List[PropertyData]:
        results = []

        for page_num in range(1, MAX_PAGES + 1):
            url = base_url if page_num == 1 else f"{base_url}&page={page_num}"
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(4)

                # Accepter les cookies
                try:
                    await page.click("#didomi-notice-agree-button", timeout=3000)
                    await asyncio.sleep(1)
                except Exception:
                    pass

                # Extraire les annonces depuis le DOM
                listings = await page.evaluate("""() => {
                    const results = [];
                    // Logic-Immo utilise des cartes d'annonces
                    const cards = document.querySelectorAll(
                        '.announcesListCard, .offer-list__item, .card-listing, [data-listing], .announceCard'
                    );
                    cards.forEach(card => {
                        const data = {};

                        // Lien
                        const link = card.querySelector('a[href*="/detail"]') || card.querySelector('a[href*="/vente"]') || card.querySelector('a');
                        data.url = link ? link.href : '';

                        // Prix
                        const priceEl = card.querySelector('.announcesListCard__price, .offer-price, .card-price, [class*="price"]');
                        data.price = priceEl ? priceEl.textContent.trim() : '';

                        // Surface
                        const surfaceEl = card.querySelector('.announcesListCard__surface, [class*="surface"], [class*="area"]');
                        data.surface = surfaceEl ? surfaceEl.textContent.trim() : '';

                        // Pièces / chambres
                        const tagsEls = card.querySelectorAll('.announcesListCard__tags li, .offer-details__item, [class*="room"], [class*="piece"]');
                        data.tags = Array.from(tagsEls).map(t => t.textContent.trim());

                        // Localisation
                        const locEl = card.querySelector('.announcesListCard__loc, .offer-location, [class*="city"], [class*="location"]');
                        data.location = locEl ? locEl.textContent.trim() : '';

                        // Type de bien
                        const typeEl = card.querySelector('.announcesListCard__type, .offer-type, [class*="type"]');
                        data.type = typeEl ? typeEl.textContent.trim() : '';

                        // Titre
                        const titleEl = card.querySelector('.announcesListCard__title, .offer-title, h2, h3, [class*="title"]');
                        data.title = titleEl ? titleEl.textContent.trim() : '';

                        // Description
                        const descEl = card.querySelector('.announcesListCard__desc, .offer-description, [class*="description"]');
                        data.description = descEl ? descEl.textContent.trim() : '';

                        // Image
                        const imgEl = card.querySelector('img[src*="http"]') || card.querySelector('img[data-src]');
                        data.image = imgEl ? (imgEl.src || imgEl.dataset.src) : '';

                        if (data.url || data.price) {
                            results.push(data);
                        }
                    });

                    // Fallback: essayer tous les liens d'annonces
                    if (results.length === 0) {
                        const allText = document.body.innerText;
                        // Retourner le texte brut pour debug
                        results.push({debug: true, bodyLength: allText.length, bodyPreview: allText.substring(0, 2000)});
                    }

                    return results;
                }""")

                print(f"[LogicImmo] Page {page_num} dept {dept}: {len(listings)} éléments trouvés")

                # Debug: si on a des résultats de debug
                if listings and listings[0].get("debug"):
                    body = listings[0].get("bodyPreview", "")
                    print(f"[LogicImmo] Debug body ({listings[0].get('bodyLength')} chars): {body[:500]}")
                    # Essayer d'extraire depuis le texte brut
                    page_props = await self._extract_from_page_source(page, dept)
                    results.extend(page_props)
                else:
                    for item in listings:
                        prop = self._parse_item(item, dept)
                        if prop and prop.title:
                            results.append(prop)

            except Exception as e:
                print(f"[LogicImmo] Erreur page {page_num} dept {dept}: {e}")
            finally:
                await page.close()

            await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

        return results

    async def _extract_from_page_source(self, page, dept: str) -> List[PropertyData]:
        """Fallback: extraire les données depuis les scripts JSON-LD ou __NEXT_DATA__."""
        results = []
        try:
            # Chercher les données JSON dans les scripts
            json_data = await page.evaluate("""() => {
                // Chercher __NEXT_DATA__ ou données React/Vue
                const nextData = document.querySelector('#__NEXT_DATA__');
                if (nextData) return {type: 'next', data: nextData.textContent};

                // Chercher les scripts JSON-LD
                const jsonLd = document.querySelectorAll('script[type="application/ld+json"]');
                const ldData = Array.from(jsonLd).map(s => s.textContent);
                if (ldData.length > 0) return {type: 'jsonld', data: ldData};

                // Chercher les scripts avec des données d'annonces
                const scripts = document.querySelectorAll('script');
                for (const s of scripts) {
                    const text = s.textContent || '';
                    if (text.includes('annonce') || text.includes('listing') || text.includes('property')) {
                        if (text.length > 100 && text.length < 500000) {
                            return {type: 'script', data: text.substring(0, 50000)};
                        }
                    }
                }

                return {type: 'none'};
            }""")

            if json_data.get("type") == "next":
                import json
                try:
                    data = json.loads(json_data["data"])
                    # Naviguer dans __NEXT_DATA__ pour trouver les annonces
                    props = data.get("props", {}).get("pageProps", {})
                    listings = props.get("announcements", []) or props.get("listings", []) or props.get("ads", [])
                    for ad in listings:
                        prop = self._parse_json_ad(ad, dept)
                        if prop:
                            results.append(prop)
                except Exception as e:
                    print(f"[LogicImmo] Erreur parsing __NEXT_DATA__: {e}")

        except Exception as e:
            print(f"[LogicImmo] Erreur extraction fallback: {e}")

        return results

    def _parse_item(self, item: dict, dept: str) -> Optional[PropertyData]:
        """Parse un élément extrait du DOM."""
        prop = PropertyData()
        prop.source = "logicimmo"
        prop.department = dept

        prop.source_url = item.get("url", "")
        if not prop.source_url.startswith("http"):
            prop.source_url = BASE_URL + prop.source_url

        # Prix
        price_text = item.get("price", "")
        prop.price = self.parse_price(price_text)

        # Surface
        surface_text = item.get("surface", "")
        prop.surface = self.parse_surface(surface_text)

        # Type
        type_text = item.get("type", "").strip()
        if type_text:
            prop.property_type = type_text.capitalize()

        # Localisation
        loc_text = item.get("location", "")
        if loc_text:
            # Extraire ville et code postal
            pc = self.extract_postal_code(loc_text)
            if pc:
                prop.postal_code = pc
                prop.city = loc_text.replace(pc, "").strip().strip(",").strip("(").strip(")").strip()
            else:
                prop.city = loc_text.strip()

        # Tags (pièces, chambres)
        for tag in item.get("tags", []):
            tag_lower = tag.lower()
            m = re.search(r"(\d+)", tag)
            if m:
                val = int(m.group(1))
                if "pièce" in tag_lower or "pce" in tag_lower:
                    prop.rooms = val
                elif "chambre" in tag_lower or "ch" in tag_lower:
                    prop.bedrooms = val
                elif "m²" in tag_lower or "m2" in tag_lower:
                    if not prop.surface:
                        prop.surface = float(val)

        # Titre
        title = item.get("title", "")
        if title:
            prop.title = title
        else:
            parts = []
            if prop.property_type:
                parts.append(prop.property_type)
            if prop.surface:
                parts.append(f"{prop.surface:.0f} m²")
            if prop.city:
                parts.append(prop.city)
            prop.title = " - ".join(parts) if parts else None

        # Description
        desc = item.get("description", "")
        if desc:
            prop.description = desc[:2000]

        # Image
        img = item.get("image", "")
        if img:
            prop.images = [img]

        return prop if prop.title else None

    def _parse_json_ad(self, ad: dict, dept: str) -> Optional[PropertyData]:
        """Parse une annonce depuis les données JSON (fallback __NEXT_DATA__)."""
        prop = PropertyData()
        prop.source = "logicimmo"
        prop.department = dept

        prop.price = ad.get("price") or ad.get("prix")
        prop.surface = ad.get("surface") or ad.get("surfaceArea") or ad.get("area")
        prop.rooms = ad.get("rooms") or ad.get("nbRooms") or ad.get("roomsQuantity")
        prop.bedrooms = ad.get("bedrooms") or ad.get("nbBedrooms")
        prop.city = ad.get("city") or ad.get("ville")
        prop.postal_code = ad.get("postalCode") or ad.get("zipCode")

        url = ad.get("url") or ad.get("detailUrl") or ad.get("link") or ""
        prop.source_url = url if url.startswith("http") else BASE_URL + url

        prop.property_type = ad.get("propertyType") or ad.get("type")
        prop.description = (ad.get("description") or "")[:2000]
        prop.title = ad.get("title") or f"{prop.property_type or 'Bien'} - {prop.city or ''}"

        # Coordonnées
        lat = ad.get("latitude") or ad.get("lat")
        lng = ad.get("longitude") or ad.get("lng") or ad.get("lon")
        if lat and lng:
            prop.latitude = float(lat)
            prop.longitude = float(lng)

        # Images
        photos = ad.get("photos") or ad.get("images") or []
        if isinstance(photos, list):
            prop.images = [p if isinstance(p, str) else p.get("url", "") for p in photos[:8]]

        return prop if prop.title else None
