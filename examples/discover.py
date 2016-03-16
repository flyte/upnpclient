#!/usr/bin/env python
#
# Demonstrate a simple UPnP device discovery.
#

import upnpclient

# De
ssdp = upnpclient.SSDP(wait_time=5)
servers = ssdp.discover()

for server in servers:
    print server.friendly_name, '@', server.location
    for service in server.services:
        print "   ", service.service_id, service.service_type
