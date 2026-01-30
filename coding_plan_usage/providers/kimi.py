import httpx
from datetime import datetime, timezone
from ..models import UsageInfo, LimitDetail
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

    def _parse_reset_time(self, reset_time_str: str | None) -> datetime | None:
        """Parse ISO format reset time string to datetime."""
        if not reset_time_str:
            return None
        return datetime.fromisoformat(reset_time_str.replace("Z", "+00:00"))

    def _parse_limits(self, raw_data: dict) -> list[LimitDetail]:
        """Parse rate limits from response."""
        limits = []
        for limit in raw_data.get("limits", []):
            window = limit.get("window", {})
            detail = limit.get("detail", {})

            reset_time = self._parse_reset_time(detail.get("resetTime"))

            limits.append(
                LimitDetail(
                    duration=window.get("duration", 0),
                    time_unit=window.get("timeUnit", ""),
                    limit=detail.get("limit", "0"),
                    used=detail.get("used", "0"),
                    remaining=detail.get("remaining", "0"),
                    reset_time=reset_time,
                )
            )
        return limits

    def parse_usage(self, raw_data: dict) -> UsageInfo:
        """Parse Kimi response into standardized UsageInfo."""
        user = raw_data.get("user", {})
        usage = raw_data.get("usage", {})

        reset_time = self._parse_reset_time(usage.get("resetTime"))
        limits = self._parse_limits(raw_data)

        return UsageInfo(
            provider=self.name,
            user_id=user.get("userId", ""),
            membership_level=user.get("membership", {}).get("level"),
            limit=usage.get("limit", "0"),
            used=usage.get("used", "0"),
            remaining=usage.get("remaining", "0"),
            reset_time=reset_time,
            limits=limits,
            raw_response=raw_data,
        )
