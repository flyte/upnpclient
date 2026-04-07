# Test Restructure & Device XML Fixtures Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert tests from unittest to pytest, add real-world device XML fixtures for broader coverage.

**Architecture:** Split monolithic test file into per-module test files. Extract HTTP server setup into pytest session fixture. Add device XML directories for IGD, Marantz, Chromecast, generic media renderer, and Roku. Each device directory is self-contained with device description + SCPD files.

**Tech Stack:** pytest, pytest-cov, lxml, requests, unittest.mock

---

### Task 1: Rename XML fixture directory and create new device directories

**Files:**
- Move: `tests/xml/upnp/` -> `tests/xml/igd/`
- Create: `tests/xml/marantz/`
- Create: `tests/xml/chromecast/`
- Create: `tests/xml/media_renderer/`
- Create: `tests/xml/roku/`

**Step 1: Rename upnp/ to igd/ and rename IGD files**

```bash
cd tests/xml
git mv upnp igd
cd igd
git mv IGD.xml.templ device.xml.templ
git mv IGD_malformed_ns.xml.templ device_malformed_ns.xml.templ
```

**Step 2: Create empty directories for new device types**

```bash
mkdir -p tests/xml/marantz tests/xml/chromecast tests/xml/media_renderer tests/xml/roku
```

**Step 3: Commit**

```bash
git add -A tests/xml/
git commit -m "Rename test XML fixture directory from upnp/ to igd/"
```

---

### Task 2: Create Marantz device XML fixtures

Based on issue #27 -- Marantz SR5008 with malformed `xmlns:ms=" urn:microsoft-com:wmc-1-0"`.

**Files:**
- Create: `tests/xml/marantz/device.xml`
- Create: `tests/xml/marantz/RenderingControl.xml`
- Create: `tests/xml/marantz/ConnectionManager.xml`
- Create: `tests/xml/marantz/AVTransport.xml`

**Step 1: Create device.xml**

Use the XML from issue #27 with the malformed namespace preserved. Include service references pointing to the SCPD files. Use `.xml.templ` if port injection needed, otherwise hardcode relative paths.

```xml
<?xml version="1.0"?>
<root xmlns="urn:schemas-upnp-org:device-1-0"
      xmlns:ms=" urn:microsoft-com:wmc-1-0">
  <!-- ... full Marantz device description from issue #27 ... -->
  <!-- serviceList with SCPDURL pointing to /marantz/*.xml -->
</root>
```

**Step 2: Create minimal SCPD stubs**

Each SCPD file needs a valid `<scpd>` root with at least one action and one state variable. Model them on the real Marantz services (RenderingControl, ConnectionManager, AVTransport).

**Step 3: Verify XML is well-formed (except the intentional namespace issue)**

```bash
uv run python -c "from lxml import etree; etree.parse('tests/xml/marantz/RenderingControl.xml')"
```

**Step 4: Commit**

```bash
git add tests/xml/marantz/
git commit -m "Add Marantz SR5008 device XML fixtures (malformed namespace)"
```

---

### Task 3: Create generic media renderer XML fixtures

A clean, compliant DLNA MediaRenderer device.

**Files:**
- Create: `tests/xml/media_renderer/device.xml.templ`
- Create: `tests/xml/media_renderer/RenderingControl.xml`
- Create: `tests/xml/media_renderer/ConnectionManager.xml`
- Create: `tests/xml/media_renderer/AVTransport.xml`

**Step 1: Create device.xml.templ**

Standard MediaRenderer with URLBase using `{port}` template variable. Three services: RenderingControl, ConnectionManager, AVTransport. SCPDURLs pointing to `/media_renderer/*.xml`.

**Step 2: Create SCPD files**

Each file should define realistic actions:
- **AVTransport**: Play, Stop, Pause, SetAVTransportURI, GetTransportInfo
- **RenderingControl**: GetVolume, SetVolume, GetMute, SetMute
- **ConnectionManager**: GetProtocolInfo, GetCurrentConnectionIDs

Include proper state variable definitions and argument lists so the full Action parsing chain works.

**Step 3: Validate all XML**

```bash
for f in tests/xml/media_renderer/*.xml; do
  uv run python -c "from lxml import etree; etree.parse('$f'); print('OK: $f')"
done
```

**Step 4: Commit**

```bash
git add tests/xml/media_renderer/
git commit -m "Add generic DLNA MediaRenderer XML fixtures"
```

---

### Task 4: Create Chromecast and Roku XML fixtures

**Files:**
- Create: `tests/xml/chromecast/device.xml.templ`
- Create: `tests/xml/roku/device.xml.templ`

**Step 1: Create Chromecast device.xml.templ**

Chromecast-style device that references a non-existent SCPD URL (`/ssdp/notfound`). This tests that device creation handles 404 SCPD responses gracefully. Use `{port}` template for URLBase.

**Step 2: Create Roku device.xml.templ**

Roku-style device referencing a non-existent SCPD path (`/dial/ecp_SCPD.xml`). Similar purpose to Chromecast but different device type and structure.

**Step 3: Commit**

```bash
git add tests/xml/chromecast/ tests/xml/roku/
git commit -m "Add Chromecast and Roku device XML fixtures"
```

---

### Task 5: Create conftest.py with HTTP server and device fixtures

**Files:**
- Create: `tests/conftest.py`

**Step 1: Write conftest.py**

```python
import http.server as httpserver
import os
import socketserver as sockserver
import threading
from pathlib import Path

import pytest

import upnpclient


@pytest.fixture(scope="session")
def httpd():
    """Start HTTP server serving test XML fixture files."""
    xml_dir = Path(__file__).parent / "xml"
    handler = lambda *args, **kwargs: httpserver.SimpleHTTPRequestHandler(
        *args, directory=str(xml_dir), **kwargs
    )
    server = sockserver.TCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    port = server.server_address[1]

    # Template .xml.templ files
    generated = []
    for templ in xml_dir.rglob("*.xml.templ"):
        out = templ.with_suffix("")  # Remove .templ
        out.write_text(templ.read_text().format(port=port))
        generated.append(out)

    yield port

    server.shutdown()
    for f in generated:
        f.unlink(missing_ok=True)


@pytest.fixture
def igd_device(httpd):
    """Standard IGD router device."""
    return upnpclient.Device(f"http://127.0.0.1:{httpd}/igd/device.xml")


@pytest.fixture
def igd_malformed_ns_device(httpd):
    """IGD device with malformed namespace."""
    return upnpclient.Device(
        f"http://127.0.0.1:{httpd}/igd/device_malformed_ns.xml"
    )


@pytest.fixture
def marantz_device(httpd):
    """Marantz SR5008 with malformed namespace."""
    return upnpclient.Device(f"http://127.0.0.1:{httpd}/marantz/device.xml")


@pytest.fixture
def media_renderer_device(httpd):
    """Generic DLNA media renderer."""
    return upnpclient.Device(
        f"http://127.0.0.1:{httpd}/media_renderer/device.xml"
    )
```

**Step 2: Verify fixtures work**

```bash
uv run pytest --co -q
```

Should list all test files and show no collection errors.

**Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "Add pytest conftest with HTTP server and device fixtures"
```

---

### Task 6: Create test_device.py

Convert `TestUPnPClientWithServer` device-related tests to pytest style.

**Files:**
- Create: `tests/test_device.py`

**Step 1: Write test_device.py**

Migrate these tests from the existing file:
- `test_device_props` -> `test_device_props(igd_device)`
- `test_device_malformed_namespace` -> `test_malformed_namespace(igd_malformed_ns_device)`
- `test_device_nonexists` -> `test_device_not_found(httpd)`
- `test_device_auth` -> `test_device_auth(httpd)`
- `test_device_auth_call_override` -> `test_device_auth_call_override(httpd)`
- `test_device_auth_call_override_none` -> `test_device_auth_call_override_none(httpd)`
- `test_device_auth_none_override` -> `test_device_auth_none_override(httpd)`
- `test_device_headers` -> `test_device_headers(httpd)`
- `test_device_headers_call_override` -> `test_device_headers_call_override(httpd)`
- `test_device_headers_call_override_none` -> `test_device_headers_call_override_none(httpd)`
- `test_device_headers_none_override` -> `test_device_headers_none_override(httpd)`
- `test_services` -> `test_services(igd_device)`
- `test_actions` -> `test_actions(igd_device)`
- `test_findaction_server` -> `test_find_action(igd_device)`
- `test_findaction_server_nonexists` -> `test_find_action_not_found(igd_device)`
- `test_findaction_service_nonexists` -> `test_find_action_service_not_found(igd_device)`
- `test_callaction_*` -> corresponding pytest functions using `igd_device` fixture
- `test_subscribe`, `test_renew_subscription`, `test_cancel_subscription` -> pytest functions
- `test_args_order`, `test_args_order_read_ok` -> pytest functions

Also add new tests for the new device fixtures:
- `test_marantz_device_props(marantz_device)` -- verify parsing works with malformed namespace
- `test_media_renderer_services(media_renderer_device)` -- verify AVTransport, RenderingControl, ConnectionManager
- `test_chromecast_scpd_404(httpd)` -- verify graceful failure when SCPD returns 404
- `test_roku_scpd_missing(httpd)` -- same for Roku

Pattern for converted tests -- replace:
```python
# Old unittest style
self.assertEqual(server.device_type, "urn:...")
self.assertRaises(SomeError, func, arg)
```

With:
```python
# New pytest style
assert device.device_type == "urn:..."
with pytest.raises(SomeError):
    func(arg)
```

Replace `@mock.patch` decorators with `mocker` fixture from `pytest-mock`, or keep using `unittest.mock.patch` as a context manager -- either works. Keep `unittest.mock` to avoid adding `pytest-mock` as a dependency.

**Step 2: Run tests**

```bash
uv run pytest tests/test_device.py -v
```

All tests should pass.

**Step 3: Commit**

```bash
git add tests/test_device.py
git commit -m "Add test_device.py with pytest-style device tests"
```

---

### Task 7: Create test_discovery.py

**Files:**
- Create: `tests/test_discovery.py`

**Step 1: Write test_discovery.py**

Migrate from `TestUPnPClient`:
- `test_discover` -> `test_discover()`
- `test_discover_exception` -> `test_discover_exception()`

These use mocks only, no server needed.

**Step 2: Run tests**

```bash
uv run pytest tests/test_discovery.py -v
```

**Step 3: Commit**

```bash
git add tests/test_discovery.py
git commit -m "Add test_discovery.py with pytest-style discovery tests"
```

---

### Task 8: Create test_marshal.py

**Files:**
- Create: `tests/test_marshal.py`

**Step 1: Write test_marshal.py**

Migrate from `TestUPnPClient`:
- All `test_marshal_*` and `test_validate_*` tests

These are pure unit tests -- no fixtures needed, just `upnpclient.Action.validate_arg` and `upnpclient.marshal.marshal_value` calls.

Consider using `@pytest.mark.parametrize` for `test_marshal_bool` which tests many input values.

**Step 2: Run tests**

```bash
uv run pytest tests/test_marshal.py -v
```

**Step 3: Commit**

```bash
git add tests/test_marshal.py
git commit -m "Add test_marshal.py with pytest-style marshal/validate tests"
```

---

### Task 9: Create test_soap.py

**Files:**
- Create: `tests/test_soap.py`

**Step 1: Write test_soap.py**

Migrate from `TestSOAP`:
- `test_call` -> `test_soap_call()`
- `test_call_with_auth` -> `test_soap_call_with_auth()`
- `test_non_xml_error` -> `test_non_xml_error()`
- `test_missing_error_code_element` -> `test_missing_error_code()`
- `test_missing_error_description_element` -> `test_missing_error_description()`
- `test_missing_response_element` -> `test_missing_response_element()`

All use mocks, no server needed. The `EndPrematurelyException` pattern can be replaced with `pytest.raises`.

**Step 2: Run tests**

```bash
uv run pytest tests/test_soap.py -v
```

**Step 3: Commit**

```bash
git add tests/test_soap.py
git commit -m "Add test_soap.py with pytest-style SOAP tests"
```

---

### Task 10: Create test_errors.py

**Files:**
- Create: `tests/test_errors.py`

**Step 1: Write test_errors.py**

Migrate from `TestErrors`:
- `test_existing_err` -> `test_existing_error_codes()`
- `test_non_integer` -> `test_non_integer_key()`
- `test_reserved` -> `test_reserved_range()`
- `test_common_action` -> `test_common_action_range()`
- `test_action_specific_committee` -> `test_committee_range()`
- `test_action_specific_vendor` -> `test_vendor_range()`

Pure unit tests, no fixtures needed.

**Step 2: Run tests**

```bash
uv run pytest tests/test_errors.py -v
```

**Step 3: Commit**

```bash
git add tests/test_errors.py
git commit -m "Add test_errors.py with pytest-style error code tests"
```

---

### Task 11: Delete old test file and verify full suite

**Files:**
- Delete: `tests/test_upnpclient.py`

**Step 1: Run full test suite to confirm everything passes**

```bash
uv run pytest -v
```

All 75+ tests should pass across the new test files.

**Step 2: Run coverage**

```bash
uv run pytest --cov upnpclient --cov-fail-under 80 --cov-report term-missing
```

Coverage should be >= 80%.

**Step 3: Run tox**

```bash
uv run --with tox-uv tox
```

All Python versions, lint, and coverage should pass.

**Step 4: Delete old test file**

```bash
git rm tests/test_upnpclient.py
```

**Step 5: Commit**

```bash
git add -A
git commit -m "Remove old unittest test file, pytest conversion complete"
```

---

### Task 12: Run ruff and fix any lint issues

**Step 1: Run ruff on test files**

```bash
uv run ruff check tests/
```

**Step 2: Fix any issues**

**Step 3: Final tox run**

```bash
uv run --with tox-uv tox
```

**Step 4: Commit**

```bash
git add -A
git commit -m "Fix lint issues in new test files"
```
