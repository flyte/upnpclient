# Test Restructure & Device XML Fixtures

## Goals

Restructure tests from unittest to pytest style, add real-world device XML fixtures for broader test coverage.

## Test file structure

Split `tests/test_upnpclient.py` into modules matching source files:

- `tests/conftest.py` -- session-scoped HTTP server fixture, per-device fixtures
- `tests/test_device.py` -- Device parsing, properties, malformed XML, HTTP errors
- `tests/test_discovery.py` -- discover(), scan(), SSDP
- `tests/test_marshal.py` -- type marshalling (date, bool, uri, uuid, etc.)
- `tests/test_soap.py` -- SOAP calls, error handling
- `tests/test_errors.py` -- error code descriptions

## Fixture directory layout

```
tests/xml/
  igd/                        # Existing IGD router (renamed from upnp/)
    device.xml.templ
    device_malformed_ns.xml.templ
    Layer3Forwarding.xml
    LANHostConfigManagement.xml
    WANCommonInterfaceConfig.xml
  chromecast/                 # 404-prone device
    device.xml
  marantz/                    # Malformed namespace (issue #27)
    device.xml
    RenderingControl.xml
    ConnectionManager.xml
    AVTransport.xml
  media_renderer/             # Clean DLNA MediaRenderer
    device.xml
    RenderingControl.xml
    ConnectionManager.xml
    AVTransport.xml
  roku/                       # Missing SCPD URLs
    device.xml
```

Each device directory is self-contained with `device.xml` (or `.xml.templ` if port injection needed) and SCPD service files.

## conftest.py design

- Session-scoped `httpd` fixture starts HTTP server, templates `.xml.templ` files with port, yields port, cleans up generated files on teardown.
- Per-device fixtures (`igd_device`, `marantz_device`, etc.) create `upnpclient.Device` instances.
- SOAP response XML stays inline in individual tests -- clearer to see expected XML next to assertions.

## XML sourcing

- **Marantz SR5008**: device XML from issue #27, SCPD stubs matching service types.
- **Chromecast**: based on typical Chromecast descriptions, tests graceful HTTP error handling.
- **Generic media renderer**: manually authored clean DLNA MediaRenderer with AVTransport, RenderingControl, ConnectionManager.
- **Roku**: device XML referencing non-existent SCPD path, tests graceful failure.
- **Compatible-license repos**: reference miniupnpd (BSD), async-upnp-client (Apache 2.0) for additional device XMLs if needed.

## What stays the same

- Test coverage targets (80%+)
- The actual assertions -- same things tested, just pytest style
- Inline SOAP response XML in mock tests
- 4-5 device types to start
