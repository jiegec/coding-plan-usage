# Coding Plan Usage

A CLI tool to fetch and display Coding Plan usage from multiple AI providers.

## Supported Providers

- **Kimi** - https://api.kimi.com/coding/v1/usages
- **智谱 BigModel** - https://open.bigmodel.cn/api/monitor/usage/quota/limit (planned)

## Installation

```bash
poetry install
```

## Configuration

Create a `config.json` file:

```json
{
  "providers": {
    "kimi": {
      "api_key": "your-kimi-api-key"
    }
  }
}
```

## Usage

```bash
# Run with default config.json
poetry run python -m coding_plan_usage

# Run with specific config file
poetry run python -m coding_plan_usage --config /path/to/config.json
```

## Development

```bash
# Run tests
poetry run pytest

# Type checking
poetry run mypy coding_plan_usage/

# Linting
poetry run ruff check .
```
