from sqlmodel import create_engine


DATABASE_URL = "postgresql+psycopg://olx_search_user:secure_password@localhost:5432/olx_search_db"
engine = create_engine(DATABASE_URL, echo=True)
