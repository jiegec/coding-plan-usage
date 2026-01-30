from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UsageInfo(BaseModel):
    """Standardized usage information across all providers."""
    provider: str
    user_id: str
    membership_level: Optional[str] = None
    limit: str
    used: str
    remaining: str
    reset_time: Optional[datetime] = None
    raw_response: dict
