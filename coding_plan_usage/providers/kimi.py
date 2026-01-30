import httpx
from datetime import datetime
from ..models import UsageInfo
from ..config import ProviderConfig
from .base import BaseProvider


class KimiProvider(BaseProvider):
    """Kimi Coding Plan usage provider."""

    API_URL = "https://api.kimi.com/coding/v1/usages"

    @property
    def name(self) -> str:
        return "kimi"

    def authenticate(self) -> None:
        """Setup Bearer token authentication."""
        self._headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    async def fetch_usage(self) -> dict:
        """Fetch usage data from Kimi API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.API_URL,
                headers=self._headers,
            )
            response.raise_for_status()
            return response.json()

    def parse_usage(self, raw_data: dict) -> UsageInfo:
        """Parse Kimi response into standardized UsageInfo."""
        user = raw_data.get("user", {})
        usage = raw_data.get("usage", {})

        reset_time = usage.get("resetTime")
        if reset_time:
            reset_time = datetime.fromisoformat(reset_time.replace("Z", "+00:00"))

        return UsageInfo(
            provider=self.name,
            user_id=user.get("userId", ""),
            membership_level=user.get("membership", {}).get("level"),
            limit=usage.get("limit", "0"),
            used=usage.get("used", "0"),
            remaining=usage.get("remaining", "0"),
            reset_time=reset_time,
            raw_response=raw_data,
        )
