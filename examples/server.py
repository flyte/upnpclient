#!/usr/bin/env python
#
# Direct UPnP device connect without device discovery.
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

server = upnpclient.Server('http://192.168.1.254:80/upnp/IGD.xml')
print server.friendly_name

for services in server:
    print service
