# Knowledge

Things we've learned about UPnP devices, this codebase, and common pitfalls.

## UPnP devices in the wild

- Many devices serve malformed XML -- leading spaces in URN namespaces (Marantz/DENON), missing SCPD files (Chromecast, Roku), invalid namespace prefixes.
- The XML parser uses `recover=True` to handle malformed device descriptions without crashing.
- Device service names vary -- `WANIPConn1`, `WANIPConnection`, `WANPPPConnection.1` etc. all refer to WAN connection services on different routers. There's no single canonical name.
- SSDP discovery returns duplicate responses -- the same device advertises multiple service types. `discover()` deduplicates by location URL.
- Some devices (e.g. crashed Sonos speakers) respond to SSDP but then time out on HTTP requests to fetch their description XML. This can cause `discover()` to take much longer than the SSDP timeout (#37).
- Chromecast devices respond to SSDP but return 404 for their SCPD URLs.
- The `service_id` format is `urn:<domain>:serviceId:<name>` -- the `name` part (after the last `:`) is what's used for attribute-style access on `Device` objects.

## Codebase

- `lxml` is used for all XML parsing. The `XML_PARSER` global in `upnp.py` is configured with `recover=True`.
- SOAP calls use raw `requests.post()`, not a session. SSL/self-signed cert support (#49) would need to change this to a `requests.Session`.
- The `six` library and all Python 2 compat code was removed in v2.0.0.
- `datetime.timezone.utc` is used instead of `datetime.UTC` for Python 3.9/3.10 compatibility.
- The `gui/` and `doc/` directories are excluded from the published package (sdist and wheel).
- Service `name` property is derived from `service_id` by taking everything after the last `:`.

## Testing

- Tests use a real HTTP server (session-scoped pytest fixture) serving XML from `tests/xml/`.
- Template files (`.xml.templ`) have `{port}` replaced with the actual server port at test startup.
- SOAP responses are mocked inline in tests -- not served from files.
- The Marantz device XML intentionally contains malformed namespaces to test `recover=True`.
- Chromecast and Roku fixtures intentionally reference non-existent SCPD files to test error handling.

## Publishing

- PyPI publishing uses trusted publishing (OIDC) via GitHub Actions, triggered by pushing a version tag (e.g. `2.0.3`).
- Version is set in `pyproject.toml` only -- no `__version__` in the package.
- Always run `uv run --with tox-uv tox` before pushing to catch cross-version issues.
