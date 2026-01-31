"""macOS menubar app for displaying Coding Plan usage using native AppKit."""

import asyncio
import os
import sys
import threading
from datetime import datetime
from typing import Any

from .config import load_config, ProviderConfig
from .models import UsageInfo, LimitDetail
from .providers.kimi import KimiProvider
from .providers.bigmodel import BigModelProvider

# Import AppKit for native macOS menu bar
import AppKit  # type: ignore[import-untyped]
import Foundation  # type: ignore[import-untyped]
import objc  # type: ignore[import-untyped]


class AppDelegate(AppKit.NSObject):  # type: ignore[misc]
    """App delegate to handle menu actions."""

    status_bar: Any = None

    @objc.typedSelector(b'v@:@')  # type: ignore[misc]
    def refresh_(self, _sender: Any) -> None:
        """Handle refresh action."""
        if self.status_bar:
            self.status_bar.refresh_data()

    @objc.typedSelector(b'v@:@')  # type: ignore[misc]
    def copyStatus_(self, _sender: Any) -> None:
        """Handle copy status action."""
        if self.status_bar:
            self.status_bar._do_copy_status()

    @objc.typedSelector(b'v@:@')  # type: ignore[misc]
    def scheduledRefresh_(self, _timer: Any) -> None:
        """Handle scheduled refresh."""
        if self.status_bar:
            self.status_bar.refresh_data()


class UsageStatusBar:
    """Native macOS status bar app."""

    def __init__(self, config_path: str | None = None) -> None:
        print("DEBUG: Initializing UsageStatusBar", file=sys.stderr)
        if config_path is None:
            # Default to ~/.coding_plan_usage_config.json
            home_dir = os.path.expanduser("~")
            config_path = os.path.join(home_dir, ".coding_plan_usage_config.json")
        self.config_path = config_path
        print(f"DEBUG: Config path: {config_path}", file=sys.stderr)
        self.config: Any = None
        self.current_usage_data: list[UsageInfo] = []
        self.last_updated: datetime | None = None
        self.current_status_text = ""

        # Get or create the shared application
        print("DEBUG: Getting NSApplication", file=sys.stderr)
        self.app = AppKit.NSApplication.sharedApplication()
        print(f"DEBUG: NSApplication: {self.app}", file=sys.stderr)

        # Set activation policy to accessory (no dock icon)
        print("DEBUG: Setting activation policy", file=sys.stderr)
        self.app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)

        # Create delegate
        self.delegate = AppDelegate.alloc().init()
        self.delegate.status_bar = self
        self.app.setDelegate_(self.delegate)

        # Create status bar item
        print("DEBUG: Creating status bar item", file=sys.stderr)
        self.status_bar = AppKit.NSStatusBar.systemStatusBar()
        self.status_item = self.status_bar.statusItemWithLength_(
            AppKit.NSVariableStatusItemLength
        )
        print(f"DEBUG: Status item: {self.status_item}", file=sys.stderr)

        # Important: retain the status item to prevent GC
        self.status_item.retain()

        # Set initial title
        if self.status_item.button():
            self.status_item.button().setTitle_("⏳")
            print("DEBUG: Set initial title", file=sys.stderr)
        else:
            print("DEBUG: No button available!", file=sys.stderr)

        # Create menu
        print("DEBUG: Setting up menu", file=sys.stderr)
        self._setup_menu()

    def _setup_menu(self) -> None:
        """Set up the menu."""
        self.menu = AppKit.NSMenu.alloc().init()

        # Add menu items
        refresh_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Refresh Now", "refresh:", ""
        )
        refresh_item.setTarget_(self.delegate)
        self.menu.addItem_(refresh_item)

        copy_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Copy Status", "copyStatus:", ""
        )
        copy_item.setTarget_(self.delegate)
        self.menu.addItem_(copy_item)

        self.menu.addItem_(AppKit.NSMenuItem.separatorItem())

        self.last_updated_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Last updated: Never", None, ""
        )
        self.menu.addItem_(self.last_updated_item)

        self.menu.addItem_(AppKit.NSMenuItem.separatorItem())

        quit_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "terminate:", "q"
        )
        quit_item.setTarget_(AppKit.NSApp())
        self.menu.addItem_(quit_item)

        # Set menu
        self.status_item.setMenu_(self.menu)

    def _do_copy_status(self) -> None:
        """Copy status to clipboard."""
        if self.current_status_text:
            pasteboard = AppKit.NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            pasteboard.setString_forType_(self.current_status_text, AppKit.NSPasteboardTypeString)

    def refresh_data(self) -> None:
        """Refresh usage data (runs in background thread)."""
        if self.status_item.button():
            self.status_item.button().setTitle_("⏳")
        thread = threading.Thread(target=self._run_async_fetch)
        thread.daemon = True
        thread.start()

    def _run_async_fetch(self) -> None:
        """Run the async fetch in a new event loop."""
        print("DEBUG: Starting async fetch", file=sys.stderr)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            print("DEBUG: About to fetch usage data", file=sys.stderr)
            usages = loop.run_until_complete(self._fetch_all_usage())
            print(f"DEBUG: Got {len(usages)} usage results", file=sys.stderr)
            self.current_usage_data = usages
            self.last_updated = datetime.now()
            # Update UI on main thread
            print("DEBUG: Scheduling UI update", file=sys.stderr)
            Foundation.NSOperationQueue.mainQueue().addOperationWithBlock_(
                lambda: self._update_display()
            )
        finally:
            loop.close()

    async def _fetch_all_usage(self) -> list[UsageInfo]:
        """Fetch usage from all configured providers."""
        if self.config is None:
            try:
                self.config = load_config(self.config_path)
            except FileNotFoundError:
                return []
            except Exception:
                return []

        usages: list[UsageInfo] = []
        tasks = []

        for provider_name, provider_config in self.config.providers.items():
            tasks.append(self._fetch_provider_usage(provider_name, provider_config))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, UsageInfo):
                usages.append(result)

        return usages

    async def _fetch_provider_usage(
        self, provider_name: str, provider_config: ProviderConfig
    ) -> UsageInfo | None:
        """Fetch usage for a single provider."""
        try:
            if provider_name == "kimi":
                provider = KimiProvider(provider_config)  # type: ignore[assignment]
            elif provider_name == "bigmodel":
                provider = BigModelProvider(provider_config)  # type: ignore[assignment]
            else:
                return None

            provider.authenticate()
            raw_data = await provider.fetch_usage()
            return provider.parse_usage(raw_data)
        except Exception as e:
            return UsageInfo(
                provider=provider_name,
                limits=[],
                raw_response={"error": str(e)},
            )

    def _update_display(self) -> None:
        """Update the menubar display with current data."""
        print("DEBUG: _update_display called", file=sys.stderr)
        if not self.current_usage_data:
            if self.status_item.button():
                self.status_item.button().setTitle_("❌")
            return

        # Build status lines for each provider
        status_parts = []
        has_error = False

        for usage in self.current_usage_data:
            if usage.limits:
                status_parts.append(self._format_status_line(usage))
            else:
                has_error = True

        if status_parts:
            title = " | ".join(status_parts)
            if has_error:
                title += " ⚠️"
        else:
            title = "❌"

        if self.status_item.button():
            print(f"DEBUG: Setting title to: {title}", file=sys.stderr)
            self.status_item.button().setTitle_(title)
            print("DEBUG: Title set successfully", file=sys.stderr)
        else:
            print("DEBUG: Cannot set title - no button!", file=sys.stderr)

        # Update last updated time
        if self.last_updated:
            self.last_updated_item.setTitle_(f"Last updated: {self.last_updated.strftime('%H:%M:%S')}")

        # Store the formatted status for copying
        self.current_status_text = self._format_detailed_status()

    def _compute_percentage(self, used: str, limit: str) -> int | None:
        """Compute percentage from used and limit values."""
        try:
            used_val = int(used)
            limit_val = int(limit)
            if limit_val == 0:
                return None
            return int(used_val * 100 / limit_val)
        except (ValueError, TypeError):
            return None

    def _format_time_window(self, limit: LimitDetail) -> str:
        """Format the time window for a rate limit."""
        if limit.time_unit == "hour":
            return f"{limit.duration}h"
        elif limit.time_unit == "minute":
            return f"{limit.duration}m"
        elif limit.time_unit == "day":
            return f"{limit.duration}d"
        elif limit.time_unit == "second":
            return f"{limit.duration}s"
        elif limit.time_unit == "TOKENS_LIMIT":
            return "total"
        else:
            unit = limit.time_unit.replace("TIME_UNIT_", "").lower()
            return f"{limit.duration}{unit[0]}"

    def _format_status_line(self, usage: UsageInfo) -> str:
        """Format a single status line for the menubar."""
        if not usage.limits:
            return f"{usage.provider}: N/A"

        # Find the most relevant limit to display (prefer longer time windows)
        sorted_limits = sorted(
            usage.limits,
            key=lambda limit: (
                limit.duration * (24 if limit.time_unit == "day" else
                           168 if limit.time_unit == "week" else
                           720 if limit.time_unit == "month" else
                           1 if limit.time_unit == "hour" else
                           1/60 if limit.time_unit == "minute" else 1)
            ),
            reverse=True
        )

        limit = sorted_limits[0]
        percentage = self._compute_percentage(limit.used, limit.limit)

        if percentage is not None:
            return f"{usage.provider}: {percentage}%"
        return f"{usage.provider}: {limit.used}/{limit.limit}"

    def _format_detailed_status(self) -> str:
        """Format detailed status text for copying."""
        if not self.current_usage_data:
            return "No usage data available."

        lines = []
        for usage in self.current_usage_data:
            lines.append(f"\n{'='*50}")
            lines.append(f"Provider: {usage.provider}")
            if usage.user_id:
                lines.append(f"User ID: {usage.user_id}")
            if usage.membership_level:
                lines.append(f"Membership: {usage.membership_level}")

            if usage.limits:
                lines.append("\n  Rate Limits:")
                for limit in usage.limits:
                    time_window = self._format_time_window(limit)
                    percentage = self._compute_percentage(limit.used, limit.limit)
                    percentage_str = f" ({percentage}%)" if percentage is not None else ""
                    lines.append(f"    - {time_window}: {limit.used}/{limit.limit}{percentage_str} (remaining: {limit.remaining})")
                    if limit.reset_time:
                        reset_str = limit.reset_time.astimezone().strftime("%Y-%m-%d %H:%M %Z")
                        lines.append(f"      Reset: {reset_str}")
            else:
                lines.append("\n  No rate limits available.")

        lines.append(f"\n{'='*50}")
        if self.last_updated:
            lines.append(f"\nLast updated: {self.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(lines)

    def run(self) -> None:
        """Start the app."""
        print("DEBUG: Starting app run", file=sys.stderr)

        # Initial data fetch
        print("DEBUG: Starting initial refresh", file=sys.stderr)
        self.refresh_data()

        # Set up timer for auto-refresh (5 minutes = 300 seconds)
        print("DEBUG: Setting up timer", file=sys.stderr)
        self.timer = Foundation.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            300.0,  # 5 minutes
            self.delegate,
            "scheduledRefresh:",
            None,
            True,  # repeats
        )

        # Run the app - this will block until app terminates
        print("DEBUG: Calling app.run()", file=sys.stderr)
        self.app.run()
        print("DEBUG: app.run() returned", file=sys.stderr)


def run_menubar(config_path: str | None = None) -> None:
    """Entry point for the menubar app.

    Args:
        config_path: Path to config file. Defaults to ~/.coding_plan_usage_config.json
    """
    status_bar = UsageStatusBar(config_path)
    status_bar.run()
