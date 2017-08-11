from netdisco.ssdp import scan

from .upnp import Server
from .util import _getLogger


def discover(timeout=5):
    """
    Convenience method to discover UPnP devices on the network. Returns a
    list of `upnp.Server` instances. Any invalid servers are silently
    ignored.
    """
    servers = {}
    for entry in scan(timeout):
        if entry.location in servers:
            continue
        try:
            servers[entry.location] = Server(entry.location)
        except Exception as exc:
            log = _getLogger("ssdp")
            log.error('Error \'%s\' for %s', exc, entry.location)
    return list(servers.values())
