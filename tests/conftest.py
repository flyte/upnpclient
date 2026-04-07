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

    # Template .xml.templ files, replacing {port} with actual port
    generated = []
    for templ in xml_dir.rglob("*.xml.templ"):
        out = templ.with_suffix("")  # Remove .templ suffix -> .xml
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
    """IGD device with malformed namespace (from old test)."""
    return upnpclient.Device(f"http://127.0.0.1:{httpd}/igd/device_malformed_ns.xml")


@pytest.fixture
def marantz_device(httpd):
    """Marantz SR5008 with malformed namespace (issue #27)."""
    return upnpclient.Device(f"http://127.0.0.1:{httpd}/marantz/device.xml")


@pytest.fixture
def media_renderer_device(httpd):
    """Generic DLNA media renderer."""
    return upnpclient.Device(f"http://127.0.0.1:{httpd}/media_renderer/device.xml")
