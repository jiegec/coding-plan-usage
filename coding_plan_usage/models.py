from pydantic import BaseModel
from datetime import datetime


class UsageDetail(BaseModel):
    """Detail of usage for a specific model/feature."""
    model_code: str
    usage: int


class LimitDetail(BaseModel):
    """Rate limit detail for a specific time window."""
    duration: int
    time_unit: str
    limit: str
    used: str
    remaining: str
    reset_time: datetime | None = None
    usage_details: list[UsageDetail] = []


class UsageInfo(BaseModel):
    """Standardized usage information across all providers."""
    provider: str
    user_id: str | None = None
    membership_level: str | None = None
    limits: list[LimitDetail] = []
    raw_response: dict
