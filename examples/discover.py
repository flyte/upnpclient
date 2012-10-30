#!/usr/bin/env python
#
# Demonstrate a simple UPnP device discovery.
#

import sys

# Relative import of upnpclient
try:
    sys.path.insert(0, '../src/')
    import upnpclient
    sys.path.pop(0)
except ImportError, e:
    sys.stderr.write('Error importing upnpclient library: %s\n' % (e))
    sys.exit(-1)

# De
ssdp = upnpclient.SSDP(wait_time=5)
servers = ssdp.discover()

for server in servers:
    print server.friendly_name
