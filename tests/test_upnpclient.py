import unittest
import threading
import os.path as path
import os
import datetime
import base64
import binascii
from uuid import UUID

import mock

import upnpclient as upnp
import requests
from requests.compat import basestring


try:
    import http.server as httpserver
except ImportError:
    import SimpleHTTPServer as httpserver

try:
    import socketserver as sockserver
except ImportError:
    import SocketServer as sockserver


class TestUPNP(unittest.TestCase):
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
        self.server = upnp.Server('http://127.0.0.1:%s/upnp/IGD.xml' % self.httpd_port)

    def test_discover(self):
        upnp_servers = upnp.discover(1)

    def test_server(self):
        server = upnp.Server('http://127.0.0.1:%s/upnp/IGD.xml' % self.httpd_port)

    def test_server_props(self):
        server = upnp.Server('http://127.0.0.1:%s/upnp/IGD.xml' % self.httpd_port)
        self.assertEqual(server.device_type, 'urn:schemas-upnp-org:device:InternetGatewayDevice:1')
        self.assertEqual(server.friendly_name, 'SpeedTouch 5x6 (0320FJ2PZ)')
        self.assertEqual(server.manufacturer, 'Pannaway')
        self.assertEqual(server.model_description, 'DSL Internet Gateway Device')
        self.assertEqual(server.model_name, 'Pannaway')
        self.assertEqual(server.model_number, 'RG-210')
        self.assertEqual(server.serial_number, '0320FJ2PZ')

    def test_server_nonexists(self):
        self.assertRaises(
            requests.exceptions.HTTPError,
            upnp.Server,
            'http://127.0.0.1:%s/upnp/DOESNOTEXIST.xml' % self.httpd_port
        )

    def test_services(self):
        service_ids = [service.service_id for service in self.server.services]
        self.assertIn('urn:upnp-org:serviceId:layer3f', service_ids)
        self.assertIn('urn:upnp-org:serviceId:lanhcm', service_ids)
        self.assertIn('urn:upnp-org:serviceId:wancic', service_ids)

    def test_actions(self):
        actions = []
        [actions.extend(service.actions) for service in self.server.services]
        action_names = [action.name for action in actions]
        self.assertIn('SetDefaultConnectionService', action_names)
        self.assertIn('GetCommonLinkProperties', action_names)
        self.assertIn('GetDNSServers', action_names)
        self.assertIn('GetDHCPRelay', action_names)

    def test_findaction_server(self):
        action = self.server.find_action('GetSubnetMask')
        self.assertIsInstance(action, upnp.Action)

    def test_findaction_server_nonexists(self):
        action = self.server.find_action('GetNoneExistingAction')
        self.assertEqual(action, None)

    def test_findaction_service_nonexists(self):
        service = self.server.services[0]
        action = self.server.find_action('GetNoneExistingAction')
        self.assertEqual(action, None)

    @mock.patch('requests.post')
    def test_callaction_server(self, mock_post):
        ret = mock.Mock()
        ret.text = """
        <?xml version="1.0" encoding="UTF-8"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
           <s:Body>
              <u:GetSubnetMaskResponse xmlns:u="urn:schemas-upnp-org:service:LANHostConfigManagement:1">
                 <NewSubnetMask>255.255.255.0</NewSubnetMask>
              </u:GetSubnetMaskResponse>
           </s:Body>
        </s:Envelope>
        """
        mock_post.return_value = ret
        self.server.call('GetSubnetMask')

    @mock.patch('requests.post')
    def test_callaction_noparam(self, mock_post):
        ret = mock.Mock()
        ret.text = """
        <?xml version="1.0" encoding="UTF-8"?>
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
        response = action.call()
        self.assertIn('NewMinAddress', response)
        self.assertIn('NewMaxAddress', response)

    @mock.patch('requests.post')
    def test_callaction_param(self, mock_post):
        ret = mock.Mock()
        ret.text = """
        <?xml version="1.0" encoding="UTF-8"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
           <s:Body>
              <u:SetDomainNameResponse xmlns:u="urn:schemas-upnp-org:service:LANHostConfigManagement:1">
                 <NewDomainName>github.com</NewDomainName>
              </u:SetDomainNameResponse>
           </s:Body>
        </s:Envelope>
        """
        mock_post.return_value = ret
        action = self.server.find_action('SetDomainName')
        response = action.call({'NewDomainName': 'github.com'})
        self.assertIn('NewDomainName', response)

    @mock.patch('requests.post')
    def test_callaction_param_kw(self, mock_post):
        ret = mock.Mock()
        ret.text = """
        <?xml version="1.0" encoding="UTF-8"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
           <s:Body>
              <u:GetGenericPortMappingEntryResponse xmlns:u="urn:schemas-upnp-org:service:LANHostConfigManagement:1">
                 <NewInternalClient>10.0.0.1</NewInternalClient>
                 <NewExternalPort>51773</NewExternalPort>
                 <NewEnabled>true</NewEnabled>
              </u:GetGenericPortMappingEntryResponse>
           </s:Body>
        </s:Envelope>
        """
        mock_post.return_value = ret
        action = self.server.find_action('GetGenericPortMappingEntry')
        response = action.call(NewPortMappingIndex=0)
        self.assertIn('NewInternalClient', response)
        self.assertIn('NewExternalPort', response)
        self.assertIn('NewEnabled', response)

    def test_callaction_param_missing(self):
        action = self.server.find_action('GetGenericPortMappingEntry')
        self.assertRaises(upnp.UPNPError, action.call)

    def test_callaction_param_invalid_ui2(self):
        action = self.server.find_action('GetGenericPortMappingEntry')
        self.assertRaises(upnp.UPNPError, action.call, {'NewPortMappingIndex': 'ZERO'})

    def test_callaction_param_invalid_allowedval(self):
        action = self.server.find_action('GetGenericPortMappingEntry')
        name = 'NewPortMappingIndex'
        arg = 'WRONG'
        statevar = action.argsdef_in[0][1]
        self.assertRaises(upnp.UPNPError, action.validate_arg, name, arg, statevar)

    @mock.patch('requests.post')
    def test_callaction_param_mashall_out(self, mock_post):
        ret = mock.Mock()
        ret.text = """
        <?xml version="1.0" encoding="UTF-8"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
           <s:Body>
              <u:GetGenericPortMappingEntryResponse xmlns:u="urn:schemas-upnp-org:service:LANHostConfigManagement:1">
                 <NewInternalClient>10.0.0.1</NewInternalClient>
                 <NewExternalPort>51773</NewExternalPort>
                 <NewEnabled>true</NewEnabled>
              </u:GetGenericPortMappingEntryResponse>
           </s:Body>
        </s:Envelope>
        """
        mock_post.return_value = ret
        action = self.server.find_action('GetGenericPortMappingEntry')
        response = action.call(NewPortMappingIndex=0)

        self.assertIsInstance(response['NewInternalClient'], basestring)
        self.assertIsInstance(response['NewExternalPort'], int)
        self.assertIsInstance(response['NewEnabled'], bool)

    def test_callaction_nonexisting(self):
        service = self.server.services[0]
        try:
            service.call('NoSuchFunction')
        except upnp.SOAPError as e:
            self.assertEqual(e.args[0], 401)
            self.assertEqual(e.args[1], 'Invalid action')

    @mock.patch('requests.post', side_effect=requests.exceptions.HTTPError("""
        <xml>
          <errorCode>401</errorCode>
          <errorDescription>Invalid action</errorDescription>
        </xml>
        """.strip()))
    def test_callaction_forbidden(self, mock_post):
        action = self.server.find_action('SetDefaultConnectionService')
        try:
            action.call({'NewDefaultConnectionService': 'foo'})
        except upnp.SOAPError as e:
            self.assertEqual(e.args[0], 401)
            self.assertEqual(e.args[1], 'Invalid action')

    def test_validate_date(self):
        v = upnp.Action.validate_arg("testarg", "2017-08-11", dict(datatype="date"))
        self.assertIsInstance(v, datetime.date)
        tests = dict(
            year=2017,
            month=8,
            day=11
        )
        for key, value in tests.items():
            self.assertEqual(getattr(v, key), value)

    def test_validate_bad_date(self):
        self.assertRaises(
            upnp.UPNPError, upnp.Action.validate_arg, "testarg",
            "2017-13-13", dict(datatype="date")
        )

    def test_validate_date_with_time(self):
        self.assertRaises(
            upnp.UPNPError, upnp.Action.validate_arg, "testarg",
            "2017-08-11T12:34:56", dict(datatype="date"))

    def test_validate_datetime(self):
        v = upnp.Action.validate_arg("testarg", "2017-08-11T12:34:56", dict(datatype="dateTime"))
        self.assertIsInstance(v, datetime.datetime)
        tests = dict(
            year=2017,
            month=8,
            day=11,
            hour=12,
            minute=34,
            second=56
        )
        for key, value in tests.items():
            self.assertEqual(getattr(v, key), value)
        self.assertEqual(v.utcoffset(), None)

    def test_validate_datetime_tz(self):
        v = upnp.Action.validate_arg(
            "testarg", "2017-08-11T12:34:56+1:00", dict(datatype="dateTime.tz"))
        self.assertIsInstance(v, datetime.datetime)
        tests = dict(
            year=2017,
            month=8,
            day=11,
            hour=12,
            minute=34,
            second=56
        )
        for key, value in tests.items():
            self.assertEqual(getattr(v, key), value)
        self.assertEqual(v.utcoffset(), datetime.timedelta(hours=1))

    def test_validate_time(self):
        v = upnp.Action.validate_arg(
            "testarg", "12:34:56", dict(datatype="time"))
        self.assertIsInstance(v, datetime.time)
        tests = dict(
            hour=12,
            minute=34,
            second=56
        )
        for key, value in tests.items():
            self.assertEqual(getattr(v, key), value)

    def test_validate_time_illegal_tz(self):
        self.assertRaises(upnp.UPNPError, upnp.Action.validate_arg,
            "testarg", "12:34:56+1:00", dict(datatype="time"))

    def test_validate_time_tz(self):
        v = upnp.Action.validate_arg(
            "testarg", "12:34:56+1:00", dict(datatype="time.tz"))
        self.assertIsInstance(v, datetime.time)
        tests = dict(
            hour=12,
            minute=34,
            second=56
        )
        for key, value in tests.items():
            self.assertEqual(getattr(v, key), value)
        self.assertEqual(v.utcoffset(), datetime.timedelta(hours=1))

    def test_validate_bool(self):
        valid_true = ("1", "true", "TRUE", "True", "yes", "YES", "Yes")
        valid_false = ("0", "false", "FALSE", "False", "no", "NO", "No")
        tests = (
            list(zip(valid_true, [True]*len(valid_true))) +
            list(zip(valid_false, [False]*len(valid_false)))
        )
        for item, test in tests:
            v = upnp.Action.validate_arg(
                "testarg", item, dict(datatype="boolean"))
            self.assertEqual(v, test)

    def test_validate_bad_bool(self):
        self.assertRaises(upnp.UPNPError, upnp.Action.validate_arg,
            "testarg", "2", dict(datatype="boolean"))

    def test_validate_base64(self):
        bstring = "Hello, world!".encode("utf8")
        v = upnp.Action.validate_arg(
            "testarg", base64.b64encode(bstring), dict(datatype="bin.base64"))
        self.assertEqual(v, bstring)

    def test_validate_hex(self):
        bstring = "Hello, world!".encode("ascii")
        v = upnp.Action.validate_arg(
            "testarg", binascii.hexlify(bstring), dict(datatype="bin.hex"))
        self.assertEqual(v, bstring)

    def test_validate_uri(self):
        uri = "https://media.giphy.com/media/22kxQ12cxyEww/giphy.gif?something=variable"
        v = upnp.Action.validate_arg(
            "testarg", uri, dict(datatype="uri"))
        self.assertEqual(v, uri)

    def test_validate_uuid(self):
        uuid = "bec6d681-a6af-4e7d-8b31-bcb78018c814"
        v = upnp.Action.validate_arg(
            "testarg", uuid, dict(datatype="uuid"))
        self.assertEqual(v, UUID(uuid))

    def test_validate_bad_uuid(self):
        uuid = "bec-6d681a6af-4e7d-8b31-bcb78018c814"
        self.assertRaises(
            upnp.UPNPError, upnp.Action.validate_arg,
            "testarg", uuid, dict(datatype="uuid"))
