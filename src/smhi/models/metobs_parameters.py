# generated by datamodel-codegen:
#   filename:  https://opendata-download-metobs.smhi.se/api/version/1.0.json
#   timestamp: 2024-03-23T21:07:52+00:00

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class LinkItem(BaseModel):
    href: str
    rel: str
    type: str


class GeoBox(BaseModel):
    min_latitude: float = Field(..., alias="minLatitude")
    min_longitude: float = Field(..., alias="minLongitude")
    max_latitude: float = Field(..., alias="maxLatitude")
    max_longitude: float = Field(..., alias="maxLongitude")


class ResourceItem(BaseModel):
    key: str | None
    updated: int | None
    title: str
    summary: str
    link: List[LinkItem]
    unit: str
    geo_box: GeoBox = Field(..., alias="geoBox")


class ParameterModel(BaseModel):
    key: str | None
    updated: int | None
    title: str
    summary: str
    link: List[LinkItem]
    resource: List[ResourceItem]
