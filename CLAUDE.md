# CLAUDE.md

## Build & Test

```bash
uv run pytest                    # Run tests
uv run --with tox-uv tox        # Run tests on Python 3.9-3.13 + lint + coverage
uv run ruff check upnpclient    # Lint
uv build                        # Build sdist + wheel
```

Always run tox before pushing to catch cross-version issues.

## Knowledge

See [doc/knowledge.md](doc/knowledge.md) for codebase conventions, UPnP device quirks, testing patterns, and publishing workflow.
