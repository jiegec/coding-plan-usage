import json
from pathlib import Path
from pydantic import BaseModel
from typing import Dict


class ProviderConfig(BaseModel):
    """Configuration for a single provider."""
    api_key: str


class Config(BaseModel):
    """Main configuration loaded from JSON file."""
    providers: Dict[str, ProviderConfig]


def load_config(config_path: str | None = None) -> Config:
    """Load configuration from JSON file.

    If config_path is not provided, defaults to ~/.coding_plan_usage_config.json
    """
    if config_path is None:
        path = Path.home() / ".coding_plan_usage_config.json"
    else:
        path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Transform provider configs to use ProviderConfig model
    providers = {}
    for name, cfg in data.get("providers", {}).items():
        providers[name] = ProviderConfig(api_key=cfg["api_key"])

    return Config(providers=providers)
