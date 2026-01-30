import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Dict, Optional


class ProviderConfig(BaseModel):
    """Configuration for a single provider."""
    api_key: str


class Config(BaseModel):
    """Main configuration loaded from JSON file."""
    providers: Dict[str, ProviderConfig]


def load_config(config_path: str = "config.json") -> Config:
    """Load configuration from JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Transform provider configs to use ProviderConfig model
    providers = {}
    for name, cfg in data.get("providers", {}).items():
        providers[name] = ProviderConfig(api_key=cfg["api_key"])

    return Config(providers=providers)
