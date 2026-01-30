from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LimitDetail(BaseModel):
    """Rate limit detail for a specific time window."""
    duration: int
    time_unit: str
    limit: str
    used: str
    remaining: str
    reset_time: Optional[datetime] = None


class UsageInfo(BaseModel):
    """Standardized usage information across all providers."""
    provider: str
    user_id: str
    membership_level: Optional[str] = None
    limit: str
    used: str
    remaining: str
    reset_time: Optional[datetime] = None
    limits: List[LimitDetail] = []
    raw_response: dict
