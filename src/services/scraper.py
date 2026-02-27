import asyncio
import re
import sys
import urllib.parse
from playwright.async_api import async_playwright
import requests

API_URL = "http://127.0.0.1:8000/api/v1/games/parse"

# Approximate exchange rates to USD (as of early 2026)
CONVERSION_RATES = {
    "RON": 0.21,
    "EUR": 1.08,
    "GBP": 1.26,
    "UAH": 0.026,
    "USD": 1.0
}

def convert_to_usd(price: float, currency: str) -> float:
    """Converts a given price to USD based on static conversion rates."""
    rate = CONVERSION_RATES.get(currency.upper(), 1.0)
    return round(price * rate, 2)

def extract_price(text: str) -> float:
    """Extracts float value from strings containing prices."""
    if not text:
        return 0.0
        
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if any(line.lower() == "free" for line in lines):
        return 0.0
        
    for line in reversed(lines):
        decimal_matches = re.findall(r"\d+[.,]\d+", line)
        if decimal_matches:
            return float(decimal_matches[-1].replace(",", "."))
            
        if re.search(r"(?:lei|ron|\$|€|£|usd|₴|uah|грн)", line, re.IGNORECASE):
            whole_matches = re.findall(r"\d+", line)
            if whole_matches:
                return float(whole_matches[-1])
                
    return 0.0

def extract_discount(text: str) -> int:
    """Extracts integer value from strings like '-50%'."""
    if not text:
        return 0
    matches = re.findall(r"\d+", text)
    if matches:
        return int(matches[0])
    return 0

def extract_currency(text: str) -> str:
    """Determines the original currency from the text."""
    if not text:
        return "USD"
        
    text_lower = text.lower()
    if "lei" in text_lower or "ron" in text_lower:
        return "RON"
    if "€" in text_lower or "eur" in text_lower:
        return "EUR"
    if "₴" in text_lower or "uah" in text_lower or "грн" in text_lower:
        return "UAH"
    if "£" in text_lower or "gbp" in text_lower:
        return "GBP"
        
    return "USD"

async def scrape_steam(search_term: str):
    print(f"🔵 [Steam] Initializing scraper for '{search_term}'...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # MAGIC SPOOFING: Add cookies to bypass the 18+ age gate on Steam
        context = await browser.new_context()
        await context.add_cookies([
            {"name": "birthtime", "value": "283993201", "domain": "store.steampowered.com", "path": "/"},
            {"name": "lastagecheckage", "value": "1-January-1900", "domain": "store.steampowered.com", "path": "/"}
        ])
        page = await context.new_page()

        encoded_term = urllib.parse.quote(search_term)
        # Force US region and USD currency using &cc=us parameter
        await page.goto(f"https://store.steampowered.com/search/?term={encoded_term}&cc=us")
        
        try:
            await page.wait_for_selector("a.search_result_row", timeout=5000)
        except Exception:
            print(f"❌ [Steam] No results found for '{search_term}'.")
            await browser.close()
            return

        games = await page.query_selector_all("a.search_result_row")
        print(f"🎮 [Steam] Found games. Processing top 5...\n")

        for game in games[:5]:
            title_el = await game.query_selector("span.title")
            raw_title = await title_el.inner_text() if title_el else "Unknown"

            url = await game.get_attribute("href")
            remote_id = url.split("/app/")[1].split("/")[0] if url and "/app/" in url else "unknown"

            if remote_id != "unknown":
                price_el = await game.query_selector("div.discount_final_price")
                raw_price = await price_el.inner_text() if price_el else "0.0"

                discount_el = await game.query_selector("div.discount_pct")
                raw_discount = await discount_el.inner_text() if discount_el else "0"

                original_price = extract_price(raw_price)
                original_currency = extract_currency(raw_price)
                
                # Convert to USD before saving to database
                final_usd_price = convert_to_usd(original_price, original_currency)

                payload = {
                    "store_id": 1,
                    "store_name": "Steam",
                    "raw_title": raw_title,
                    "remote_id": remote_id,
                    "url": url.split("?")[0],
                    "price": final_usd_price,
                    "currency": "USD", # Forcing USD everywhere
                    "discount_percent": extract_discount(raw_discount),
                }

                try:
                    response = requests.post(API_URL, json=payload)
                    if response.status_code == 200:
                        print(f"✅ [Steam] Saved: {raw_title} | ${payload['price']} USD")
                except Exception as e:
                    pass

        await browser.close()

async def scrape_epic(search_term: str):
    print(f"⚫ [Epic Games] Initializing scraper for '{search_term}'...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # MAGIC SPOOFING: Pretend to be a normal Windows + Chrome browser
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        encoded_term = urllib.parse.quote(search_term)
        await page.goto(f"https://store.epicgames.com/en-US/browse?q={encoded_term}&sortBy=relevancy")
        
        try:
            await page.wait_for_selector('a[href*="/p/"]', timeout=15000)
        except Exception:
            print(f"❌ [Epic Games] No results found for '{search_term}'. (Timeout or Bot Protection)")
            await browser.close()
            return

        games = await page.query_selector_all('a[href*="/p/"]')
        print(f"🎮 [Epic Games] Found games. Processing top 3...\n")

        for game in games[:3]:
            try:
                url_attr = await game.get_attribute("href")
                full_url = f"https://store.epicgames.com{url_attr}" if url_attr else ""
                remote_id = url_attr.split("/")[-1] if url_attr else "unknown"

                text_content = await game.inner_text()
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                
                if not lines:
                    continue
                    
                raw_title = lines[1] if len(lines) > 1 and ("Game" in lines[0] or "Edition" in lines[0]) else lines[0]

                raw_discount = "0"
                for line in lines:
                    if "%" in line:
                        raw_discount = line
                        break
                
                original_price = extract_price(text_content)
                original_currency = extract_currency(text_content)
                
                # Convert RON/EUR directly to USD before saving
                final_usd_price = convert_to_usd(original_price, original_currency)

                payload = {
                    "store_id": 2,
                    "store_name": "Epic Games",
                    "raw_title": raw_title,
                    "remote_id": remote_id,
                    "url": full_url,
                    "price": final_usd_price,
                    "currency": "USD", # Forcing USD everywhere
                    "discount_percent": extract_discount(raw_discount),
                }

                try:
                    response = requests.post(API_URL, json=payload)
                    if response.status_code == 200:
                        print(f"✅ [Epic Games] Saved: {raw_title} | ${payload['price']} USD")
                except Exception as e:
                    pass

            except Exception as e:
                pass

        await browser.close()

async def main(search_term: str):
    await asyncio.gather(
        scrape_steam(search_term),
        scrape_epic(search_term)
    )
    print("\n✨ All scrape pipelines finished!")

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "witcher"
    asyncio.run(main(query))