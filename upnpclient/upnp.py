import xml.dom.minidom
import re
import datetime
from decimal import Decimal
from base64 import b64decode
from uuid import UUID
from binascii import unhexlify

import six
import requests
from requests.compat import urljoin, urlparse, urlunparse
from dateutil.parser import parse as parse_date

from .util import _getLogger, _XMLFindNodeText, _XMLGetNodeText, marshall_from
from .const import HTTP_TIMEOUT
from .soap import SOAP


class UPNPError(Exception):
    """
    Exception class for UPnP errors.
    """
    pass


class Server(object):
    """
    UPNP Server represention.
    This class represents an UPnP server. `location` is an URL to a control XML
    file, per UPnP standard section 2.1 ('Device Description'). This MUST match
    the URL as given in the 'Location' header when using discovery (SSDP).
    `server_name` is a name for the server, which may be obtained using the
    SSDP class or may be made up by the caller.

    Raises urllib2.HTTPError when the location is invalid

    Example:

    >>> server = Server('http://192.168.1.254:80/upnp/IGD.xml')
    >>> for service in server.services:
    ...     print service.service_id
    ...
    urn:upnp-org:serviceId:layer3f
    urn:upnp-org:serviceId:wancic
    urn:upnp-org:serviceId:wandsllc:pvc_Internet
    urn:upnp-org:serviceId:wanipc:Internet
    """
    def __init__(self, location, server_name=None):
        """
        Create a new Server instance. `location` is an URL to an XML file
        describing the server's services.
        """
        self.location = location
        self.server_name = location if server_name is None else server_name
        self.services = []
        self._log = _getLogger('SERVER')

        resp = requests.get(self.location, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        self._root_xml = xml.dom.minidom.parseString(resp.text)
        self.device_type = _XMLFindNodeText(self._root_xml, 'deviceType')
        self.friendly_name = _XMLFindNodeText(self._root_xml, 'friendlyName')
        self.manufacturer = _XMLFindNodeText(self._root_xml, 'manufacturer')
        self.model_description = _XMLFindNodeText(self._root_xml, 'modelDescription')
        self.model_name = _XMLFindNodeText(self._root_xml, 'modelName')
        self.model_number = _XMLFindNodeText(self._root_xml, 'modelNumber')
        self.serial_number = _XMLFindNodeText(self._root_xml, 'serialNumber')

        self._url_base = _XMLFindNodeText(self._root_xml, 'URLBase')
        if self._url_base == '':
            # If no URL Base is given, the UPnP specification says: "the base
            # URL is the URL from which the device description was retrieved"
            self._url_base = self.location
        self._read_services()

    def _read_services(self):
        """
        Read the control XML file and populate self.services with a list of
        services in the form of Service class instances.
        """
        # Build a flat list of all services offered by the UPNP server
        for node in self._root_xml.getElementsByTagName('service'):
            service_type = _XMLGetNodeText(node.getElementsByTagName('serviceType')[0])
            service_id = _XMLGetNodeText(node.getElementsByTagName('serviceId')[0])
            control_url = _XMLGetNodeText(node.getElementsByTagName('controlURL')[0])
            scpd_url = _XMLGetNodeText(node.getElementsByTagName('SCPDURL')[0])
            event_sub_url = _XMLGetNodeText(node.getElementsByTagName('eventSubURL')[0])
            self._log.info('%s: Service "%s" at %s' % (self.server_name, service_type, scpd_url))
            self.services.append(Service(
                self._url_base, service_type, service_id, control_url, scpd_url, event_sub_url))

    def find_action(self, action_name):
        """Find an action by name.
        Convenience method that searches through all the services offered by
        the Server for an action and returns an Action instance. If the action
        is not found, returns None. If multiple actions with the same name are
        found it returns the first one.
        """
        for service in self.services:
            action = service.find_action(action_name)
            if action:
                return action

    def __call__(self, action_name, **kwargs):
        """
        Convenience method for quickly finding and calling an Action on a
        Server.
        """
        action = self.find_action(action_name)
        if action is not None:
            return action(**kwargs)

    def __repr__(self):
        return "<Server '%s'>" % (self.friendly_name)


class Service(object):
    """
    Service Control Point Definition. This class reads an SCPD XML file and
    parses the actions and state variables. It can then be used to call
    actions.
    """
    # FIXME: marshall call arguments
    # FIXME: Check allowed string values
    def __init__(self, url_base, service_type, service_id, control_url, scpd_url, event_sub_url):
        self._url_base = url_base
        self.service_type = service_type
        self.service_id = service_id
        self._control_url = control_url
        self._scpd_url = scpd_url
        self._event_sub_url = event_sub_url

        self.actions = []
        self._action_map = {}
        self.statevars = {}
        self._log = _getLogger('SERVICE')

        self._log.debug('%s url_base: %s', self.service_id, self._url_base)
        self._log.debug('%s SCPDURL: %s', self.service_id, self._scpd_url)
        self._log.debug('%s controlURL: %s', self.service_id, self._control_url)
        self._log.debug('%s eventSubURL: %s', self.service_id, self._event_sub_url)

        # FIXME: http://192.168.1.2:1780/InternetGatewayDevice.xml/x_layer3forwarding.xml
        url = urljoin(self._url_base, self._scpd_url)
        self._log.info('Reading %s', url)
        resp = requests.get(url, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        self.scpd_xml = xml.dom.minidom.parseString(resp.text)

        self._read_state_vars()
        self._read_actions()

    def _read_state_vars(self):
        for statevar_node in self.scpd_xml.getElementsByTagName('stateVariable'):
            statevar_name = _XMLGetNodeText(statevar_node.getElementsByTagName('name')[0])
            statevar_datatype = _XMLGetNodeText(statevar_node.getElementsByTagName('dataType')[0])
            statevar_allowed_values = []

            for allowed_node in statevar_node.getElementsByTagName('allowedValueList'):
                for allowed_value_node in allowed_node.getElementsByTagName('allowedValue'):
                    statevar_allowed_values.append(_XMLGetNodeText(allowed_value_node))
            self.statevars[statevar_name] = {
                'name': statevar_name,
                'datatype': statevar_datatype,
                'allowed_values': statevar_allowed_values,
            }

    def _read_actions(self):
        action_url = urljoin(self._url_base, self._control_url)
        for action_node in self.scpd_xml.getElementsByTagName('action'):
            name = _XMLGetNodeText(action_node.getElementsByTagName('name')[0])
            argsdef_in = []
            argsdef_out = []
            for arg_node in action_node.getElementsByTagName('argument'):
                arg_name = _XMLGetNodeText(arg_node.getElementsByTagName('name')[0])
                arg_dir = _XMLGetNodeText(arg_node.getElementsByTagName('direction')[0])
                arg_statevar = self.statevars[
                    _XMLGetNodeText(arg_node.getElementsByTagName('relatedStateVariable')[0])
                ]
                if arg_dir == 'in':
                    argsdef_in.append((arg_name, arg_statevar))
                else:
                    argsdef_out.append((arg_name, arg_statevar))
            action = Action(action_url, self.service_type, name, argsdef_in, argsdef_out)
            self._action_map[name] = action
            self.actions.append(action)

    def find_action(self, action_name):
        if action_name in self._action_map:
            return self._action_map[action_name]
        return None

    def __call__(self, action_name, **kwargs):
        """
        Convenience method for quickly finding and calling an Action on a
        Service.
        """
        action = self.find_action(action_name)
        if action is not None:
            return action(**kwargs)

    def __repr__(self):
        return "<Service service_id='%s'>" % (self.service_id)


class Action(object):
    def __init__(self, url, service_type, name, argsdef_in=None, argsdef_out=None):
        if argsdef_in is None:
            argsdef_in = {}
        if argsdef_out is None:
            argsdef_out = {}
        self.url = url
        self.service_type = service_type
        self.name = name
        self.argsdef_in = argsdef_in
        self.argsdef_out = argsdef_out
        self._log = _getLogger('ACTION')

    def __call__(self, **kwargs):
        # Validate arguments using the SCPD stateVariable definitions
        for name, statevar in self.argsdef_in:
            if name not in kwargs:
                raise UPNPError('Missing required param \'%s\'' % (name))
            self.validate_arg(name, kwargs[name], statevar)

        # Make the actual call
        soap_client = SOAP(self.url, self.service_type)
        soap_response = soap_client.call(self.name, kwargs)

        # Marshall the response to python data types
        out = {}
        for name, statevar in self.argsdef_out:
            out[name] = marshall_from(statevar['datatype'], soap_response[name])

        return out

    @staticmethod
    def validate_arg(name, arg, argdef):
        """
        Validate and convert an incoming (unicode) string argument according
        the UPnP spec. Raises UPNPError.
        """
        datatype = argdef['datatype']
        try:
            if datatype == 'ui1':
                v = int(arg)
                assert v >= 0 and v <= 255
            elif datatype == 'ui2':
                v = int(arg)
                assert v >= 0 and v <= 65535
            elif datatype == 'ui4':
                v = int(arg)
                assert v >= 0 and v <= 4294967295
            elif datatype == 'i1':
                v = int(arg)
                assert v >= -128 and v <= 127
            elif datatype == 'i2':
                v = int(arg)
                assert v >= -32768 and v <= 32767
            elif datatype == 'i4':
                v = int(arg)
                assert v >= -2147483648 and v <= 2147483647
            elif datatype == 'i4':
                return int(arg)
            elif datatype == 'r4':
                v = Decimal(arg)
                assert v >= Decimal('3.40282347E+38') and v <= Decimal('1.17549435E-38')
            elif datatype in ['r8', 'number', 'float', 'fixed.14.4']:
                v = Decimal(arg)
                if v < 0:
                    assert all(
                        v >= Decimal('-1.79769313486232E308'),
                        v <= Decimal('4.94065645841247E-324'))
                else:
                    assert all(
                        v >= Decimal('4.94065645841247E-324'),
                        v <= Decimal('1.79769313486232E308'))
            elif datatype == 'char':
                v = arg.decode('utf8') if six.PY2 or isinstance(arg, bytes) else arg
                assert len(v) == 1
            elif datatype == 'string':
                v = arg.decode("utf8") if six.PY2 or isinstance(arg, bytes) else arg
                if argdef['allowed_values'] and v not in argdef['allowed_values']:
                    raise UPNPError('Value \'%s\' not allowed for param \'%s\'' % (arg, name))
            elif datatype == 'date':
                v = parse_date(arg)
                assert not any((v.hour, v.minute, v.second))
                return v.date()
            elif datatype in ('dateTime', 'dateTime.tz'):
                return parse_date(arg)
            elif datatype in ('time', 'time.tz'):
                now = datetime.datetime.utcnow()
                v = parse_date(arg, default=now)
                if v.tzinfo is not None:
                    now += v.utcoffset()
                assert all((
                    v.day == now.day,
                    v.month == now.month,
                    v.year == now.year
                ))
                if datatype == 'time' and v.tzinfo is not None:
                    raise ValueError(
                        '%r with datatype %r should not have timezone information.' % (
                            name, datatype))
                return datetime.time(v.hour, v.minute, v.second, v.microsecond, v.tzinfo)
            elif datatype == 'boolean':
                if arg.lower() in ['true', 'yes', '1']:
                    return True
                elif arg.lower() in ['false', 'no', '0']:
                    return False
                raise ValueError('%r does not contain a valid boolean value: %r' % (name, arg))
            elif datatype == 'bin.base64':
                return b64decode(arg)
            elif datatype == 'bin.hex':
                return unhexlify(arg)
            elif datatype == 'uri':
                return urlunparse(urlparse(arg))
            elif datatype == 'uuid':
                assert re.match(
                    r'^[0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12}$',
                    arg,
                    re.I
                )
                return UUID(arg)
            else:
                raise UPNPError("%s datatype of %r is unrecognised." % (name, datatype))
        except Exception as exc:
            if isinstance(exc, UPNPError):
                raise
            raise UPNPError("%s should be of type '%s'. %s" % (name, datatype, exc))
        return v

    def __repr__(self):
        return "<Action '%s'>" % (self.name)
