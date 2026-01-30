import httpx
from datetime import datetime, timezone
from ..models import UsageInfo, LimitDetail
from ..config import ProviderConfig
from .base import BaseProvider


class BigModelProvider(BaseProvider):
    """智谱 BigModel Coding Plan usage provider."""

    API_URL = "https://open.bigmodel.cn/api/monitor/usage/quota/limit"

    @property
    def name(self) -> str:
        return "bigmodel"

    def authenticate(self) -> None:
        """Setup access key authentication via Authorization header."""
        self._headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    async def fetch_usage(self) -> dict:
        """Fetch usage data from BigModel API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.API_URL,
                headers=self._headers,
            )
            response.raise_for_status()
            return response.json()

    def _parse_reset_time(self, timestamp_ms: int | None) -> datetime | None:
        """Parse millisecond timestamp to datetime."""
        if not timestamp_ms:
            return None
        return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)

    def _get_unit_name(self, unit: int) -> str:
        """Convert unit code to readable name."""
        unit_names = {
            1: "second",
            2: "minute",
            3: "hour",
            4: "day",
            5: "month",
            6: "year",
        }
        return unit_names.get(unit, f"unit_{unit}")

    def _parse_limits(self, raw_data: dict) -> list[LimitDetail]:
        """Parse rate limits from response."""
        limits = []
        data = raw_data.get("data", {})

        for limit in data.get("limits", []):
            limit_type = limit.get("type", "")
            unit = limit.get("unit", 0)
            number = limit.get("number", 1)

            reset_time = self._parse_reset_time(limit.get("nextResetTime"))

            # Convert BigModel's structure to LimitDetail
            # For tokens limit, duration doesn't apply the same way
            duration = number if limit_type == "TIME_LIMIT" else 0
            time_unit = self._get_unit_name(unit) if limit_type == "TIME_LIMIT" else limit_type

            limits.append(
                LimitDetail(
                    duration=duration,
                    time_unit=time_unit,
                    limit=str(limit.get("usage", 0)),
                    used=str(limit.get("currentValue", 0)),
                    remaining=str(limit.get("remaining", 0)),
                    reset_time=reset_time,
                )
            )
        return limits

    def parse_usage(self, raw_data: dict) -> UsageInfo:
        """Parse BigModel response into standardized UsageInfo."""
        data = raw_data.get("data", {})
        limits_data = data.get("limits", [])

        # Find the main quota (TOKENS_LIMIT) for primary usage display
        tokens_limit = None
        time_limit = None
        for limit in limits_data:
            if limit.get("type") == "TOKENS_LIMIT":
                tokens_limit = limit
            elif limit.get("type") == "TIME_LIMIT":
                time_limit = limit

        # Use tokens limit as primary if available, otherwise time limit
        primary_limit = tokens_limit or time_limit or {}

        reset_time = self._parse_reset_time(primary_limit.get("nextResetTime"))
        limits = self._parse_limits(raw_data)

        return UsageInfo(
            provider=self.name,
            user_id="",  # BigModel doesn't provide user ID in this response
            membership_level=None,
            limit=str(primary_limit.get("usage", 0)),
            used=str(primary_limit.get("currentValue", 0)),
            remaining=str(primary_limit.get("remaining", 0)),
            reset_time=reset_time,
            limits=limits,
            raw_response=raw_data,
        )
