import asyncio
import re
from playwright.async_api import async_playwright
import requests

API_URL = "http://127.0.0.1:8000/api/v1/games/parse"

def extract_price(text: str) -> float:
    """Extracts float value from strings like '$19.99' or 'Free'."""
    if not text or "free" in text.lower():
        return 0.0
    matches = re.findall(r'\d+[.,]\d+', text)
    if matches:
        return float(matches[0].replace(',', '.'))
    return 0.0

def extract_discount(text: str) -> int:
    """Extracts integer value from strings like '-50%'."""
    if not text:
        return 0
    matches = re.findall(r'\d+', text)
    if matches:
        return int(matches[0])
    return 0

async def scrape_steam():
    print("🚀 Initializing Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("🌐 Navigating to Steam Search...")
        await page.goto("https://store.steampowered.com/search/?term=witcher")
        await page.wait_for_selector("a.search_result_row")

        games = await page.query_selector_all("a.search_result_row")
        print(f"🎮 Found {len(games)} games. Processing top 3...\n")

        for game in games[:3]:
            # Extract Title
            title_el = await game.query_selector("span.title")
            raw_title = await title_el.inner_text() if title_el else "Unknown"

            # Extract URL & ID
            url = await game.get_attribute("href")
            remote_id = url.split("/app/")[1].split("/")[0] if url and "/app/" in url else "unknown"

            if remote_id != "unknown":
                # Extract Price & Discount
                price_el = await game.query_selector("div.discount_final_price")
                raw_price = await price_el.inner_text() if price_el else "0.0"
                
                discount_el = await game.query_selector("div.discount_pct")
                raw_discount = await discount_el.inner_text() if discount_el else "0"

                payload = {
                    "store_id": 1,
                    "store_name": "Steam",
                    "raw_title": raw_title,
                    "remote_id": remote_id,
                    "url": url.split("?")[0],
                    "price": extract_price(raw_price),
                    "currency": "USD",
                    "discount_percent": extract_discount(raw_discount)
                }

                # Send to API
                try:
                    response = requests.post(API_URL, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Saved: {raw_title} | Price: {payload['price']} | Discount: {payload['discount_percent']}%")
                    else:
                        print(f"❌ API Error for {raw_title}: {response.text}")
                except Exception as e:
                    print(f"❌ Connection Error: {e}")

        await browser.close()
        print("\n✨ Scrape pipeline finished!")

if __name__ == "__main__":
    asyncio.run(scrape_steam())