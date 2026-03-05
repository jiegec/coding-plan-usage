import httpx
from ..models import UsageInfo, LimitDetail
from .base import BaseProvider


class InfiniProvider(BaseProvider):
    """Infini AI Coding Plan usage provider."""

    API_URL = "https://cloud.infini-ai.com/maas/coding/usage"

    @property
    def name(self) -> str:
        return "infini"

    def authenticate(self) -> None:
        """Setup Bearer token authentication."""
        self._headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    async def fetch_usage(self) -> dict:  # type: ignore[no-any-return]
        """Fetch usage data from Infini AI API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.API_URL,
                headers=self._headers,
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

    def _parse_window_key(self, window_key: str) -> tuple[int, str]:
        """Parse window key like '5_hour' or '30_day' into duration and time_unit."""
        parts = window_key.split("_")
        if len(parts) != 2:
            return (0, window_key)

        try:
            duration = int(parts[0])
        except ValueError:
            duration = 0

        time_unit = parts[1]
        return (duration, time_unit)

    def _parse_limits(self, raw_data: dict) -> list[LimitDetail]:
        """Parse rate limits from response."""
        limits = []

        for window_key, data in raw_data.items():
            duration, time_unit = self._parse_window_key(window_key)

            limits.append(
                LimitDetail(
                    duration=duration,
                    time_unit=time_unit,
                    limit=str(data.get("quota", 0)),
                    used=str(data.get("used", 0)),
                    remaining=str(data.get("remain", 0)),
                )
            )

        # Sort limits by time unit priority: hour < day < month
        unit_priority = {"hour": 0, "day": 1, "month": 2}
        limits.sort(key=lambda x: (unit_priority.get(x.time_unit, 3), x.duration))

        return limits

    def parse_usage(self, raw_data: dict) -> UsageInfo:
        """Parse Infini AI response into standardized UsageInfo."""
        limits = self._parse_limits(raw_data)

        return UsageInfo(
            provider=self.name,
            limits=limits,
            raw_response=raw_data,
        )
