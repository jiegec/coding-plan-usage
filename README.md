# Coding Plan Usage

A CLI tool to fetch and display Coding Plan usage from multiple AI providers.

## Supported Providers

- **Kimi** - https://api.kimi.com/coding/v1/usages
- **智谱 BigModel** - https://open.bigmodel.cn/api/monitor/usage/quota/limit

## Installation

```bash
git clone https://github.com/jiegec/coding-plan-usage
cd coding-plan-usage
poetry install
```

## Configuration

Create a config file at `~/.coding_plan_usage_config.json`:

```json
{
  "providers": {
    "kimi": {
      "api_key": "your-kimi-api-key"
    },
    "bigmodel": {
      "api_key": "your-bigmodel-access-key"
    }
  }
}
```

Or use a custom config path (see usage below).

## Usage

### CLI Mode

```bash
# Run with default config at ~/.coding_plan_usage_config.json
poetry run coding-plan-usage

# Run with specific config file
poetry run coding-plan-usage --config /path/to/config.json
```

### macOS Menubar App

```bash
# Run menubar app with default config
poetry run coding-plan-usage-menubar

# Run menubar app with specific config file
poetry run coding-plan-usage-menubar --config /path/to/config.json
```

**Menubar Features:**

- Displays current usage percentage for each configured provider in the menu bar (e.g., `kimi: 13% | bigmodel: 45%`)
- Auto-refreshes every 5 minutes
- Click the menu bar icon to open dropdown menu with:
  - **Refresh Now** - Manually trigger a refresh
  - **Copy Status** - Copy detailed usage info to clipboard
  - **Last updated** - Shows when data was last refreshed
  - **Quit** - Exit the application

## Development

```bash
# Run tests
poetry run pytest

# Type checking
poetry run mypy coding_plan_usage/

# Linting
poetry run ruff check .
```
