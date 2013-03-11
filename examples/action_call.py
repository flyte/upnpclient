#!/usr/bin/env python
#
# Show how to actually perform UPnP calls.
#

import upnpclient

# Get a upnpclient.Server class instance for the UPnP service at our local
# router.
server = upnpclient.Server('http://192.168.1.1:37215/upnpdev.xml')

# Find the 'GetGenericPortMappingEntry' action on the server, regardless of the
# (virtual) device/service/etc it's on. You can use the find_action call on
# most levels of the upnpclient stack.In essence you can use find_action on all
# instances.

action = server.find_action('GetGenericPortMappingEntry')
response = action.call(NewPortMappingIndex=0)
print response
# Output: {u'NewPortMappingDescription': u'Transmission at 6881',
#          u'NewLeaseDuration': 0, u'NewInternalClient': u'192.168.1.10',
#          u'NewEnabled': True, u'NewExternalPort': 6881, u'NewRemoteHost': '',
#          u'NewProtocol': u'UDP', u'NewInternalPort': 6881}

# It's also possible to pass in a dictionary with the required parameters
action = server.find_action('GetGenericPortMappingEntry')
response = action.call({'NewPortMappingIndex': 0})
print response

# If we don't pass a required parameter, a UPNPError will be thrown
try:
    response = action.call()
except upnpclient.UPNPError, e:
    print str(e)
