"""
Scraper LeBonCoin pour les ventes immobilières en Seine-Maritime (76) et Eure (27).
NOTE: LeBonCoin utilise DataDome (anti-bot) qui bloque le scraping headless.
Ce scraper tente l'extraction mais signale clairement l'échec.
"""
import asyncio
import json
import re
from typing import Optional, List
from playwright.async_api import async_playwright, Page, BrowserContext

from app.scrapers.base import BaseScraper, PropertyData

SEARCH_URLS = {
    "76": "https://www.leboncoin.fr/recherche?category=9&real_estate_type=1%2C2%2C4&locations=76",
    "27": "https://www.leboncoin.fr/recherche?category=9&real_estate_type=1%2C2%2C4&locations=27",
}

MAX_PAGES = 2
MAX_LISTINGS = 40


class LeBonCoinScraper(BaseScraper):
    """Scrape les annonces immobilières de LeBonCoin pour le 76 et le 27."""

    async def scrape(self) -> List[PropertyData]:
        results = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                )
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/127.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 800},
                    locale="fr-FR",
                    timezone_id="Europe/Paris",
                )
                # Tenter de masquer l'automation
                await context.add_init_script(
                    'Object.defineProperty(navigator, "webdriver", {get: () => false});'
                )
                await context.route(
                    "**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,mp4,mp3}",
                    lambda route: route.abort(),
                )

                for dept, url in SEARCH_URLS.items():
                    dept_results = await self._scrape_department(context, url, dept)
                    results.extend(dept_results)
                    if len(results) >= MAX_LISTINGS:
                        break
                    await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

                await browser.close()
        except Exception as e:
            print(f"[LeBonCoin] Erreur globale: {e}")

        if not results:
            print("[LeBonCoin] ⚠ Aucune annonce récupérée (probable blocage DataDome/anti-bot)")

        return results[:MAX_LISTINGS]

    async def _scrape_department(
        self, context: BrowserContext, base_url: str, dept: str
    ) -> List[PropertyData]:
        results = []
        page = await context.new_page()
        try:
            await page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            # Vérifier si on est bloqué par DataDome
            content = await page.content()
            if "datadome" in content.lower() or "captcha" in content.lower():
                print(f"[LeBonCoin] Bloqué par DataDome/CAPTCHA pour dept {dept}")
                return []

            # Essayer d'accepter les cookies
            try:
                await page.click("#didomi-notice-agree-button", timeout=3000)
                await asyncio.sleep(1)
            except Exception:
                pass

            # Essayer différents sélecteurs pour les annonces
            listing_links = []
            for selector in [
                "a[data-qa-id='aditem_container']",
                "a[data-test-id='ad']",
                "a[href*='/ad/ventes_immobilieres/']",
            ]:
                try:
                    listing_links = await page.eval_on_selector_all(
                        selector, "els => els.map(el => el.href)"
                    )
                    if listing_links:
                        print(f"[LeBonCoin] Dept {dept}: {len(listing_links)} annonces trouvées avec '{selector}'")
                        break
                except Exception:
                    continue

            if not listing_links:
                print(f"[LeBonCoin] Dept {dept}: aucune annonce trouvée")
                return []

            for link in listing_links[:15]:
                try:
                    prop = await self._scrape_listing(page, link, dept)
                    if prop:
                        results.append(prop)
                    await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)
                except Exception as e:
                    print(f"[LeBonCoin] Erreur annonce {link}: {e}")

        except Exception as e:
            print(f"[LeBonCoin] Erreur dept {dept}: {e}")
        finally:
            await page.close()

        return results

    async def _scrape_listing(
        self, page: Page, url: str, dept: str
    ) -> Optional[PropertyData]:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(1)

        prop = PropertyData()
        prop.source = "leboncoin"
        prop.source_url = url
        prop.department = dept

        try:
            prop.title = (await page.inner_text("h1", timeout=5000)).strip()
        except Exception:
            prop.title = "Bien immobilier"

        try:
            price_text = await page.inner_text("[data-qa-id='adview_price']", timeout=5000)
            prop.price = self.parse_price(price_text)
        except Exception:
            pass

        try:
            criteria_items = await page.query_selector_all("[data-qa-id='criteria_item']")
            for item in criteria_items:
                label_el = await item.query_selector("[data-qa-id='criteria_item_key']")
                value_el = await item.query_selector("[data-qa-id='criteria_item_value']")
                if not label_el or not value_el:
                    continue
                label = (await label_el.inner_text()).strip().lower()
                value = (await value_el.inner_text()).strip()

                if "surface" in label and "terrain" not in label:
                    prop.surface = self.parse_surface(value)
                elif "terrain" in label or "jardin" in label:
                    prop.exterior_surface = self.parse_surface(value)
                elif "pièce" in label:
                    m = re.search(r"\d+", value)
                    if m:
                        prop.rooms = int(m.group())
                elif "chambre" in label:
                    m = re.search(r"\d+", value)
                    if m:
                        prop.bedrooms = int(m.group())
                elif "type" in label:
                    prop.property_type = value
        except Exception:
            pass

        try:
            location_text = await page.inner_text("[data-qa-id='adview_location_informations']", timeout=5000)
            prop.city = location_text.strip()
            postal = self.extract_postal_code(location_text)
            if postal:
                prop.postal_code = postal
        except Exception:
            pass

        try:
            prop.description = (await page.inner_text("[data-qa-id='adview_description_container']", timeout=5000)).strip()[:2000]
        except Exception:
            pass

        try:
            scripts = await page.query_selector_all("script[type='application/ld+json']")
            for script in scripts:
                text = await script.inner_text()
                try:
                    data = json.loads(text)
                    if isinstance(data, dict) and "geo" in data:
                        prop.latitude = float(data["geo"].get("latitude", 0)) or None
                        prop.longitude = float(data["geo"].get("longitude", 0)) or None
                except Exception:
                    pass
        except Exception:
            pass

        return prop if prop.title else None
