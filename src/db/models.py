from typing import Any
from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel
from datetime import datetime


class Offers(SQLModel, table=True):
    model_config = {"validate_assignment": True}
    __tablename__ = "offers"

    url: str = Field(primary_key=True)
    category_type: str = Field(index=True)
    is_active: bool = Field(index=True)

    # Content
    title: str = Field(index=True)
    description: str
    params: dict[str, Any] = Field(default_factory=dict, sa_type=JSON)
    photos: list = Field(default_factory=list, sa_type=JSON)
    item_condition: str = Field(index=True)

    # Price
    value: float | None = Field(default=None, index=True)
    currency_code: str | None = Field(default=None, index=True)
    negotiable: bool | None = Field(default=False, index=True)
    exchange: bool = Field(default=False, index=True)
    seller_paid_delivery: bool | None = Field(default=False, index=True)

    # Location
    lat: float | None = Field(default=None, index=True)
    lon: float | None = Field(default=None, index=True)
    radius: int | None = Field(default=None, index=True)

    # Time, UTC 0
    created_time: datetime = Field(index=True)
    last_refresh_time: datetime = Field(index=True)
    valid_to_time: datetime = Field(index=True)
    last_scanned_time: datetime = Field(index=True)


class ScheduledScrape(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    interval_minutes: int
    is_active: bool = Field(default=True)
    last_run_at: datetime | None = Field(default=None)
