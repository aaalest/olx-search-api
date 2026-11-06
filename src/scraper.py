import json
import re
from typing import Any

from sqlmodel import Session
from playwright.async_api import Browser, ViewportSize

from db.database import engine
from db.models import Offers
from crud import upsert_offer
from utils.common import safe_get, maybe
from utils.time import get_current_utc_datetime, parse_iso_to_utc_datetime
from logger import logger


async def scrape_olx_offers(browser: Browser, url: str) -> int:
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 "
                   "Safari/537.36",
        viewport=ViewportSize(width=1280, height=800)
    )
    page = await context.new_page()

    try:
        print(f"[*] Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded")

        content = await page.content()

        match = re.search(r'window\.__PRERENDERED_STATE__\s*=\s*(".*?"|\{.*?\});', content, re.DOTALL)
        if not match:
            logger.critical("[!] Could not find __PRERENDERED_STATE__ in page source.")
            return 0

        raw_state = match.group(1)
        if raw_state.startswith('"'):
            state_data = json.loads(json.loads(raw_state))
        else:
            state_data = json.loads(raw_state)

        raw_offers = safe_get(state_data, "listing.listing.ads", [])

        logger.info(f"[+] Found {len(raw_offers)} listings in raw JSON state.\n")

        count = 0
        with Session(engine) as session:
            for raw_offer in raw_offers:
                # Safe extraction for parameters
                params = {}
                for param in safe_get(raw_offer, "params", []):
                    key = safe_get(param, "key")
                    value = safe_get(param, "value")
                    if isinstance(value, dict):
                        params[key] = safe_get(value, "value")
                    else:
                        params[key] = value

                price_properties: Any = safe_get(raw_offer, "price", {})
                raw_value = safe_get(price_properties, "regularPrice.value")
                value = 0.0 if safe_get(price_properties, "free") else raw_value  # set value 0 if free is true

                offer = Offers(
                    url=safe_get(raw_offer, "url"),
                    category_type=safe_get(raw_offer, "category.type"),
                    is_active=safe_get(raw_offer, "isActive"),

                    title=safe_get(raw_offer, "title"),
                    description=safe_get(raw_offer, "description"),
                    params=params,
                    photos=safe_get(raw_offer, "photos", []),
                    item_condition=safe_get(raw_offer, "itemCondition"),

                    value=maybe(float, value),
                    currency_code=safe_get(raw_offer, "price.regularPrice.currencyCode"),
                    negotiable=safe_get(raw_offer, "price.regularPrice.negotiable"),
                    exchange=safe_get(raw_offer, "price.exchange"),
                    seller_paid_delivery=safe_get(raw_offer, "payAndShip.sellerPaidDeliveryEnabled"),

                    lat = safe_get(raw_offer, "map.lat"),
                    lon = safe_get(raw_offer, "map.lon"),
                    radius = safe_get(raw_offer, "map.radius"),

                    created_time=parse_iso_to_utc_datetime(safe_get(raw_offer, "createdTime")),
                    last_refresh_time=parse_iso_to_utc_datetime(safe_get(raw_offer, "lastRefreshTime")),
                    valid_to_time=parse_iso_to_utc_datetime(safe_get(raw_offer, "validToTime")),
                    last_scanned_time=get_current_utc_datetime()
                )
                upsert_offer(session, offer)
                count += 1

                logger.info(f"Title: {offer.title}")
                print(f"URL: {offer.url}")
                logger.info(f"Price: {offer.value}")
                logger.info(f"Params: {offer.params}")
                logger.info("-" * 50)
        return count
    finally:
        await context.close()
