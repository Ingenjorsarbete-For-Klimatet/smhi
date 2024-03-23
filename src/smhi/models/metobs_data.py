# generated by datamodel-codegen:
#   filename:  https://opendata-download-metobs.smhi.se/api/version/1.0/parameter/1/station/1/period/corrected-archive.json
#   timestamp: 2024-03-23T21:07:54+00:00

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class LinkItem(BaseModel):
    href: str
    rel: str
    type: str


class Datum(BaseModel):
    key: str | None
    updated: int | None
    title: str
    summary: str
    link: List[LinkItem]


class DataModel(BaseModel):
    key: str | None
    updated: int | None
    title: str
    summary: str
    from_: int = Field(..., alias="from")
    to: int
    link: List[LinkItem]
    data: List[Datum]
