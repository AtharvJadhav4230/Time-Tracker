# Changelog

All notable changes to this project are documented here. The project follows
[Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-10-04

### Added

- local CSV/JSON activity exports and safe SQLite backups while tracking;
- Previous 7 days analysis, saved sampling/idle preferences and keyboard tab traversal;
- portable Windows ZIP alongside the installer, with separate SHA-256 entries;
- native Tk validation with fictional activity and real Windows package checks.

### Fixed

- failed analysis clears stale cards, rankings and chart, then recovers;
- recent activity retains selection, item focus and scrolling during refresh;
- reports-folder creation failures show a handled error;
- synthetic database generation reports expected filesystem/SQLite failures cleanly;
- release builds work from other directories and restore the caller's location;
- portable staging follows application signing and executable version metadata matches source;
- Reset clears the analysis failure state.

### Contributors

- Thanks to @Ymax27 for eight further desktop and release contributions.
- Thanks to @Juhita2005 for the portable build.
- Thanks to @Fire162 for concise synthetic-data generator errors.

## [1.2.0] - 2026-10-03

### Added

- offline category-rule preview command for fictional application/title inputs;
- reproducible synthetic activity database and dated-report instructions;
- `--version` for the terminal tracker;
- first-run and architecture guides and a fork-first contributor setup;
- expanded tracking, category, database, interval, reporting, analytics, CLI
  and Windows-provider regression coverage;
- Windows Python 3.11/3.13 and Ubuntu Python 3.12 CI jobs.

### Changed

- rankings use deterministic duration/name/color tie-breakers, including
  distinct case-equivalent application names and browser titles;
- contributor documentation uses the virtual environment executable directly.

### Fixed

- SQLite failures in the report command exit cleanly without a traceback;
- failed database initialization closes its connection.

### Contributors

- Thanks to @Ymax27 for 19 merged contributions.

## [1.1.0] - 2026-07-20

### Changed

- translated the entire desktop interface, reports, installer, command-line
  tools, categories, build messages, and documentation into English;
- renamed the source launcher to `Launch Time Tracker.cmd`;
- made GitHub release publication idempotent by replacing assets when a release
  already exists for the tag.

## [1.0.0] - 2026-07-20

### Added

- local foreground-window activity tracking for Windows;
- configurable keyboard and mouse idle detection;
- desktop interface with live activity;
- analysis for today and the last seven days;
- rankings by category, application, and browser tab;
- local SQLite storage and standalone HTML reports;
- Start, Stop, Reset, reports-folder, and data-management controls;
- PyInstaller executable and distributable Inno Setup installer;
- automated tests and tag-triggered GitHub release workflow;
- MIT License, privacy policy, legal notice, and signing guidance.
