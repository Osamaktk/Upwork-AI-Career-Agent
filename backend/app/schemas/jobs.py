from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class SampleClient(BaseModel):
    source_client_id: str
    name: str | None = None
    facts: list[dict[str, Any]] = Field(default_factory=list)


class SampleJob(BaseModel):
    source: Literal["sample"]
    source_job_id: str
    title: str
    description: str
    budget_type: Literal["fixed", "hourly"]
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    currency: str = "USD"
    required_skills: list[str]
    posted_at: datetime
    source_url: HttpUrl | None = None
    client: SampleClient
    raw_data: dict[str, Any] = Field(default_factory=dict)
