# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-13

### Added

- Initial release with CLI and macOS menubar app.
- Support for Kimi API (`api.kimi.com/coding/v1/usages`).
- Support for 智谱 BigModel API (`open.bigmodel.cn/api/monitor/usage/quota/limit`).
- Configuration via JSON file (default: `~/.coding_plan_usage_config.json`).
- Auto-refresh every 5 minutes in menubar mode.
- Display usage percentages for each configured provider.
- Copy status to clipboard feature in menubar.
- Show last updated time in menubar.
- Add `CHANGELOG.md` following Keep a Changelog format.

[Unreleased]: https://github.com/jiegec/coding-plan-usage/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jiegec/coding-plan-usage/releases/tag/v0.1.0
