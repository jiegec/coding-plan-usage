from abc import ABC, abstractmethod
from typing import Any

from ..config import ProviderConfig
from ..models import UsageInfo


class BaseProvider(ABC):
    """Abstract base class for Coding Plan usage providers."""

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self._headers: dict[str, str] = {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""

    @abstractmethod
    def authenticate(self) -> None:
        """Setup authentication headers/credentials."""

    @abstractmethod
    async def fetch_usage(self) -> Any:
        """Call provider API and return raw response data."""

    @abstractmethod
    def parse_usage(self, raw_data: dict) -> UsageInfo:
        """Convert raw response to standardized UsageInfo model."""
