import unittest
import threading
import os.path as path
import os
import datetime
import base64
import binascii
from uuid import UUID

import mock
import requests
from requests.compat import basestring
from lxml import etree

import upnpclient as upnp


try:
    import http.server as httpserver
except ImportError:
    import SimpleHTTPServer as httpserver

try:
    import socketserver as sockserver
except ImportError:
    import SocketServer as sockserver

try:
    from urllib.parse import ParseResult
except ImportError:
    from urlparse import ParseResult


class EndPrematurelyException(Exception):
    pass


class TestUPnPClientWithServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Set up an HTTP server to serve the XML files. Set the correct port in
        the IGD.xml URLBase element.
        """
        # Have to chdir here because the py2 SimpleHTTPServer doesn't allow us
        # to change its working directory like the py3 one does.
        os.chdir(path.join(path.dirname(path.realpath(__file__)), 'xml'))
        cls.httpd = sockserver.TCPServer(('127.0.0.1', 0), httpserver.SimpleHTTPRequestHandler)
        cls.httpd_thread = threading.Thread(target=cls.httpd.serve_forever)
        cls.httpd_thread.daemon = True
        cls.httpd_thread.start()
        cls.httpd_port = cls.httpd.server_address[1]

        with open('upnp/IGD.xml', 'w') as out_f:
            with open('upnp/IGD.xml.templ') as in_f:
                out_f.write(in_f.read().format(port=cls.httpd_port))

    @classmethod
    def tearDownClass(cls):
        """
        Shut down the HTTP server and delete the IGD.xml file.
        """
        cls.httpd.shutdown()
        try:
            os.unlink('upnp/IGD.xml')
        except OSError:
            pass

    def setUp(self):
        self.server = upnp.Device('http://127.0.0.1:%s/upnp/IGD.xml' % self.httpd_port)

    def test_device_props(self):
        """
        `Device` instance should contain the properties from the XML.
        """
        server = upnp.Device('http://127.0.0.1:%s/upnp/IGD.xml' % self.httpd_port)
        self.assertEqual(server.device_type, 'urn:schemas-upnp-org:device:InternetGatewayDevice:1')
        self.assertEqual(server.friendly_name, 'SpeedTouch 5x6 (0320FJ2PZ)')
        self.assertEqual(server.manufacturer, 'Pannaway')
        self.assertEqual(server.model_description, 'DSL Internet Gateway Device')
        self.assertEqual(server.model_name, 'Pannaway')
        self.assertEqual(server.model_number, 'RG-210')
        self.assertEqual(server.serial_number, '0320FJ2PZ')

    def test_device_nonexists(self):
        """
        Should return `HTTPError` if the XML is not found on the server.
        """
        self.assertRaises(
            requests.exceptions.HTTPError,
            upnp.Device,
            'http://127.0.0.1:%s/upnp/DOESNOTEXIST.xml' % self.httpd_port
        )

    def test_services(self):
        """
        All of the services from the XML should be present in the server services.
        """
        service_ids = [service.service_id for service in self.server.services]
        self.assertIn('urn:upnp-org:serviceId:layer3f', service_ids)
        self.assertIn('urn:upnp-org:serviceId:lanhcm', service_ids)
        self.assertIn('urn:upnp-org:serviceId:wancic', service_ids)

    def test_actions(self):
        """
        Action names should be present in the list of server actions.
        """
        action_names = set()
        for service in self.server.services:
            for action in service.actions:
                action_names.add(action.name)

        self.assertIn('SetDefaultConnectionService', action_names)
        self.assertIn('GetCommonLinkProperties', action_names)
        self.assertIn('GetDNSServers', action_names)
        self.assertIn('GetDHCPRelay', action_names)

    def test_findaction_server(self):
        """
        Should find and return the correct action.
        """
        action = self.server.find_action('GetSubnetMask')
        self.assertIsInstance(action, upnp.Action)
        self.assertEqual(action.name, 'GetSubnetMask')

    def test_findaction_server_nonexists(self):
        """
        Should return None if no action is found with the given name.
        """
        action = self.server.find_action('GetNoneExistingAction')
        self.assertEqual(action, None)

    def test_findaction_service_nonexists(self):
        """
        Should return None if no action is found with the given name.
        """
        service = self.server.services[0]
        action = self.server.find_action('GetNoneExistingAction')
        self.assertEqual(action, None)

    @mock.patch('requests.post')
    def test_callaction_server(self, mock_post):
        """
        Should be able to call the server with the name of an action.
        """
        ret = mock.Mock()
        ret.content = """
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
           <s:Body>
              <u:GetSubnetMaskResponse xmlns:u="urn:schemas-upnp-org:service:LANHostConfigManagement:1">
                 <NewSubnetMask>255.255.255.0</NewSubnetMask>
              </u:GetSubnetMaskResponse>
           </s:Body>
        </s:Envelope>
        """
        mock_post.return_value = ret
        ret = self.server('GetSubnetMask')
        self.assertEqual(ret, dict(NewSubnetMask='255.255.255.0'))

    @mock.patch('requests.post')
    def test_callaction_noparam(self, mock_post):
        """
        Should be able to call an action with no params and get the results.
        """
        ret = mock.Mock()
        ret.content = """
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
           <s:Body>
              <u:GetAddressRangeResponse xmlns:u="urn:schemas-upnp-org:service:LANHostConfigManagement:1">
                 <NewMinAddress>10.0.0.2</NewMinAddress>
                 <NewMaxAddress>10.0.0.254</NewMaxAddress>
              </u:GetAddressRangeResponse>
           </s:Body>
        </s:Envelope>
        """
        mock_post.return_value = ret
        action = self.server.find_action('GetAddressRange')
        self.assertIsInstance(action, upnp.Action)
        response = action()
        self.assertIsInstance(response, dict)
        self.assertEqual(response['NewMinAddress'], '10.0.0.2')
        self.assertEqual(response['NewMaxAddress'], '10.0.0.254')

    @mock.patch('requests.post')
    def test_callaction_param(self, mock_post): 
        """
        Should be able to call an action with parameters and get the results.
        """
        ret = mock.Mock()
        ret.content = """
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
           <s:Body>
              <u:GetGenericPortMappingEntryResponse xmlns:u="urn:schemas-upnp-org:service:Layer3Forwarding:1">
                 <NewInternalClient>10.0.0.1</NewInternalClient>
                 <NewExternalPort>51773</NewExternalPort>
                 <NewEnabled>true</NewEnabled>
              </u:GetGenericPortMappingEntryResponse>
           </s:Body>
        </s:Envelope>
        """
        mock_post.return_value = ret
        action = self.server.find_action('GetGenericPortMappingEntry')
        response = action(NewPortMappingIndex=0)
        self.assertEqual(response['NewInternalClient'], '10.0.0.1')
        self.assertEqual(response['NewExternalPort'], 51773)
        self.assertEqual(response['NewEnabled'], True)

    def test_callaction_param_missing(self):
        """
        Calling an action without its parameters should raise a UPNPError.
        """
        action = self.server.find_action('GetGenericPortMappingEntry')
        self.assertRaises(upnp.UPNPError, action)

    def test_callaction_param_invalid_ui2(self):
        """
        Calling an action with an invalid data type should raise a UPNPError.
        """
        action = self.server.find_action('GetGenericPortMappingEntry')
        self.assertRaises(upnp.ValidationError, action, NewPortMappingIndex='ZERO')

    @mock.patch('requests.post')
    def test_callaction_param_mashal_out(self, mock_post):
        """
        Values should be marshalled into the appropriate Python data types.
        """
        ret = mock.Mock()
        ret.content = """
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
           <s:Body>
              <u:GetGenericPortMappingEntryResponse xmlns:u="urn:schemas-upnp-org:service:Layer3Forwarding:1">
                 <NewInternalClient>10.0.0.1</NewInternalClient>
                 <NewExternalPort>51773</NewExternalPort>
                 <NewEnabled>true</NewEnabled>
              </u:GetGenericPortMappingEntryResponse>
           </s:Body>
        </s:Envelope>
        """
        mock_post.return_value = ret
        action = self.server.find_action('GetGenericPortMappingEntry')
        response = action(NewPortMappingIndex=0)

        self.assertIsInstance(response['NewInternalClient'], basestring)
        self.assertIsInstance(response['NewExternalPort'], int)
        self.assertIsInstance(response['NewEnabled'], bool)

    def test_callaction_nonexisting(self):
        """
        When a non-existent action is called, an InvalidActionException should be raised.
        """
        service = self.server.services[0]
        try:
            service('NoSuchFunction')
            self.fail('An InvalidActionException should be raised.')
        except upnp.InvalidActionException:
            pass

    @mock.patch('requests.post')
    def test_callaction_upnperror(self, mock_post):
        """
        UPNPErrors should be raised with the correct error code and description.
        """
        exc = requests.exceptions.HTTPError(500)
        exc.response = mock.Mock()
        exc.response.content = """
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
          <s:Body>
            <s:Fault>
              <faultcode>s:Client</faultcode>
              <faultstring>UPnPError</faultstring>
              <detail>
                <UPnPError xmlns="urn:schemas-upnp-org:control-1-0">
                  <errorCode>401</errorCode>
                  <errorDescription>Invalid Action</errorDescription>
                </UPnPError>
              </detail>
            </s:Fault>
          </s:Body>
        </s:Envelope>
        """.strip()
        mock_post.side_effect = exc
        action = self.server.find_action('SetDefaultConnectionService')
        try:
            action(NewDefaultConnectionService='foo')
        except upnp.soap.SOAPError as exc:
            code, desc = exc.args
            self.assertEqual(code, 401)
            self.assertEqual(desc, 'Invalid Action')

    @mock.patch('requests.Session.send', side_effect=EndPrematurelyException)
    def test_subscribe(self, mock_send):
        """
        Should perform a well formed HTTP SUBSCRIBE request.
        """
        cb_url = 'http://127.0.0.1/'
        try:
            self.server.layer3f.subscribe(cb_url, timeout=123)
        except EndPrematurelyException:
            pass
        req = mock_send.call_args[0][0]
        self.assertEqual(req.method, 'SUBSCRIBE')
        self.assertEqual(req.url, 'http://127.0.0.1:%s/upnp/event/layer3f' % self.httpd_port)
        self.assertEqual(req.body, None)
        self.assertEqual(req.headers['NT'], 'upnp:event')
        self.assertEqual(req.headers['CALLBACK'], '<%s>' % cb_url)
        self.assertEqual(req.headers['HOST'], '127.0.0.1:%s' % self.httpd_port)
        self.assertEqual(req.headers['TIMEOUT'], 'Second-123')

    @mock.patch('requests.Session.send', side_effect=EndPrematurelyException)
    def test_renew_subscription(self, mock_send):
        """
        Should perform a well formed HTTP SUBSCRIBE request on sub renewal.
        """
        sid = 'abcdef'
        try:
            self.server.layer3f.renew_subscription(sid, timeout=123)
        except EndPrematurelyException:
            pass
        req = mock_send.call_args[0][0]
        self.assertEqual(req.method, 'SUBSCRIBE')
        self.assertEqual(req.url, 'http://127.0.0.1:%s/upnp/event/layer3f' % self.httpd_port)
        self.assertEqual(req.body, None)
        self.assertEqual(req.headers['HOST'], '127.0.0.1:%s' % self.httpd_port)
        self.assertEqual(req.headers['SID'], sid)
        self.assertEqual(req.headers['TIMEOUT'], 'Second-123')

    @mock.patch('requests.Session.send', side_effect=EndPrematurelyException)
    def test_cancel_subscription(self, mock_send):
        """
        Should perform a well formed HTTP UNSUBSCRIBE request on sub cancellation.
        """
        sid = 'abcdef'
        try:
            self.server.layer3f.cancel_subscription(sid)
        except EndPrematurelyException:
            pass
        req = mock_send.call_args[0][0]
        self.assertEqual(req.method, 'UNSUBSCRIBE')
        self.assertEqual(req.url, 'http://127.0.0.1:%s/upnp/event/layer3f' % self.httpd_port)
        self.assertEqual(req.body, None)
        self.assertEqual(req.headers['HOST'], '127.0.0.1:%s' % self.httpd_port)
        self.assertEqual(req.headers['SID'], sid)

    @mock.patch('requests.Session.send', side_effect=EndPrematurelyException)
    def test_args_order(self, mock_send):
        """
        Arguments should be called in the order they're listed in the specification.
        This test is non-deterministic, as there's a chance that the arguments will
        naturally end up in the correct order. However, I've deemed this pretty much
        OK because the chance of that happening is one in four hundred and three
        septillion, two hundred and ninety one sextillion, four hundred and sixty
        one quintillion, one hundred and twenty six quadrillion, six hundred and five
        trillion, six hundred and thirty five billion, five hundred and eighty four
        million (403,291,461,126,605,635,584,000,000). Good luck! :)
        """
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        args_in = list(alphabet)
        try:
            self.server.lanhcm.InArgsTest(**{x: 'test' for x in args_in})
        except EndPrematurelyException:
            pass
        req = mock_send.call_args[0][0]
        tree = etree.fromstring(req.body)
        nsmap = tree.nsmap.copy()
        nsmap.update({'m': 'urn:schemas-upnp-org:service:LANHostConfigManagement:1'})
        args = [x.tag for x in tree.xpath(
            'SOAP-ENV:Body/m:InArgsTest', namespaces=nsmap)[0].getchildren()]
        self.assertEqual(''.join(args), alphabet)

    def test_args_order_read_ok(self):
        """
        Make sure that the arguments in the XML are read in order by lxml.
        """
        xpath = (
            's:actionList/s:action/s:name[text()="InArgsTest"]/../s:argumentList/s:argument/s:name')
        xml = self.server.service_map['lanhcm'].scpd_xml
        args = xml.xpath(xpath, namespaces={'s': xml.nsmap[None]})
        self.assertEqual(''.join(x.text for x in args), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')


class TestUPnPClient(unittest.TestCase):
    @mock.patch('upnpclient.ssdp.Device', return_value='test string')
    @mock.patch('upnpclient.ssdp.scan')
    def test_discover(self, mock_scan, mock_server):
        """
        discover() should call netdisco's scan function and return a list of unique servers.
        """
        url = 'http://www.example.com'
        entry = mock.Mock()
        entry.location = url
        mock_scan.return_value = [entry, entry]
        ret = upnp.discover()
        mock_scan.assert_called()
        mock_server.assert_called_with(url)
        self.assertEqual(ret, ['test string'])

    @mock.patch('upnpclient.ssdp.Device', side_effect=Exception)
    @mock.patch('upnpclient.ssdp.scan')
    def test_discover_exception(self, mock_scan, mock_server):
        """
        If unable to read a discovered server's root XML file, it should not appear in the list.
        """
        url = 'http://www.example.com'
        entry = mock.Mock()
        entry.location = url
        mock_scan.return_value = [entry]
        ret = upnp.discover()
        mock_scan.assert_called()
        mock_server.assert_called_with(url)
        self.assertEqual(ret, [])

    def test_validate_date(self):
        """
        Should validate the 'date' type.
        """
        ret = upnp.Action.validate_arg('2017-08-11', dict(datatype='date'))
        self.assertEqual(ret, (True, set()))

    def test_validate_bad_date(self):
        """
        Bad 'date' type should fail validation.
        """
        valid, reasons = upnp.Action.validate_arg('2017-13-13', dict(datatype='date'))
        print(reasons)
        self.assertTrue(reasons)
        self.assertFalse(valid)

    def test_validate_date_with_time(self):
        """
        Should raise a ValidationError if a 'date' contains a time.
        """
        valid, reasons = upnp.Action.validate_arg('2017-13-13T12:34:56', dict(datatype='date'))
        print(reasons)
        self.assertTrue(reasons)
        self.assertFalse(valid)

    def test_marshal_date(self):
        """
        Should parse a valid date into a `datetime.date` object.
        """
        marshalled, val = upnp.marshal.marshal_value('date', '2017-08-11')
        self.assertTrue(marshalled)
        self.assertIsInstance(val, datetime.date)
        tests = dict(
            year=2017,
            month=8,
            day=11
        )
        for key, value in tests.items():
            self.assertEqual(getattr(val, key), value)

    def test_marshal_datetime(self):
        """
        Should parse and marshal a 'dateTime' into a timezone naive `datetime.datetime`.
        """
        marshalled, val = upnp.marshal.marshal_value('dateTime', '2017-08-11T12:34:56')
        self.assertTrue(marshalled)
        self.assertIsInstance(val, datetime.datetime)
        tests = dict(
            year=2017,
            month=8,
            day=11,
            hour=12,
            minute=34,
            second=56
        )
        for key, value in tests.items():
            self.assertEqual(getattr(val, key), value)
        self.assertEqual(val.tzinfo, None)

    def test_marshal_datetime_tz(self):
        """
        Should parse and marshal a 'dateTime.tz' into a timezone aware `datetime.datetime`.
        """
        marshalled, val = upnp.marshal.marshal_value('dateTime.tz', '2017-08-11T12:34:56+1:00')
        self.assertTrue(marshalled)
        self.assertIsInstance(val, datetime.datetime)
        tests = dict(
            year=2017,
            month=8,
            day=11,
            hour=12,
            minute=34,
            second=56
        )
        for key, value in tests.items():
            self.assertEqual(getattr(val, key), value)
        self.assertEqual(val.utcoffset(), datetime.timedelta(hours=1))

    def test_validate_time_illegal_tz(self):
        """
        Should fail validation if 'time' contains a timezone.
        """
        valid, reasons = upnp.Action.validate_arg('12:34:56+1:00', dict(datatype='time'))
        print(reasons)
        self.assertTrue(reasons)
        self.assertFalse(valid)

    def test_marshal_time(self):
        """
        Should parse a 'time' into a timezone naive `datetime.time`.
        """
        marshalled, val = upnp.marshal.marshal_value('time', '12:34:56')
        self.assertTrue(marshalled)
        self.assertIsInstance(val, datetime.time)
        tests = dict(
            hour=12,
            minute=34,
            second=56
        )
        for key, value in tests.items():
            self.assertEqual(getattr(val, key), value)
        self.assertEqual(val.tzinfo, None)

    def test_marshal_time_tz(self):
        """
        Should parse a 'time.tz' into a timezone aware `datetime.time`.
        """
        marshalled, val = upnp.marshal.marshal_value('time.tz', '12:34:56+1:00')
        self.assertTrue(marshalled)
        self.assertIsInstance(val, datetime.time)
        tests = dict(
            hour=12,
            minute=34,
            second=56
        )
        for key, value in tests.items():
            self.assertEqual(getattr(val, key), value)
        self.assertEqual(val.utcoffset(), datetime.timedelta(hours=1))

    def test_marshal_bool(self):
        """
        Should parse a 'boolean' into a `bool`.
        """
        valid_true = ('1', 'true', 'TRUE', 'True', 'yes', 'YES', 'Yes')
        valid_false = ('0', 'false', 'FALSE', 'False', 'no', 'NO', 'No')
        tests = (
            list(zip(valid_true, [True]*len(valid_true))) +
            list(zip(valid_false, [False]*len(valid_false)))
        )
        for item, test in tests:
            marshalled, val = upnp.marshal.marshal_value('boolean', item)
            self.assertTrue(marshalled)
            self.assertEqual(val, test)

    def test_validate_bad_bool(self):
        """
        Should raise a ValidationError if an invalid 'boolean' is provided.
        """
        valid, reasons = upnp.Action.validate_arg('2', dict(datatype='boolean'))
        print(reasons)
        self.assertTrue(reasons)
        self.assertFalse(valid)

    def test_validate_base64(self):
        """
        Should validate a 'bin.base64' value.
        """
        bstring = 'Hello, World!'.encode('utf8')
        encoded = base64.b64encode(bstring)
        valid, reasons = upnp.Action.validate_arg(encoded, dict(datatype='bin.base64'))
        print(reasons)
        self.assertFalse(reasons)
        self.assertTrue(valid)

    def test_marshal_base64(self):
        """
        Should simply leave the base64 string as it is.
        """
        bstring = 'Hello, World!'.encode('utf8')
        encoded = base64.b64encode(bstring)
        marshalled, val = upnp.marshal.marshal_value('bin.base64', encoded)
        self.assertTrue(marshalled)
        self.assertEqual(val, encoded)

    def test_validate_hex(self):
        """
        Should validate a 'bin.hex' value.
        """
        bstring = 'Hello, World!'.encode('ascii')
        valid, reasons = upnp.Action.validate_arg(
            binascii.hexlify(bstring), dict(datatype='bin.hex'))
        print(reasons)
        self.assertFalse(reasons)
        self.assertTrue(valid)

    def test_marshal_hex(self):
        """
        Should simply leave the hex string as it is.
        """
        bstring = 'Hello, World!'.encode('ascii')
        encoded = binascii.hexlify(bstring)
        marshalled, val = upnp.marshal.marshal_value('bin.hex', encoded)
        self.assertTrue(marshalled)
        self.assertEqual(val, encoded)

    def test_validate_uri(self):
        """
        Should validate a 'uri' value.
        """
        uri = 'https://media.giphy.com/media/22kxQ12cxyEww/giphy.gif?something=variable'
        valid, reasons = upnp.Action.validate_arg(uri, dict(datatype='uri'))
        print(reasons)
        self.assertFalse(reasons)
        self.assertTrue(valid)

    def test_marshal_uri(self):
        """
        Should parse a 'uri' value into a `ParseResult`.
        """
        uri = 'https://media.giphy.com/media/22kxQ12cxyEww/giphy.gif?something=variable'
        marshalled, val = upnp.marshal.marshal_value('uri', uri)
        self.assertTrue(marshalled)
        self.assertIsInstance(val, ParseResult)

    def test_validate_uuid(self):
        """
        Should validate a 'uuid' value.
        """
        uuid = 'bec6d681-a6af-4e7d-8b31-bcb78018c814'
        valid, reasons = upnp.Action.validate_arg(uuid, dict(datatype='uuid'))
        print(reasons)
        self.assertFalse(reasons)
        self.assertTrue(valid)

    def test_validate_bad_uuid(self):
        """
        Should reject badly formatted 'uuid' values.
        """
        uuid = 'bec-6d681a6af-4e7d-8b31-bcb78018c814'
        valid, reasons = upnp.Action.validate_arg(uuid, dict(datatype='uuid'))
        self.assertTrue(reasons)
        self.assertFalse(valid)

    def test_marshal_uuid(self):
        """
        Should parse a 'uuid' into a `uuid.UUID`.
        """
        uuid = 'bec6d681-a6af-4e7d-8b31-bcb78018c814'
        marshalled, val = upnp.marshal.marshal_value('uuid', uuid)
        self.assertTrue(marshalled)
        self.assertIsInstance(val, UUID)

    def test_validate_subscription_response(self):
        """
        Should validate the sub response and return sid and timeout.
        """
        sid = 'abcdef'
        timeout = 123
        resp = mock.Mock()
        resp.headers = dict(SID=sid, Timeout='Second-%s' % timeout)
        rsid, rtimeout = upnp.Service.validate_subscription_response(resp)
        self.assertEqual(rsid, sid)
        self.assertEqual(rtimeout, timeout)

    def test_validate_subscription_response_caps(self):
        """
        Should validate the sub response and return sid and timeout regardless of capitalisation.
        """
        sid = 'abcdef'
        timeout = 123
        resp = mock.Mock()
        resp.headers = dict(sid=sid, TIMEOUT='SeCoNd-%s' % timeout)
        rsid, rtimeout = upnp.Service.validate_subscription_response(resp)
        self.assertEqual(rsid, sid)
        self.assertEqual(rtimeout, timeout)

    def test_validate_subscription_response_infinite(self):
        """
        Should validate the sub response and return None as the timeout.
        """
        sid = 'abcdef'
        timeout = 'infinite'
        resp = mock.Mock()
        resp.headers = dict(SID=sid, Timeout='Second-%s' % timeout)
        rsid, rtimeout = upnp.Service.validate_subscription_response(resp)
        self.assertEqual(rsid, sid)
        self.assertEqual(rtimeout, None)

    def test_validate_subscription_response_no_timeout(self):
        """
        Should raise UnexpectedResponse if timeout is missing.
        """
        resp = mock.Mock()
        resp.headers = dict(SID='abcdef')
        self.assertRaises(
            upnp.UnexpectedResponse,
            upnp.Service.validate_subscription_response,
            resp)

    def test_validate_subscription_response_no_sid(self):
        """
        Should raise UnexpectedResponse if sid is missing.
        """
        resp = mock.Mock()
        resp.headers = dict(Timeout='Second-123')
        self.assertRaises(
            upnp.UnexpectedResponse,
            upnp.Service.validate_subscription_response,
            resp)

    def test_validate_subscription_response_bad_timeout(self):
        """
        Should raise UnexpectedResponse if timeout is in the wrong format.
        """
        resp = mock.Mock()
        resp.headers = dict(SID='abcdef', Timeout='123')
        self.assertRaises(
            upnp.UnexpectedResponse,
            upnp.Service.validate_subscription_response,
            resp)

    def test_validate_subscription_response_bad_timeout2(self):
        """
        Should raise UnexpectedResponse if timeout is not an int/infinite.
        """
        resp = mock.Mock()
        resp.headers = dict(SID='abcdef', Timeout='Second-abc')
        self.assertRaises(
            upnp.UnexpectedResponse,
            upnp.Service.validate_subscription_response,
            resp)

    def test_validate_subscription_renewal_response(self):
        """
        Should validate the sub renewal response and return the timeout.
        """
        timeout = 123
        resp = mock.Mock()
        resp.headers = dict(Timeout='Second-%s' % timeout)
        rtimeout = upnp.Service.validate_subscription_renewal_response(resp)
        self.assertEqual(rtimeout, timeout)

    def test_validate_subscription_renewal_response_infinite(self):
        """
        Should validate the sub renewal response and return None as the timeout.
        """
        timeout = 'infinite'
        resp = mock.Mock()
        resp.headers = dict(Timeout='Second-%s' % timeout)
        rtimeout = upnp.Service.validate_subscription_renewal_response(resp)
        self.assertEqual(rtimeout, None)

    def test_validate_subscription_renewal_response_no_timeout(self):
        """
        Should raise UnexpectedResponse if timeout is missing.
        """
        resp = mock.Mock()
        resp.headers = dict()
        self.assertRaises(
            upnp.UnexpectedResponse,
            upnp.Service.validate_subscription_renewal_response,
            resp)

    def test_validate_subscription_renewal_response_bad_timeout(self):
        """
        Should raise UnexpectedResponse if timeout is in the wrong format.
        """
        resp = mock.Mock()
        resp.headers = dict(Timeout='123')
        self.assertRaises(
            upnp.UnexpectedResponse,
            upnp.Service.validate_subscription_renewal_response,
            resp)

    def test_validate_subscription_renewal_response_bad_timeout2(self):
        """
        Should raise UnexpectedResponse if timeout is not an int/infinite.
        """
        resp = mock.Mock()
        resp.headers = dict(Timeout='Second-abc')
        self.assertRaises(
            upnp.UnexpectedResponse,
            upnp.Service.validate_subscription_renewal_response,
            resp)


class TestSOAP(unittest.TestCase):
    @mock.patch('requests.post', side_effect=EndPrematurelyException)
    def test_call(self, mock_post):
        url = 'http://www.example.com'
        soap = upnp.soap.SOAP(url, 'test')
        self.assertRaises(EndPrematurelyException, soap.call, 'TestAction')
        mock_post.assert_called()
        args, _ = mock_post.call_args
        call_url, body = args
        self.assertEqual(url, call_url)
        etree.fromstring(body)

    @mock.patch('requests.post')
    def test_non_xml_error(self, mock_post):
        exc = requests.exceptions.HTTPError()
        exc.response = mock.Mock()
        exc.response.content = 'this is not valid xml'
        mock_post.side_effect = exc
        soap = upnp.soap.SOAP('http://www.example.com', 'test')
        self.assertRaises(requests.exceptions.HTTPError, soap.call, 'TestAction')

    @mock.patch('requests.post')
    def test_missing_error_code_element(self, mock_post):
        exc = requests.exceptions.HTTPError()
        exc.response = mock.Mock()
        exc.response.content = """
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
          <s:Body>
            <s:Fault>
              <faultcode>s:Client</faultcode>
              <faultstring>UPnPError</faultstring>
              <detail>
                <UPnPError xmlns="urn:schemas-upnp-org:control-1-0">
                  <errorDescription>Invalid Action</errorDescription>
                </UPnPError>
              </detail>
            </s:Fault>
          </s:Body>
        </s:Envelope>
        """.strip()
        mock_post.side_effect = exc
        soap = upnp.soap.SOAP('http://www.example.com', 'test')
        self.assertRaises(upnp.soap.SOAPProtocolError, soap.call, 'TestAction')

    @mock.patch('requests.post')
    def test_missing_error_description_element(self, mock_post):
        exc = requests.exceptions.HTTPError()
        exc.response = mock.Mock()
        exc.response.content = """
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
          <s:Body>
            <s:Fault>
              <faultcode>s:Client</faultcode>
              <faultstring>UPnPError</faultstring>
              <detail>
                <UPnPError xmlns="urn:schemas-upnp-org:control-1-0">
                  <errorCode>401</errorCode>
                </UPnPError>
              </detail>
            </s:Fault>
          </s:Body>
        </s:Envelope>
        """.strip()
        mock_post.side_effect = exc
        soap = upnp.soap.SOAP('http://www.example.com', 'test')
        self.assertRaises(upnp.soap.SOAPProtocolError, soap.call, 'TestAction')

    @mock.patch('requests.post')
    def test_missing_response_element(self, mock_post):
        ret = mock.Mock()
        ret.content = """
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
           <s:Body>
              <u:SomeOtherElement xmlns:u="urn:schemas-upnp-org:service:Layer3Forwarding:1">
                 <NewEnabled>true</NewEnabled>
              </u:SomeOtherElement>
           </s:Body>
        </s:Envelope>
        """
        mock_post.return_value = ret
        soap = upnp.soap.SOAP('http://www.example.com', 'test')
        self.assertRaises(upnp.soap.SOAPProtocolError, soap.call, 'TestAction')


class TestErrors(unittest.TestCase):
    desc = upnp.errors.ERR_CODE_DESCRIPTIONS

    def test_existing_err(self):
        for key, value in self.desc._descriptions.items():
            self.assertEqual(self.desc[key], value)

    def test_non_integer(self):
        try:
            self.desc['a string']
            raise Exception('Should have raised KeyError.')
        except KeyError as exc:
            self.assertEqual(str(exc), '"\'key\' must be an integer"')

    def test_reserved(self):
        for i in range(606, 612+1):  # 606-612
            self.assertEqual(self.desc[i], 'These ErrorCodes are reserved for UPnP DeviceSecurity.')

    def test_common_action(self):
        for i in range(613, 699+1):
            self.assertEqual(
                self.desc[i], 'Common action errors. Defined by UPnP Forum Technical Committee.')

    def test_action_specific_committee(self):
        for i in range(700, 799+1):
            self.assertEqual(
                self.desc[i], 'Action-specific errors defined by UPnP Forum working committee.')

    def test_action_specific_vendor(self):
        for i in range(800, 899+1):
            self.assertEqual(
                self.desc[i],
                'Action-specific errors for non-standard actions. Defined by UPnP vendor.')
