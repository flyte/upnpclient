from netdisco.ssdp import scan

from .upnp import Device
from .util import _getLogger


def discover(timeout=5):
    """
    Convenience method to discover UPnP devices on the network. Returns a
    list of `upnp.Device` instances. Any invalid servers are silently
    ignored.
    """
    devices = {}
    for entry in scan(timeout):
        if entry.location in devices:
            continue
        try:
            devices[entry.location] = Device(entry.location)
        except Exception as exc:
            log = _getLogger("ssdp")
            log.error('Error \'%s\' for %s', exc, entry.location)
    return list(devices.values())
