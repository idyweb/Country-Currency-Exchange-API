from typing import Annotated
from datetime import datetime, timezone

from fastapi import  Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, SQLModel, create_engine, Session, select


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


sqlite_file_name = "countries.db"
sqlite_url = f"sqlite:///{sqlite_file_name }"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]