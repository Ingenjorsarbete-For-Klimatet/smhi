# generated by datamodel-codegen:
#   filename:  https://opendata-download-metobs.smhi.se/api/version/1.0/parameter/1/station/1.json
#   timestamp: 2024-03-23T16:55:01+00:00

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class PositionItem(BaseModel):
    from_: int = Field(..., alias="from")
    to: int
    height: float
    latitude: float
    longitude: float


class LinkItem(BaseModel):
    href: str
    rel: str
    type: str


class PeriodItem(BaseModel):
    key: str
    updated: int
    title: str
    summary: str
    link: List[LinkItem]


class PeriodModel(BaseModel):
    key: str
    updated: int
    title: str
    owner: str
    ownerCategory: str
    measuringStations: str
    active: bool
    summary: str
    from_: int = Field(..., alias="from")
    to: int
    position: List[PositionItem]
    link: List[LinkItem]
    period: List[PeriodItem]
