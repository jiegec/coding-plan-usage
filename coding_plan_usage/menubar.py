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
from .formatter import _compute_percentage, format_usage_simple

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

        # Add action items at the top
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

        # Usage info section (will be populated dynamically)
        self.usage_section_start = self.menu.numberOfItems()

        self.menu.addItem_(AppKit.NSMenuItem.separatorItem())

        # Last updated time
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

        # Update usage menu items
        self._update_usage_menu_items()

        # Update last updated time
        if self.last_updated:
            self.last_updated_item.setTitle_(f"Last updated: {self.last_updated.strftime('%H:%M:%S')}")

        # Store the formatted status for copying
        self.current_status_text = self._format_detailed_status()

    def _update_usage_menu_items(self) -> None:
        """Update the usage info section in the menu."""
        # Remove old usage items (between usage_section_start and the separator before last_updated)
        # We need to find where to insert new items
        separator_index = self.usage_section_start

        # Remove items between section start and the "Last updated" separator
        while self.menu.numberOfItems() > separator_index + 1:
            item = self.menu.itemAtIndex_(separator_index)
            if item == self.last_updated_item or (item and item.isSeparatorItem()):
                break
            self.menu.removeItemAtIndex_(separator_index)

        # Insert new usage items
        insert_index = separator_index
        if not self.current_usage_data:
            item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "No usage data available", None, ""
            )
            item.setEnabled_(False)
            self.menu.insertItem_atIndex_(item, insert_index)
            return

        for index, usage in enumerate(self.current_usage_data):
            # Provider name as header (disabled, bold-like by using uppercase or emoji)
            header_text = f"{usage.provider.upper()}"
            if usage.membership_level:
                header_text += f" ({usage.membership_level})"
            item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                header_text, None, ""
            )
            item.setEnabled_(False)
            self.menu.insertItem_atIndex_(item, insert_index)
            insert_index += 1

            if usage.limits:
                for limit in usage.limits:
                    pct = _compute_percentage(limit.used, limit.limit)
                    pct_str = f"{pct}%" if pct is not None else f"{limit.used}/{limit.limit}"
                    time_window = self._format_time_window_short(limit)

                    # Main line: percentage/usage
                    line1 = f"- Usage: {pct_str} ({limit.used}/{limit.limit})"
                    item1 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                        line1, None, ""
                    )
                    item1.setEnabled_(False)
                    self.menu.insertItem_atIndex_(item1, insert_index)
                    insert_index += 1

                    # Second line: window and reset time
                    if limit.reset_time:
                        reset_time = limit.reset_time.astimezone()
                        now = datetime.now().astimezone()
                        # Show date if reset is not today
                        if reset_time.date() != now.date():
                            reset_str = reset_time.strftime("%m/%d %H:%M")
                        else:
                            reset_str = reset_time.strftime("%H:%M today")
                        line2 = f"  Time: {time_window} · resets {reset_str}"
                    else:
                        line2 = f"  Time: {time_window}"
                    item2 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                        line2, None, ""
                    )
                    item2.setEnabled_(False)
                    self.menu.insertItem_atIndex_(item2, insert_index)
                    insert_index += 1
            else:
                item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    "- No rate limits available", None, ""
                )
                item.setEnabled_(False)
                self.menu.insertItem_atIndex_(item, insert_index)
                insert_index += 1

            # Add small spacing between providers (but not after the last one)
            if index < len(self.current_usage_data) - 1:
                item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    "", None, ""
                )
                item.setEnabled_(False)
                self.menu.insertItem_atIndex_(item, insert_index)
                insert_index += 1

    def _format_time_window_short(self, limit: LimitDetail) -> str:
        """Format the time window as a short string."""
        if limit.time_unit == "hour":
            return f"{limit.duration}h"
        elif limit.time_unit == "minute":
            return f"{limit.duration}min"
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
        # Short provider names
        short_names = {
            "kimi": "K",
            "bigmodel": "B",
        }
        short_name = short_names.get(usage.provider, usage.provider[:1].upper())

        if not usage.limits:
            return f"{short_name}: N/A"

        # Show percentage for each limit
        percentages = []
        for limit in usage.limits:
            pct = _compute_percentage(limit.used, limit.limit)
            if pct is not None:
                percentages.append(f"{pct}%")
            else:
                percentages.append(f"{limit.used}/{limit.limit}")

        return f"{short_name}: {'/'.join(percentage for percentage in percentages)}"

    def _format_detailed_status(self) -> str:
        """Format detailed status text for copying."""
        if not self.current_usage_data:
            return "No usage data available."

        result = format_usage_simple(self.current_usage_data)
        if self.last_updated:
            result += f"\n\nLast updated: {self.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
        return result

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
