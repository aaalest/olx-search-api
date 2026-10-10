import asyncio
import json
import re
from playwright.async_api import async_playwright

from init_app import initialize_db

async def get_olx_json_listings():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        query = "oneplus-13"
        url = f"https://www.olx.pl/elektronika/telefony/q-{query}/"
        print(f"[*] Navigating to: {url}")

        await page.goto(url, wait_until="domcontentloaded")

        content = await page.content()

        match = re.search(r'window\.__PRERENDERED_STATE__\s*=\s*(".*?"|\{.*?\});', content, re.DOTALL)
        if not match:
            print("[!] Could not find __PRERENDERED_STATE__ in page source.")
            await browser.close()
            return

        raw_state = match.group(1)
        if raw_state.startswith('"'):
            state_data = json.loads(json.loads(raw_state))
        else:
            state_data = json.loads(raw_state)

        ads = (
            state_data.get("listing", {})
            .get("listing", {})
            .get("ads", [])
        )

        print(f"[+] Found {len(ads)} listings in raw JSON state.\n")

        for ad in ads[:5]:
            title = ad.get("title")
            ad_url = ad.get("url")
            created_time = ad.get("created_time")

            # Safe extraction for parameters
            params = {}
            for p in ad.get("params", []):
                key = p.get("key")
                val = p.get("value")
                if isinstance(val, dict):
                    params[key] = val.get("label") or val.get("value")
                else:
                    params[key] = val

            # Safe extraction for photos (scalar string or dict)
            photos = []
            for photo in ad.get("photos", []):
                if isinstance(photo, dict):
                    photo_url = photo.get("link", "")
                elif isinstance(photo, str):
                    photo_url = photo
                else:
                    continue
                photos.append(photo_url.replace("{width}x{height}", "1000x700"))

            print(f"Title: {title}")
            print(f"URL: {ad_url}")
            print(f"Created: {created_time}")
            print(f"Price/Params: {params}")
            print(f"Photos: {len(photos)} found")
            print("-" * 50)

        await browser.close()


if __name__ == "__main__":
    initialize_db()
    asyncio.run(get_olx_json_listings())
