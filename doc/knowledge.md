# Knowledge

Things we've learned about UPnP devices, this codebase, and common pitfalls.

## Project structure

- `upnpclient/` -- the package (upnp.py, ssdp.py, soap.py, marshal.py, errors.py, const.py, util.py)
- `tests/` -- pytest tests split by module (test_device, test_discovery, test_marshal, test_soap, test_errors)
- `tests/xml/` -- device XML fixtures organised by device type (igd, marantz, media_renderer, chromecast, roku)
- `tests/conftest.py` -- session-scoped HTTP server fixture and per-device fixtures
- `doc/` -- UPnP spec PDFs and this file
- `gui/` -- old PyQt5 GUI browser (not maintained, excluded from builds)
- `examples/` -- example scripts

## UPnP devices in the wild

- Many devices serve malformed XML -- leading spaces in URN namespaces (Marantz/DENON), missing SCPD files (Chromecast, Roku), invalid namespace prefixes.
- The XML parser uses `recover=True` to handle malformed device descriptions without crashing.
- Device service names vary -- `WANIPConn1`, `WANIPConnection`, `WANPPPConnection.1` etc. all refer to WAN connection services on different routers. There's no single canonical name.
- SSDP discovery returns duplicate responses -- the same device advertises multiple service types. `discover()` deduplicates by location URL.
- Some devices (e.g. crashed Sonos speakers) respond to SSDP but then time out on HTTP requests to fetch their description XML. This can cause `discover()` to take much longer than the SSDP timeout (#37).
- Chromecast devices respond to SSDP but return 404 for their SCPD URLs.
- The `service_id` format is `urn:<domain>:serviceId:<name>` -- the `name` part (after the last `:`) is what's used for attribute-style access on `Device` objects.

## Codebase conventions

- Python 3.9 is the minimum -- use `datetime.timezone.utc` not `datetime.UTC`.
- `lxml` is used for all XML parsing. The `XML_PARSER` global in `upnp.py` is configured with `recover=True`.
- Use `urllib.parse` directly, not `requests.compat`.
- No `six`, no Python 2 compat patterns.
- SOAP calls use raw `requests.post()`, not a session. SSL/self-signed cert support (#49) would need to change this to a `requests.Session`.
- The `gui/`, `doc/` and `examples/` directories are excluded from the published package (sdist and wheel).
- Service `name` property is derived from `service_id` by taking everything after the last `:`.

## Testing

- Tests use a real HTTP server (session-scoped pytest fixture) serving XML from `tests/xml/`.
- Device XML fixtures go in `tests/xml/<device_name>/`.
- Template files (`.xml.templ`) have `{port}` replaced with the actual server port at test startup.
- SOAP responses are mocked inline in tests -- not served from files.
- New device fixtures need a corresponding pytest fixture in `conftest.py`.
- The Marantz device XML intentionally contains malformed namespaces to test `recover=True`.
- Chromecast and Roku fixtures intentionally reference non-existent SCPD files to test error handling.

## Publishing

- PyPI publishing uses trusted publishing (OIDC) via GitHub Actions, triggered by pushing a version tag (e.g. `2.0.3`).
- Version is set in `pyproject.toml` only -- no `__version__` in the package.
- Always run `uv run --with tox-uv tox` before pushing to catch cross-version issues.
