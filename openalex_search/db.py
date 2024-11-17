from typing import Any

import requests
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sqlmodel import Field, SQLModel, create_engine

from openalex_search.config import EMBEDDING_DIMS


class Work(SQLModel, table=True):
    id: str = Field(primary_key=True)
    doi: str
    title: str
    display_name: str
    publication_year: int
    publication_date: str
    type: str
    cited_by_count: int
    is_retracted: bool
    is_paratext: bool
    is_oa: bool
    pdf_url: str | None
    landing_page_url: str | None
    journal: str
    abstract: str | None = Field(default=None)
    embedding: Any = Field(default=None, sa_column=Column(Vector(EMBEDDING_DIMS)))

    @classmethod
    def pull(cls, doi: str):
        """Pull a work from the OpenAlex by DOI."""
        response = requests.get(f"https://api.openalex.org/works/doi:{doi}")
        response.raise_for_status()
        data = response.json()

        return cls(
            id=data["id"],
            doi=data["doi"],
            title=data["title"],
            display_name=data["display_name"],
            publication_year=data["publication_year"],
            publication_date=data["publication_date"],
            type=data["type"],
            cited_by_count=data["cited_by_count"],
            is_retracted=data["is_retracted"],
            is_paratext=data["is_paratext"],
            is_oa=data["best_oa_location"]["is_oa"],
            pdf_url=data["best_oa_location"]["pdf_url"],
            landing_page_url=data["best_oa_location"]["landing_page_url"],
            journal=data["primary_location"]["source"]["display_name"],
        )


# create a session
engine = create_engine("postgresql://postgres:postgres@localhost/dev")


def init(wipe: bool = False) -> None:
    """Initialize the database."""

    with Session(engine) as session:
        session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        session.commit()

        if wipe:
            session.execute(text("DROP TABLE IF EXISTS work"))
            session.commit()
        SQLModel.metadata.create_all(engine)
