import pytest
from datetime import datetime, timezone
from coding_plan_usage.providers.bigmodel import BigModelProvider
from coding_plan_usage.config import ProviderConfig


@pytest.fixture
def bigmodel_provider():
    config = ProviderConfig(api_key="test-access-key")
    return BigModelProvider(config)


@pytest.fixture
def sample_bigmodel_response():
    return {
        "code": 200,
        "msg": "操作成功",
        "data": {
            "limits": [
                {
                    "type": "TOKENS_LIMIT",
                    "unit": 3,
                    "number": 5,
                    "percentage": 42,
                    "nextResetTime": 1769776934422,
                },
                {
                    "type": "TIME_LIMIT",
                    "unit": 5,
                    "number": 1,
                    "usage": 100,
                    "currentValue": 92,
                    "remaining": 8,
                    "percentage": 92,
                    "nextResetTime": 1769776934422,
                    "usageDetails": [
                        {"modelCode": "search-prime", "usage": 83},
                        {"modelCode": "web-reader", "usage": 9},
                        {"modelCode": "zread", "usage": 0},
                    ],
                },
            ],
            "level": "lite",
        },
        "success": True,
    }


def test_bigmodel_authenticate(bigmodel_provider):
    bigmodel_provider.authenticate()
    assert bigmodel_provider._headers["Authorization"] == "Bearer test-access-key"
    assert bigmodel_provider._headers["Content-Type"] == "application/json"


def test_bigmodel_parse_usage(bigmodel_provider, sample_bigmodel_response):
    usage = bigmodel_provider.parse_usage(sample_bigmodel_response)

    assert usage.provider == "bigmodel"
    assert usage.user_id is None  # BigModel doesn't provide user ID
    assert usage.membership_level == "lite"

    # Test limits parsing
    assert len(usage.limits) == 2

    # TOKENS_LIMIT - returns percentage-based values
    tokens_limit = usage.limits[0]
    assert tokens_limit.duration == 5
    assert tokens_limit.time_unit == "hour"
    assert tokens_limit.limit == "100"
    assert tokens_limit.used == "42"
    assert tokens_limit.remaining == "58"
    assert tokens_limit.reset_time == datetime(
        2026, 1, 30, 12, 42, 14, 422000, tzinfo=timezone.utc
    )

    # TIME_LIMIT - returns actual usage values
    time_limit = usage.limits[1]
    assert time_limit.duration == 1
    assert time_limit.time_unit == "month"
    assert time_limit.limit == "100"
    assert time_limit.used == "92"
    assert time_limit.remaining == "8"
    assert time_limit.reset_time == datetime(
        2026, 1, 30, 12, 42, 14, 422000, tzinfo=timezone.utc
    )
    # Test usage_details parsing
    assert len(time_limit.usage_details) == 3
    assert time_limit.usage_details[0].model_code == "search-prime"
    assert time_limit.usage_details[0].usage == 83
    assert time_limit.usage_details[1].model_code == "web-reader"
    assert time_limit.usage_details[1].usage == 9
    assert time_limit.usage_details[2].model_code == "zread"
    assert time_limit.usage_details[2].usage == 0


def test_bigmodel_get_unit_name(bigmodel_provider):
    assert bigmodel_provider._get_unit_name(1) == "second"
    assert bigmodel_provider._get_unit_name(2) == "minute"
    assert bigmodel_provider._get_unit_name(3) == "hour"
    assert bigmodel_provider._get_unit_name(4) == "day"
    assert bigmodel_provider._get_unit_name(5) == "month"
    assert bigmodel_provider._get_unit_name(6) == "year"
    assert bigmodel_provider._get_unit_name(99) == "unit_99"


def test_bigmodel_parse_reset_time(bigmodel_provider):
    # Test with valid timestamp
    dt = bigmodel_provider._parse_reset_time(1769776934422)
    assert dt == datetime(2026, 1, 30, 12, 42, 14, 422000, tzinfo=timezone.utc)

    # Test with None
    assert bigmodel_provider._parse_reset_time(None) is None
