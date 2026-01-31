import argparse
import asyncio
import sys

from .config import load_config, ProviderConfig
from .models import UsageInfo
from .providers.base import BaseProvider
from .providers.kimi import KimiProvider
from .providers.bigmodel import BigModelProvider
from .formatter import format_usage_simple
from .menubar import run_menubar


async def fetch_provider_usage(provider_name: str, provider_config: ProviderConfig) -> UsageInfo:
    """Fetch usage for a single provider."""
    provider: BaseProvider
    if provider_name == "kimi":
        provider = KimiProvider(provider_config)  # type: ignore[assignment]
    elif provider_name == "bigmodel":
        provider = BigModelProvider(provider_config)  # type: ignore[assignment]
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

    provider.authenticate()
    raw_data = await provider.fetch_usage()
    return provider.parse_usage(raw_data)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Coding Plan usage from multiple AI providers."
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file (default: config.json)",
    )
    parser.add_argument(
        "--menubar",
        action="store_true",
        help="Run as macOS menubar app (auto-refreshes every 5 minutes)",
    )
    args = parser.parse_args()

    if args.menubar:
        run_menubar(args.config)
        return

    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nPlease create a config.json file with the following structure:", file=sys.stderr)
        print('''
{
  "providers": {
    "kimi": {
      "api_key": "your-api-key"
    }
  }
}
''', file=sys.stderr)
        sys.exit(1)

    usages: list[UsageInfo] = []

    for provider_name, provider_config in config.providers.items():
        try:
            print(f"Fetching usage for {provider_name}...", file=sys.stderr)
            usage = await fetch_provider_usage(provider_name, provider_config)
            usages.append(usage)
        except Exception as e:
            print(f"Error fetching {provider_name} usage: {e}", file=sys.stderr)

    if usages:
        print(format_usage_simple(usages))
    else:
        print("No usage data retrieved.", file=sys.stderr)
        sys.exit(1)


def cli() -> None:
    """Synchronous entry point for CLI."""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
