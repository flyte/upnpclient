#!/usr/bin/env python
#
# Dump all the methods on every UPnP server found.
#

import upnpclient

# Create an SSDP (Simple Service Discovery Protocol) client. This is the first
# step in discovering UPnP devices on the network.
ssdp = upnpclient.SSDP(wait_time=5)

# Do a device discovery on the network by broadcasting an HTTPU M-SEARCH using
# UDP over the network. We wait for devices to reply for 5 seconds.
servers = ssdp.discover()

# The discovery phase has provided us with a list of upnpclient.Server class
# instances. We'll walk through them, print some information on them and list
# their services, actions and the arguments for those actions.
if not servers:
    print "No UPnP servers discovered on your network. Maybe try turning on"
    print "UPnP on one of your devices?"
else:
    for server in servers:
        print "%s: %s (%s)" % (server.friendly_name, server.model_description, server.location)
        for service in server.services:
            print "   %s" % (service.service_type)
            for action in service.actions:
                print "      %s" % (action.name)
                for arg_name, arg_def in action.argsdef_in:
                    valid = ', '.join(arg_def['allowed_values']) or '*'
                    print "          in: %s (%s): %s" % (arg_name, arg_def['datatype'], valid)
                for arg_name, arg_def in action.argsdef_out:
                    valid = ', '.join(arg_def['allowed_values']) or '*'
                    print "         out: %s (%s): %s" % (arg_name, arg_def['datatype'], valid)

