from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from playwright.async_api import Browser
from sqlmodel import Session, select

from db.database import engine
from db.models import ScheduledScrape
from scraper import scrape_olx_offers
from logger import logger

scheduler = AsyncIOScheduler()


async def execute_scheduled_scrape(scrape_id: int, url: str, browser: Browser) -> None:
    logger.info(f"[Scheduler] Starting task {scrape_id} for {url}")
    try:
        count = await scrape_olx_offers(browser, url)
        logger.info(f"[Scheduler] Task {scrape_id} finished. Scraped {count} offers.")
    except Exception as e:
        logger.error(f"[Scheduler] Error executing task {scrape_id}: {e}")
        return

    with Session(engine) as session:
        statement = select(ScheduledScrape).where(ScheduledScrape.id == scrape_id)
        job_record = session.exec(statement).first()
        if job_record:
            job_record.last_run_at = datetime.now(timezone.utc)
            session.add(job_record)
            session.commit()


def register_job(job_id: int, url: str, interval_minutes: int, browser: Browser) -> None:
    scheduler.add_job(
        execute_scheduled_scrape,
        trigger="interval",
        minutes=interval_minutes,
        id=str(job_id),
        replace_existing=True,
        args=[job_id, url, browser]
    )


def unregister_job(job_id: int) -> None:
    job_str_id = str(job_id)
    if scheduler.get_job(job_str_id):
        scheduler.remove_job(job_str_id)


def load_active_jobs_from_db(browser: Browser) -> None:
    with Session(engine) as session:
        statement = select(ScheduledScrape).where(ScheduledScrape.is_active == True)
        active_jobs = session.exec(statement).all()
        for job in active_jobs:
            if job.id is not None:
                register_job(job.id, job.url, job.interval_minutes, browser)
                logger.info(f"[Scheduler] Restored job {job.id} ({job.url}) from database")
