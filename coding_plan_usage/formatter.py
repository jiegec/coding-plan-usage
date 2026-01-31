from datetime import datetime
from .models import UsageInfo, LimitDetail


def _format_datetime(dt: datetime | None) -> str | None:
    """Format datetime in local timezone and locale."""
    if dt is None:
        return None
    # Convert to local timezone
    local_dt = dt.astimezone()
    # Format with locale-aware datetime string
    return local_dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def _compute_percentage(used: str, limit: str) -> int | None:
    """Compute percentage from used and limit values."""
    try:
        used_val = int(used)
        limit_val = int(limit)
        if limit_val == 0:
            return None
        return int(used_val * 100 / limit_val)
    except (ValueError, TypeError):
        return None


def _format_time_window(limit: LimitDetail) -> str:
    """Format the time window for a rate limit."""
    # Handle BigModel time units
    if limit.time_unit == "hour":
        return f"{limit.duration} hour"
    elif limit.time_unit == "minute":
        return f"{limit.duration} minute"
    elif limit.time_unit == "day":
        return f"{limit.duration} day"
    elif limit.time_unit == "second":
        return f"{limit.duration} second"
    elif limit.time_unit == "TOKENS_LIMIT":
        return "total"
    else:
        # Handle TIME_UNIT_* format from other providers
        unit = limit.time_unit.replace("TIME_UNIT_", "").lower()
        return f"{limit.duration} {unit}"


def format_usage_simple(usages: list[UsageInfo]) -> str:
    """Format usage info in a simple readable format."""
    lines = []
    for usage in usages:
        lines.append(f"\n{'='*60}")
        lines.append(f"Provider: {usage.provider}")
        if usage.user_id:
            lines.append(f"User ID: {usage.user_id}")
        if usage.membership_level:
            lines.append(f"Membership: {usage.membership_level}")

        # Display rate limits from the limits list
        if usage.limits:
            lines.append("\n  Rate Limits:")
            for limit in usage.limits:
                time_window = _format_time_window(limit)

                limit_percentage = _compute_percentage(limit.used, limit.limit)
                percentage_str = f" ({limit_percentage}%)" if limit_percentage is not None else ""

                lines.append(f"    - {time_window}: {limit.used}/{limit.limit}{percentage_str} (remaining: {limit.remaining})")
                if limit.reset_time:
                    lines.append(f"      Reset: {_format_datetime(limit.reset_time)}")
                # Show usage details if available (e.g., BigModel TIME_LIMIT breakdown by model)
                if limit.usage_details:
                    lines.append("      Usage by model:")
                    for detail in limit.usage_details:
                        lines.append(f"        • {detail.model_code}: {detail.usage}")
        else:
            lines.append("\n  No rate limits available.")

    lines.append(f"\n{'='*60}")
    return "\n".join(lines)
