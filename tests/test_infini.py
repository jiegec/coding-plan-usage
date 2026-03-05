import pytest
from coding_plan_usage.providers.infini import InfiniProvider
from coding_plan_usage.config import ProviderConfig


@pytest.fixture
def infini_provider():
    config = ProviderConfig(api_key="test-key")
    return InfiniProvider(config)


@pytest.fixture
def sample_infini_response():
    return {
        "5_hour": {"quota": 5000, "used": 0, "remain": 5000},
        "7_day": {"quota": 6000, "used": 0, "remain": 6000},
        "30_day": {"quota": 12000, "used": 0, "remain": 12000},
    }


def test_infini_authenticate(infini_provider):
    infini_provider.authenticate()
    assert infini_provider._headers["Authorization"] == "Bearer test-key"
    assert infini_provider._headers["Content-Type"] == "application/json"


def test_infini_parse_usage(infini_provider, sample_infini_response):
    usage = infini_provider.parse_usage(sample_infini_response)

    assert usage.provider == "infini"
    assert usage.raw_response == sample_infini_response
    assert len(usage.limits) == 3

    # Limits should be sorted by time unit priority: hour < day < month
    hour_limit = usage.limits[0]
    assert hour_limit.duration == 5
    assert hour_limit.time_unit == "hour"
    assert hour_limit.limit == "5000"
    assert hour_limit.used == "0"
    assert hour_limit.remaining == "5000"

    day_limit = usage.limits[1]
    assert day_limit.duration == 7
    assert day_limit.time_unit == "day"
    assert day_limit.limit == "6000"
    assert day_limit.used == "0"
    assert day_limit.remaining == "6000"

    month_limit = usage.limits[2]
    assert month_limit.duration == 30
    assert month_limit.time_unit == "day"
    assert month_limit.limit == "12000"
    assert month_limit.used == "0"
    assert month_limit.remaining == "12000"


def test_parse_window_key(infini_provider):
    assert infini_provider._parse_window_key("5_hour") == (5, "hour")
    assert infini_provider._parse_window_key("30_day") == (30, "day")
    assert infini_provider._parse_window_key("invalid") == (0, "invalid")
    assert infini_provider._parse_window_key("abc_def") == (0, "def")


def test_parse_usage_with_partial_data(infini_provider):
    """Test parsing with partial or missing data."""
    partial_response = {"24_hour": {"quota": 1000, "used": 100, "remain": 900}}

    usage = infini_provider.parse_usage(partial_response)
    assert len(usage.limits) == 1
    limit = usage.limits[0]
    assert limit.duration == 24
    assert limit.time_unit == "hour"
    assert limit.limit == "1000"
    assert limit.used == "100"
    assert limit.remaining == "900"
