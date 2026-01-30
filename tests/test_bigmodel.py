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
                    "usage": 40000000,
                    "currentValue": 16931403,
                    "remaining": 23068597,
                    "percentage": 42,
                    "nextResetTime": 1769776934422
                },
                {
                    "type": "TIME_LIMIT",
                    "unit": 5,
                    "number": 1,
                    "usage": 100,
                    "currentValue": 92,
                    "remaining": 8,
                    "percentage": 92,
                    "usageDetails": [
                        {
                            "modelCode": "search-prime",
                            "usage": 83
                        },
                        {
                            "modelCode": "web-reader",
                            "usage": 9
                        }
                    ]
                }
            ]
        },
        "success": True
    }


def test_bigmodel_authenticate(bigmodel_provider):
    bigmodel_provider.authenticate()
    assert bigmodel_provider._headers["Authorization"] == "Bearer test-access-key"
    assert bigmodel_provider._headers["Content-Type"] == "application/json"


def test_bigmodel_parse_usage(bigmodel_provider, sample_bigmodel_response):
    usage = bigmodel_provider.parse_usage(sample_bigmodel_response)

    assert usage.provider == "bigmodel"
    assert usage.user_id is None  # BigModel doesn't provide user ID
    assert usage.membership_level is None
    # TOKENS_LIMIT is used as primary
    assert usage.limit == "40000000"
    assert usage.used == "16931403"
    assert usage.remaining == "23068597"
    assert usage.reset_time == datetime(2026, 1, 30, 12, 42, 14, 422000, tzinfo=timezone.utc)

    # Test limits parsing
    assert len(usage.limits) == 2

    # TOKENS_LIMIT
    tokens_limit = usage.limits[0]
    assert tokens_limit.duration == 0
    assert tokens_limit.time_unit == "TOKENS_LIMIT"
    assert tokens_limit.limit == "40000000"
    assert tokens_limit.used == "16931403"
    assert tokens_limit.remaining == "23068597"

    # TIME_LIMIT
    time_limit = usage.limits[1]
    assert time_limit.duration == 1
    assert time_limit.time_unit == "month"
    assert time_limit.limit == "100"
    assert time_limit.used == "92"
    assert time_limit.remaining == "8"
    # Test usage_details parsing
    assert len(time_limit.usage_details) == 2
    assert time_limit.usage_details[0].model_code == "search-prime"
    assert time_limit.usage_details[0].usage == 83
    assert time_limit.usage_details[1].model_code == "web-reader"
    assert time_limit.usage_details[1].usage == 9


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
