# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Changed
- Restructured tests from unittest to pytest with per-module test files
- Added device XML fixtures for IGD, Marantz, generic MediaRenderer, Chromecast, and Roku
- Rewrote README for clarity -- explains service name derivation, shows `d.services` before accessing by name
- Added `doc/knowledge.md` and `CLAUDE.md`

## [2.0.3] - 2026-04-07

### Fixed
- `datetime.UTC` replaced with `datetime.timezone.utc` for Python 3.9/3.10 compatibility

### Changed
- Replaced `requests.compat` imports with `urllib.parse`
- Replaced `requests.compat.basestring` with `str` in tests
- Removed Python 2 `try/except ImportError` compat blocks from tests
- Modernised test HTTP server to use `directory` parameter instead of `os.chdir`
- Excluded `doc/`, `gui/`, `examples/` from sdist
- Removed unused Makefile
- Added PyPI, Python version, license and download badges to README

## [2.0.2] - 2026-04-07

### Fixed
- Non-compliant devices with malformed XML namespaces (e.g. Marantz/DENON with leading spaces in URNs) no longer crash the parser. XML parsing now uses `recover=True` mode.

## [2.0.1] - 2026-04-07

### Fixed
- `discover()` no longer prints errors to stderr for non-compliant devices. Discovery errors are now logged at `debug` level instead of `error`.

## [2.0.0] - 2026-04-07

### Changed
- **Breaking:** Minimum Python version raised from 3.6 to 3.9
- Converted from poetry to PEP 621 + hatchling + uv
- Replaced Travis CI with GitHub Actions (CI + PyPI publish via trusted publishing)
- Replaced flake8 with ruff
- Replaced `mock` with `unittest.mock` in tests

### Removed
- `six` dependency and all Python 2 compatibility code
- `poetry.lock`, `requirements.txt`, `setup.cfg`, `MANIFEST.in`

### Fixed
- `lxml` constraint widened from `^4.0.0` (`<5.0.0`) to `>=4.6.0`, fixing installation on Python 3.13+

## [1.0.3] - 2020-12-04

### Fixed
- Fix error when device attributes return None (stripping from None)

## [1.0.2] - 2020-09-27

### Changed
- Use tox-travis for CI

## [1.0.1] - 2020-09-27

### Changed
- Minor release updates

## [1.0.0] - 2020-06-04

### Changed
- Migrated from setuptools to poetry
- Dropped Python 2 support

## [0.0.8] - 2020-06-04

### Added
- ifaddr dependency for network interface discovery

## [0.0.7] and earlier

See [git history](https://github.com/flyte/upnpclient/commits/develop) for changes prior to 0.0.8.
