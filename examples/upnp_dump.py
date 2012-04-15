#!/usr/bin/env python
#
# Dump all the methods on every UPnP server found.
#

import sys
import optparse
import logging

# Relative import of upnpclient
try:
    sys.path.insert(0, '../src/')
    import upnpclient
    sys.path.pop(0)
except ImportError, e:
    sys.stderr.write('Error importing upnpclient library: %s\n' % (e))
    sys.exit(-1)

# Parse options
parser = optparse.OptionParser()
parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False, help="Show debug information")
(options, args) = parser.parse_args()

# Enable debugging logging
if options.debug:
    logging.root.setLevel(logging.INFO)
    log = logging.basicConfig(level=logging.INFO,
        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')

# Discover services and dump
ssdp = upnpclient.SSDP()
servers = ssdp.discover()

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

