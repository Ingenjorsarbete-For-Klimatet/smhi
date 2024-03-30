# generated by datamodel-codegen:
#   filename:  https://opendata-download-metanalys.smhi.se/api/category/mesan2g/version/1/geotype/polygon.json
#   timestamp: 2024-03-24T20:37:11+00:00

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame, Index, Series
from pydantic import BaseModel, ConfigDict, Field


class MetfctsValidTime(BaseModel):
    status: int
    headers: Dict[str, str]
    valid_time: List[str]


class MetfctsApprovedTime(BaseModel):
    status: int
    headers: Dict[str, str]
    approved_time: str
    reference_time: str


class MetfctsPolygon(BaseModel):
    status: int
    headers: Dict[str, str]
    type_: str = Field(..., alias="type")
    coordinates: List[List[List[float]]]


class MetfctsParameterItem(BaseModel):
    name: str
    key: str
    level_type: str = Field(..., alias="levelType")
    level: int
    unit: str
    missing_value: int = Field(..., alias="missingValue")


class MetfctsParameters(BaseModel):
    status: int
    headers: Dict[str, str]
    parameter: List[MetfctsParameterItem]


class MetfctsPointDataInfoSchema(pa.DataFrameModel):
    name: Index[str] = pa.Field(check_name=True, unique=True)
    level: Series[int]
    level_type: Series[str]
    unit: Series[str]


class MetfctsMultiPointDataSchema(pa.DataFrameModel):
    lat: Optional[Series[float]]
    lon: Optional[Series[float]]
    value: Series[float]


class MetfctsPointData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: int
    headers: Dict[str, str]
    approved_time: str
    reference_time: str
    level_unit: str

    df: pd.DataFrame
    df_info: DataFrame[MetfctsPointDataInfoSchema]


class MetfctsMultiPointData(BaseModel):
    status: int
    headers: Dict[str, str]
    parameter: str
    approved_time: str
    reference_time: str
    valid_time: str
    df: DataFrame[MetfctsMultiPointDataSchema]
