import pytest
from datetime import datetime, timezone
from coding_plan_usage.providers.kimi import KimiProvider
from coding_plan_usage.config import ProviderConfig


@pytest.fixture
def kimi_provider():
    config = ProviderConfig(api_key="test-key")
    return KimiProvider(config)


@pytest.fixture
def sample_kimi_response():
    return {
        "user": {
            "userId": "11111111111111111111",
            "region": "REGION_CN",
            "membership": {
                "level": "LEVEL_TRIAL"
            },
            "businessId": ""
        },
        "usage": {
            "limit": "100",
            "used": "13",
            "remaining": "87",
            "resetTime": "2026-02-06T08:31:59.863136Z"
        },
        "limits": [
            {
                "window": {
                    "duration": 300,
                    "timeUnit": "TIME_UNIT_MINUTE"
                },
                "detail": {
                    "limit": "100",
                    "used": "65",
                    "remaining": "35",
                    "resetTime": "2026-01-30T13:31:59.863136Z"
                }
            }
        ]
    }


def test_kimi_authenticate(kimi_provider):
    kimi_provider.authenticate()
    assert kimi_provider._headers["Authorization"] == "Bearer test-key"
    assert kimi_provider._headers["Content-Type"] == "application/json"


def test_kimi_parse_usage(kimi_provider, sample_kimi_response):
    usage = kimi_provider.parse_usage(sample_kimi_response)

    assert usage.provider == "kimi"
    assert usage.user_id == "11111111111111111111"
    assert usage.membership_level == "LEVEL_TRIAL"
    assert usage.raw_response == sample_kimi_response

    # Test rate limits parsing - should have weekly limit + any additional limits
    assert len(usage.limits) == 2

    # First limit is the weekly limit from top-level usage object
    weekly_limit = usage.limits[0]
    assert weekly_limit.duration == 1
    assert weekly_limit.time_unit == "week"
    assert weekly_limit.limit == "100"
    assert weekly_limit.used == "13"
    assert weekly_limit.remaining == "87"
    assert weekly_limit.reset_time == datetime(2026, 2, 6, 8, 31, 59, 863136, tzinfo=timezone.utc)

    # Second limit is the 300 minute limit from limits array
    minute_limit = usage.limits[1]
    assert minute_limit.duration == 300
    assert minute_limit.time_unit == "minute"
    assert minute_limit.limit == "100"
    assert minute_limit.used == "65"
    assert minute_limit.remaining == "35"
    assert minute_limit.reset_time == datetime(2026, 1, 30, 13, 31, 59, 863136, tzinfo=timezone.utc)
