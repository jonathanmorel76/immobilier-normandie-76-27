"""
Scraper Ouestfrance-immo.com pour les ventes immobilières en Seine-Maritime (76) et Eure (27).
Utilise Playwright pour charger les pages et parser le HTML rendu.
Ouestfrance-immo est un portail régional bien adapté à la Normandie.
"""
import asyncio
import json
import re
from typing import Optional, List
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper, PropertyData

SEARCH_URLS = {
    "76": "https://www.ouestfrance-immo.com/acheter/seine-maritime/",
    "27": "https://www.ouestfrance-immo.com/acheter/eure/",
}

MAX_PAGES = 3
BASE_URL = "https://www.ouestfrance-immo.com"


class OuestFranceScraper(BaseScraper):
    """Scrape les annonces immobilières de Ouestfrance-immo pour le 76 et le 27."""

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
                    print(f"[OuestFrance] Dept {dept}: {len(dept_results)} annonces")
                    await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

                await browser.close()
        except Exception as e:
            print(f"[OuestFrance] Erreur globale: {e}")

        return results

    async def _scrape_department(
        self, context, base_url: str, dept: str
    ) -> List[PropertyData]:
        results = []
        captured_json = []

        async def on_response(response):
            """Intercepte les réponses JSON qui pourraient contenir les annonces."""
            url = response.url
            if response.status == 200 and ("api" in url or "search" in url or "annonce" in url):
                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    try:
                        data = await response.json()
                        captured_json.append(data)
                    except Exception:
                        pass

        for page_num in range(1, MAX_PAGES + 1):
            url = base_url if page_num == 1 else f"{base_url}?page={page_num}"
            page = await context.new_page()
            page.on("response", on_response)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(5)

                # Accepter les cookies
                for selector in [
                    "#didomi-notice-agree-button",
                    "[class*='cookie'] button",
                    "button[class*='accept']",
                    ".consent-accept",
                ]:
                    try:
                        await page.click(selector, timeout=2000)
                        await asyncio.sleep(1)
                        break
                    except Exception:
                        continue

                # Extraire les annonces depuis le DOM
                listings = await page.evaluate("""() => {
                    const results = [];

                    // Sélecteurs courants pour Ouestfrance-immo
                    const cards = document.querySelectorAll(
                        '.annLink, .ann-item, .annonce, [class*="annonce"], .listAnnonce li, .card-announcement, article[class*="ann"]'
                    );

                    cards.forEach(card => {
                        const data = {};

                        // Lien
                        const link = card.tagName === 'A' ? card : card.querySelector('a');
                        data.url = link ? link.href : '';

                        // Prix
                        const priceEl = card.querySelector('[class*="price"], [class*="prix"], .ann-price, .annPrice');
                        data.price = priceEl ? priceEl.textContent.trim() : '';

                        // Titre / type
                        const titleEl = card.querySelector('h2, h3, [class*="title"], [class*="titre"], .ann-title');
                        data.title = titleEl ? titleEl.textContent.trim() : '';

                        // Localisation
                        const locEl = card.querySelector('[class*="city"], [class*="ville"], [class*="location"], [class*="loc"], .ann-loc');
                        data.location = locEl ? locEl.textContent.trim() : '';

                        // Détails (surface, pièces, etc.)
                        const detailEls = card.querySelectorAll('[class*="detail"] li, [class*="crit"] li, [class*="tag"], .ann-criteria span, [class*="feature"]');
                        data.details = Array.from(detailEls).map(d => d.textContent.trim());

                        // Si pas de détails dans les li, chercher dans le texte global
                        if (data.details.length === 0) {
                            const allText = card.textContent || '';
                            data.fullText = allText.replace(/\\s+/g, ' ').trim();
                        }

                        // Image
                        const imgEl = card.querySelector('img[src*="http"]') || card.querySelector('img[data-src]');
                        data.image = imgEl ? (imgEl.src || imgEl.dataset.src || '') : '';

                        if (data.url && data.url.includes('/acheter/')) {
                            results.push(data);
                        }
                    });

                    // Si aucune carte trouvée, fallback
                    if (results.length === 0) {
                        // Chercher tous les liens d'annonces
                        const links = document.querySelectorAll('a[href*="/acheter/"]');
                        links.forEach(link => {
                            const href = link.href;
                            if (href.includes('/acheter/') && !href.endsWith('/acheter/') && !href.includes('departement')) {
                                const parent = link.closest('li, article, div');
                                results.push({
                                    url: href,
                                    title: link.textContent.trim().substring(0, 200),
                                    price: '',
                                    location: '',
                                    details: [],
                                    fullText: parent ? parent.textContent.replace(/\\s+/g, ' ').trim().substring(0, 500) : '',
                                    image: ''
                                });
                            }
                        });
                    }

                    return results;
                }""")

                print(f"[OuestFrance] Page {page_num} dept {dept}: {len(listings)} éléments")

                for item in listings:
                    prop = self._parse_item(item, dept)
                    if prop and prop.title:
                        results.append(prop)

                # Essayer aussi les données JSON interceptées
                for json_data in captured_json:
                    json_props = self._parse_json_response(json_data, dept)
                    results.extend(json_props)

                captured_json.clear()

            except Exception as e:
                print(f"[OuestFrance] Erreur page {page_num} dept {dept}: {e}")
            finally:
                await page.close()

            await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

        # Dédupliquer par URL
        seen = set()
        unique = []
        for prop in results:
            if prop.source_url not in seen:
                seen.add(prop.source_url)
                unique.append(prop)

        return unique

    def _parse_item(self, item: dict, dept: str) -> Optional[PropertyData]:
        """Parse un élément extrait du DOM."""
        prop = PropertyData()
        prop.source = "ouestfrance"
        prop.department = dept

        prop.source_url = item.get("url", "")
        if not prop.source_url.startswith("http"):
            prop.source_url = BASE_URL + prop.source_url

        # Prix
        price_text = item.get("price", "")
        prop.price = self.parse_price(price_text)

        # Titre
        title = item.get("title", "").strip()

        # Extraire type de bien depuis le titre
        type_patterns = {
            "maison": "Maison",
            "appartement": "Appartement",
            "terrain": "Terrain",
            "immeuble": "Immeuble",
            "commerce": "Commerce",
            "bureau": "Bureau",
            "parking": "Parking",
            "ferme": "Ferme",
            "château": "Château",
            "loft": "Loft",
            "studio": "Studio",
        }
        for pattern, ptype in type_patterns.items():
            if pattern in (title + " " + item.get("fullText", "")).lower():
                prop.property_type = ptype
                break

        # Localisation
        loc = item.get("location", "")
        full_text = item.get("fullText", "")

        if loc:
            pc = self.extract_postal_code(loc)
            if pc:
                prop.postal_code = pc
                prop.city = loc.replace(pc, "").strip().strip(",").strip("(").strip(")").strip()
            else:
                prop.city = loc.strip()

        # Fallback: chercher code postal dans le texte ou l'URL
        if not prop.postal_code:
            pc = self.extract_postal_code(full_text) or self.extract_postal_code(prop.source_url)
            if pc:
                prop.postal_code = pc

        # Détails (surface, pièces, chambres)
        for detail in item.get("details", []):
            detail_lower = detail.lower()
            m = re.search(r"(\d+(?:[.,]\d+)?)", detail)
            if m:
                if "m²" in detail_lower or "m2" in detail_lower:
                    val = float(m.group(1).replace(",", "."))
                    if "terrain" in detail_lower or "parcelle" in detail_lower:
                        prop.exterior_surface = val
                    elif not prop.surface:
                        prop.surface = val
                elif "pièce" in detail_lower or "pce" in detail_lower:
                    prop.rooms = int(float(m.group(1)))
                elif "chambre" in detail_lower or "ch" in detail_lower:
                    prop.bedrooms = int(float(m.group(1)))

        # Fallback: extraire depuis le texte brut
        if not prop.surface and full_text:
            s = self.parse_surface(full_text)
            if s:
                prop.surface = s
        if not prop.price and full_text:
            p = self.parse_price(full_text)
            if p and p > 10000:
                prop.price = p

        # Composer le titre
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

        # Image
        img = item.get("image", "")
        if img:
            prop.images = [img]

        return prop if prop.title else None

    def _parse_json_response(self, data, dept: str) -> List[PropertyData]:
        """Parse une réponse JSON interceptée."""
        results = []

        # Chercher les annonces dans différentes structures JSON
        ads = []
        if isinstance(data, dict):
            for key in ("items", "ads", "announcements", "results", "listings", "data"):
                if key in data and isinstance(data[key], list):
                    ads = data[key]
                    break

        for ad in ads:
            if not isinstance(ad, dict):
                continue
            prop = PropertyData()
            prop.source = "ouestfrance"
            prop.department = dept

            prop.price = ad.get("price") or ad.get("prix")
            prop.surface = ad.get("surface") or ad.get("area")
            prop.rooms = ad.get("rooms") or ad.get("nbRooms")
            prop.bedrooms = ad.get("bedrooms") or ad.get("nbBedrooms")
            prop.city = ad.get("city") or ad.get("ville")
            prop.postal_code = ad.get("postalCode") or ad.get("zipCode")
            prop.property_type = ad.get("propertyType") or ad.get("type")
            prop.description = (ad.get("description") or "")[:2000]

            url = ad.get("url") or ad.get("link") or ad.get("detailUrl") or ""
            prop.source_url = url if url.startswith("http") else BASE_URL + url

            lat = ad.get("latitude") or ad.get("lat")
            lng = ad.get("longitude") or ad.get("lng")
            if lat and lng:
                prop.latitude = float(lat)
                prop.longitude = float(lng)

            prop.title = ad.get("title") or f"{prop.property_type or 'Bien'} - {prop.city or ''}"

            photos = ad.get("photos") or ad.get("images") or []
            if isinstance(photos, list):
                prop.images = [
                    ph if isinstance(ph, str) else ph.get("url", "")
                    for ph in photos[:8]
                ]

            if prop.title and (prop.price or prop.surface):
                results.append(prop)

        return results
