"""Pydantic request/response schemas."""
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Unit = Literal["count", "duration", "boolean"]
Aggregation = Literal["sum", "max", "last"]
SourceType = Literal["github", "webhook", "manual"]


class MetricCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    icon: str = "📊"
    color: str = "#3fb950"
    unit: Unit = "count"
    aggregation: Aggregation = "sum"
    source_type: SourceType = "manual"


class MetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: str
    color: str
    unit: Unit
    aggregation: Aggregation
    source_type: SourceType
    created_at: datetime


class MetricWithStats(MetricOut):
    today_value: Optional[float] = None
    streak: int = 0
    total_days_tracked: int = 0


class MetricEventCreate(BaseModel):
    date: date
    value: float
    meta: dict = Field(default_factory=dict)


class MetricEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    value: float
    meta: dict
