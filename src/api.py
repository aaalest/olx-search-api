from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlmodel import Session, select
from pydantic import BaseModel
from playwright.async_api import Browser, Playwright, async_playwright

from init_app import initialize_db
from db.database import engine
from db.models import Offers, ScheduledScrape
from scraper import scrape_olx_offers
from logger import logger
from scheduler import scheduler, register_job, unregister_job, load_active_jobs_from_db


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

    scheduler.start()
    logger.info("[+] APScheduler started")
    load_active_jobs_from_db(browser)

    yield

    scheduler.shutdown(wait=False)
    logger.info("[-] APScheduler stopped")

    await app.state.browser.close()
    await app.state.playwright.stop()
    logger.info("[-] Playwright browser instance closed")


app = TypedFastAPI(title="OLX Search API", version="1.0", lifespan=lifespan)

# --- DTOs ---

class ScrapeResponse(BaseModel):
    status: str
    message: str
    count: int


class ScheduledScrapeCreate(BaseModel):
    url: str
    interval_minutes: int = Query(gt=0)


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


# --- Scheduled Jobs ---

class ScheduledScrapeUpdate(BaseModel):
    url: Optional[str] = None
    interval_minutes: Optional[int] = Query(None, gt=0)
    is_active: Optional[bool] = None

@app.get("/schedules", response_model=List[ScheduledScrape])
def list_scheduled_scrapes(session: Session = Depends(get_session)):
    return session.exec(select(ScheduledScrape)).all()

@app.post("/schedules", response_model=ScheduledScrape)
def create_scheduled_scrape(
    request: Request,
    payload: ScheduledScrapeCreate,
    session: Session = Depends(get_session)
):
    job = ScheduledScrape(
        url=payload.url,
        interval_minutes=payload.interval_minutes,
        is_active=True
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    if job.id is not None:
        register_job(job.id, job.url, job.interval_minutes, request.app.state.browser)

    return job

@app.patch("/schedules/{schedule_id}", response_model=ScheduledScrape)
def update_scheduled_scrape(
    schedule_id: int,
    payload: ScheduledScrapeUpdate,
    request: Request,
    session: Session = Depends(get_session)
):
    job = session.get(ScheduledScrape, schedule_id)
    if not job:
        raise HTTPException(status_code=404, detail="Schedule not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(job, key, value)

    session.add(job)
    session.commit()
    session.refresh(job)

    # Sync APScheduler
    if job.is_active:
        # Re-registers or updates trigger interval with replace_existing=True
        register_job(job.id, job.url, job.interval_minutes, request.app.state.browser)
    else:
        unregister_job(job.id)

    return job

@app.delete("/schedules/{schedule_id}")
def delete_scheduled_scrape(
    schedule_id: int,
    session: Session = Depends(get_session)
):
    job = session.get(ScheduledScrape, schedule_id)
    if not job:
        raise HTTPException(status_code=404, detail="Schedule not found")

    unregister_job(schedule_id)
    session.delete(job)
    session.commit()

    return {"status": "success", "message": f"Schedule {schedule_id} removed"}
