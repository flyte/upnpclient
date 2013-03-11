#!/usr/bin/env python
#
# Direct UPnP device connect without device discovery.
#

import upnpclient

server = upnpclient.Server('http://192.168.1.254:80/upnp/IGD.xml')
print server.friendly_name

for services in server:
    print service
