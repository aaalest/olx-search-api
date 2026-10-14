from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel

from db.database import engine
from db.models import Offers
from scraper import scrape_olx_offers


app = FastAPI(title="OLX Search API", version="1.0")


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
async def trigger_scrape(url: str):
    try:
        count = await scrape_olx_offers(url)

        return ScrapeResponse(
            status="success",
            message="Scrape completed and records updated.",
            count=count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
