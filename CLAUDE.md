# CLAUDE.md

## Build & Test

```bash
uv run pytest                    # Run tests
uv run --with tox-uv tox        # Run tests on Python 3.9-3.13 + lint + coverage
uv run ruff check upnpclient    # Lint
uv build                        # Build sdist + wheel
```

Always run tox before pushing to catch cross-version issues.

## Changelog

When making changes, add an entry to the `[Unreleased]` section of [CHANGELOG.md](CHANGELOG.md) under the appropriate heading (Added, Changed, Fixed, Removed). Entries are moved to a versioned section when a release is tagged.

## Knowledge

See [doc/knowledge.md](doc/knowledge.md) for codebase conventions, UPnP device quirks, testing patterns, and publishing workflow.
