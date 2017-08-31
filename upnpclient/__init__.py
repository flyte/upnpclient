# Copyright (c) 2012-2016, Ferry Boender <ferry.boender@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Todo:
#  - Allow persistance of discovered servers.
#  - The control point should wait at least the amount of time specified in the
#    MX header for responses to arrive from devices.
#  - Date/datetime
#  - Store all properties
#  - SSDP.discover(st): Allow to discover only certain service types
#  - .find() method on most classes.
#  - async discover (if possible).
#  - Read parameter types and verify them when doing a call.
#  - Marshall return values to the correct databases.
#  - Handle SOAP error:
#    <?xml version="1.0"?>
#    <s:Envelope
#      xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
#      s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
#     <s:Body>
#      <s:Fault>
#       <faultcode>s:Client</faultcode>
#       <faultstring>UPnPError</faultstring>
#       <detail>
#        <UPnPError xmlns="urn:schemas-upnp-org:control-1-0">
#          <errorCode xmlns="">714</errorCode>
#          <errorDescription xmlns="">No such entry in array</errorDescription>
#        </UPnPError>
#       </detail>
#      </s:Fault>
#     </s:Body>
#    </s:Envelope>
#  - Test params and responses with XML entities in them "<", "&", etc.
#  - AllowedValueRange
#    <allowedValueRange>
#      <minimum>minimum value</minimum>
#      <maximum>maximum value</maximum>
#      <step>increment value</step>
#    </allowedValueRange>
#  - Name params as 'NewFoo', or not (See spec)?

"""
This module provides an UPnP Control Point (client), and provides an easy
interface to discover and communicate with UPnP servers. It implements SSDP
(Simple Service Discovery Protocol), SCPD (Simple Control Point Definition) and
a minimal SOAP (Simple Object Access Protocol) implementation.

The usual flow for working with UPnP servers is:

- Discover UPnP servers using SSDP.

  SSDP is a simple HTTP-over-UDP protocol. An M-SEARCH HTTP request is broad-
  casted over the network and any UPnP servers should respond with an HTTP
  response. This response includes an URL to an XML file containing information
  about the server. The SSDP.discover() method returns a list of Server
  instances. If you already know the URL of the XML file, you can skip this
  step and instantiate a Server instance directly.

- Inspect Server capabilities using SCPD.

  The XML file returned by UPnP servers during discovery is read and information
  about the server and the services it offers is stored in a Server instance. The
  Server.services property contains a list of Service instances supported by that
  server.

- Inspect Services capabilities using SCPD.

  Each Server may contain more than one Services. For each Service, a separate
  XML file exists. The Service class reads that XML file and determines which
  actions a service supports. The Service.actions property contains a list of
  Action instances supported by that service.

- Inspect an Action using SCPD.

  An Action instance may be inspected to determine which arguments need to be
  passed into it and what it returns. Information on the type and possible
  values of each argument can also be queried.

- Call an Action using SOAP.

  An Action instance may then be called using the Action.call(arguments) method.
  The Action class will verify the correctness of arguments, possibly
  converting them. A SOAP call is then made to the UPnP server and the results
  are returned.

Classes:

* SSDP: Discover UPnP servers using the SSDP class.
* Server: Connect to an UPnP server and retrieve information/capabilities using the Server class.
* Service: Query a Server class instance for the various services it supports.
* Action: Query a Service class instance for the various actions it supports and call them.

Various convenience methods are provided at almost all levels. For instance,
the find_action() methods can directly find a method (by name) in an UPnP
server/service. The call() method can be used at most levels to directly call
an action.

The following example discovers all UPnP servers on the local network and then
dumps all their services and actions:

------------------------------------------------------------------------------
import upnpclient

ssdp = upnpclient.SSDP()
servers = ssdp.discover()

for server in servers:
    print "%s: %s" % (server.friendly_name, server.model_description)
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
------------------------------------------------------------------------------

Useful Links:

* https://embeddedinn.wordpress.com/tutorials/upnp-device-architecture/
* http://upnp.org/specs/arch/UPnP-arch-DeviceArchitecture-v1.1.pdf
"""
from upnpclient import const, errors, marshal, soap, ssdp, upnp, util  # noqa: F401
from .upnp import (
    Device, Action, Service, UPNPError, InvalidActionException, ValidationError, UnexpectedResponse)
from .ssdp import discover

__all__ = [
    "Device", "Action", "Service", "UPNPError", "InvalidActionException", "ValidationError",
    "discover", "UnexpectedResponse"
]
