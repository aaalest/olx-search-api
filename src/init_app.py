# src/init_app.py
from sqlmodel import SQLModel
from config import DATA_DIR
from db.database import engine
import db.models  # Registers the Offers table with SQLModel metadata

def initialize_db() -> None:
    SQLModel.metadata.create_all(engine)
