from typing import List
from .models import UsageInfo


def format_usage_table(usages: List[UsageInfo]) -> str:
    """Format usage info as a readable table."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"{'Provider':<15} {'User ID':<25} {'Membership':<15} {'Used':<10} {'Limit':<10} {'Remaining':<10}")
    lines.append("-" * 80)

    for usage in usages:
        membership = usage.membership_level or "N/A"
        lines.append(
            f"{usage.provider:<15} {usage.user_id:<25} {membership:<15} "
            f"{usage.used:<10} {usage.limit:<10} {usage.remaining:<10}"
        )
        if usage.reset_time:
            lines.append(f"  Reset Time: {usage.reset_time}")
        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)


def format_usage_simple(usages: List[UsageInfo]) -> str:
    """Format usage info in a simple readable format."""
    lines = []
    for usage in usages:
        lines.append(f"\n{'='*60}")
        lines.append(f"Provider: {usage.provider}")
        lines.append(f"User ID: {usage.user_id}")
        if usage.membership_level:
            lines.append(f"Membership: {usage.membership_level}")
        lines.append(f"Usage: {usage.used} / {usage.limit} (Remaining: {usage.remaining})")
        if usage.reset_time:
            lines.append(f"Reset Time: {usage.reset_time}")

        if usage.limits:
            lines.append("\n  Rate Limits:")
            for limit in usage.limits:
                duration_unit = "min" if limit.time_unit == "TIME_UNIT_MINUTE" else limit.time_unit.replace("TIME_UNIT_", "").lower()
                lines.append(f"    - {limit.duration} {duration_unit}: {limit.used}/{limit.limit} (Remaining: {limit.remaining})")
                if limit.reset_time:
                    lines.append(f"      Reset: {limit.reset_time}")
    lines.append(f"\n{'='*60}")
    return "\n".join(lines)
