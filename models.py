from typing import Annotated
from datetime import datetime, timezone

from fastapi import  Depends
from sqlmodel import Field, SQLModel, create_engine, Session
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///countries.db") 

class Countries(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    capital: str | None = None
    region: str | None = None
    population: int
    currency_code: str | None = Field(default=None, nullable=True)
    exchange_rate: float | None = Field(default=None, nullable=True)
    estimated_gdp: float | None = Field(default=None, nullable=True)
    flag_url: str | None = None
    last_refreshed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]