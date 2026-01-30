# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool to fetch and display Coding Plan usage from multiple AI providers (智谱 BigModel, Kimi, etc.).

## Development Commands

```bash
# Install dependencies
poetry install

# Run the tool
poetry run python -m coding_plan_usage

# Run with specific config file
poetry run python -m coding_plan_usage --config config.json

# Run tests
poetry run pytest

# Run specific test
poetry run pytest tests/test_kimi.py -v

# Type checking
poetry run mypy coding_plan_usage/

# Linting
poetry run ruff check .

# Add new dependency
poetry add <package>

# Add dev dependency
poetry add --group dev <package>
```

## Project Structure

```
coding_plan_usage/
├── __init__.py          # Package init
├── __main__.py          # CLI entry point
├── config.py            # Configuration loading/validation
├── providers/
│   ├── __init__.py
│   ├── base.py          # Abstract base class for providers
│   ├── bigmodel.py      # 智谱 BigModel API client
│   └── kimi.py          # Kimi API client
├── models.py            # Pydantic data models for responses
└── formatter.py         # Output formatting (table, JSON, etc.)
```

## Configuration Format

The tool reads a JSON config file with provider credentials:

```json
{
  "providers": {
    "bigmodel": {
      "api_key": "your-access-key"
    },
    "kimi": {
      "api_key": "your-api-key"
    }
  }
}
```

## Provider API Endpoints

- **智谱 BigModel**: `https://open.bigmodel.cn/api/monitor/usage/quota/limit`
  - Uses access key authentication
- **Kimi**: `https://api.kimi.com/coding/v1/usages`
  - Uses API key authentication

## Architecture

The provider pattern uses an abstract base class (`providers/base.py`) that defines:
- `authenticate()`: Setup auth headers/credentials
- `fetch_usage()`: Call provider API and return raw data
- `parse_usage()`: Convert raw response to standardized `UsageInfo` model

Each provider implements these methods. The main module iterates over configured providers, aggregates results, and formats output.

## Key Implementation Notes

- Use `pydantic` for config validation and data modeling
- Use `httpx` for HTTP requests (supports both sync and async)
- Handle API errors gracefully with try/except blocks
- Support multiple output formats: table (default), JSON
