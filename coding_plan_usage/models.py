from pydantic import BaseModel
from typing import Optional, List
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
    reset_time: Optional[datetime] = None
    usage_details: List[UsageDetail] = []


class UsageInfo(BaseModel):
    """Standardized usage information across all providers."""
    provider: str
    user_id: Optional[str] = None
    membership_level: Optional[str] = None
    limit: str
    used: str
    remaining: str
    reset_time: Optional[datetime] = None
    limits: List[LimitDetail] = []
    raw_response: dict
