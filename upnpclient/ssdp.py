import socket

from .upnp import Server
from .util import _getLogger


class SSDP(object):
    """
    Simple Service Discovery Protocol. The SSDP class allows for discovery of
    UPnP devices by broadcasting on the local network. It does so by sending an
    HTTP M-SEARCH command over multicast UDP. The `discover()` method does the
    actual discovering. It returns a list of `upnp.Server` class instances of
    servers that responded. After discovery, these servers can also be accessed
    through the `servers` propery.

    Example:

    >>> ssdp = SSDP(1)
    >>> servers = ssdp.discover()
    >>> print upnpservers
    [<Server 'SpeedTouch 546 5.4.0.14 UPnP/1.0 (0612BH95K)'>, <Server 'Linux/2.6.35-31-generic, UPnP/1.0, Free UPnP Entertainment Service/0.655'>]
    """
    def __init__(self, wait_time=2, listen_port=12333):
        """
        Create a new SSDP class. `wait_time` determines how long to wait for
        responses from servers. `listen_port` determines the UDP port on which
        to send/receive replies.
        """
        self.listen_port = listen_port
        self.wait_time = wait_time
        self._log = _getLogger('SSDP')

    def discover_raw(self):
        """
        Discover UPnP devices on the network via UDP multicast. Returns a list
        of dictionaries, each of which contains the HTTPMU reply headers.

        # FIXME: Do this on all interfaces instead of letting the OS choose.
        """
        msg = '\r\n'.join([
            'M-SEARCH * HTTP/1.1',
            'HOST:239.255.255.250:1900',
            'MAN:"ssdp:discover"',
            'MX:2',
            'ST:upnp:rootdevice',
            ''
        ])

        # Send discovery broadcast message
        self._log.debug('M-SEARCH broadcast discovery')
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(self.wait_time)
        s.sendto(msg.encode('utf8'), ('239.255.255.250', 1900))

        # Wait for replies
        ssdp_replies = []
        servers = []
        try:
            while True:
                self._log.debug('Waiting for replies...')
                data, addr = s.recvfrom(65507)
                ssdp_reply_headers = {}
                for line in data.splitlines():
                    if ':' in line:
                        key, value = line.split(':', 1)
                        ssdp_reply_headers[key.strip().lower()] = value.strip()
                self._log.info('Response from %s:%i %s' % (addr[0], addr[1], ssdp_reply_headers['server']))
                self._log.info('%s:%i at %s' % (addr[0], addr[1], ssdp_reply_headers['location']))
                if ssdp_reply_headers not in ssdp_replies:
                    # Prevent multiple responses from showing up multiple
                    # times.
                    ssdp_replies.append(ssdp_reply_headers)
        except socket.timeout:
            pass

        s.close()
        return ssdp_replies

    def discover(self):
        """
        Convenience method to discover UPnP devices on the network. Returns a
        list of `upnp.Server` instances. Any invalid servers are silently
        ignored. If you do not want this, use the `SSDP.discover_raw` method.
        """
        servers = []
        for ssdp_reply in self.discover_raw():
            try:
                upnp_server = Server(ssdp_reply['location'], ssdp_reply['server'])
                servers.append(upnp_server)
            except Exception as e:
                self._log.error('Error \'%s\' for %s' % (e, ssdp_reply['server']))
        return servers
