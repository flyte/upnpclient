# CLAUDE.md

## Project

upnpclient -- a UPnP client library for Python 3.9+. Discovers and controls UPnP devices on the network.

## Build & Test

```bash
uv run pytest                    # Run tests
uv run --with tox-uv tox        # Run tests on Python 3.9-3.13 + lint + coverage
uv run ruff check upnpclient    # Lint
uv build                        # Build sdist + wheel
```

Always run tox before pushing to catch cross-version issues.

## Project structure

- `upnpclient/` -- the package (upnp.py, ssdp.py, soap.py, marshal.py, errors.py, const.py, util.py)
- `tests/` -- pytest tests split by module (test_device, test_discovery, test_marshal, test_soap, test_errors)
- `tests/xml/` -- device XML fixtures organised by device type (igd, marantz, media_renderer, chromecast, roku)
- `tests/conftest.py` -- session-scoped HTTP server fixture and per-device fixtures
- `doc/` -- UPnP spec PDFs and knowledge.md
- `gui/` -- old PyQt5 GUI browser (not maintained, excluded from builds)
- `examples/` -- example scripts

## Key conventions

- Python 3.9 is the minimum -- use `datetime.timezone.utc` not `datetime.UTC`
- XML parsing uses `lxml` with `recover=True` (defined as `XML_PARSER` in upnp.py)
- No `six`, no Python 2 compat patterns
- Use `urllib.parse` directly, not `requests.compat`
- Publish by pushing a version tag (e.g. `2.0.3`) -- GitHub Actions handles PyPI via trusted publishing

## Testing patterns

- Device XML fixtures go in `tests/xml/<device_name>/`
- Templates use `.xml.templ` extension with `{port}` placeholder
- SOAP responses are mocked inline, not from fixture files
- New device fixtures need a corresponding pytest fixture in `conftest.py`
