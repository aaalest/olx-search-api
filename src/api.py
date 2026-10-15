from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlmodel import Session, select
from pydantic import BaseModel
from playwright.async_api import Browser, Playwright, async_playwright

from init_app import initialize_db
from db.database import engine
from db.models import Offers
from scraper import scrape_olx_offers
from logger import logger


class AppState:
    playwright: Playwright
    browser: Browser

class TypedFastAPI(FastAPI):
    state: AppState

@asynccontextmanager
async def lifespan(app: TypedFastAPI):
    initialize_db()

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    app.state.playwright = playwright
    app.state.browser = browser
    logger.info("[+] Playwright browser instance started")

    yield

    await app.state.browser.close()
    await app.state.playwright.stop()
    logger.info("[-] Playwright browser instance closed")


app = TypedFastAPI(title="OLX Search API", version="1.0", lifespan=lifespan)


def get_session():
    with Session(engine) as session:
        yield session

@app.get("/offers", response_model=List[Offers])
def read_offers(
        skip: int = 0,
        limit: int = Query(50, le=500, description="Max 500 items per request"),
        session: Session = Depends(get_session)
):
    statement = select(Offers).offset(skip).limit(limit)
    return session.exec(statement).all()


class ScrapeResponse(BaseModel):
    status: str
    message: str
    count: int

@app.post("/scrape", response_model=ScrapeResponse)
async def trigger_scrape(request: Request, url: str):
    try:
        browser = request.app.state.browser
        if not browser:
            raise HTTPException(status_code=500, detail="Browser instance not initialized.")

        count = await scrape_olx_offers(browser, url)

        return ScrapeResponse(
            status="success",
            message="Scrape completed and records updated.",
            count=count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
