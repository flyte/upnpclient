import unittest
import threading
import os.path as path
import os
import asyncio
from upnpclient.upnp import UnexpectedResponse
import aiohttp
import mock
import requests
from requests.compat import basestring
from lxml import etree
from base64 import b64encode
try:
    import http.server as httpserver
except ImportError:
    import SimpleHTTPServer as httpserver
try:
    import socketserver as sockserver
except ImportError:
    import SocketServer as sockserver

import upnpclient as upnp
from tests.helpers import async_test, add_async_test
from tests.async_server import (
    mock_resp,
    mock_req,
    setup_web_server,
    app,
)

from tests.const import (
    ASYNC_HOST,
    ASYNC_SERVER_ADDR,
    ASYNC_SERVER_PORT,
    HTTP_LOCALHOST,
    LOCALHOST,
    TEST_CALLACTION_NOPARAM,
    TEST_CALLACTION_PARAM,
    TEST_CALLACTION_PARAM_MASHAL_OUT_ASYNC,
    TEST_CALLACTION_UPNPERROR,
    TEST_DEVICE_AUTH,
    TEST_MISSING_ERROR_CODE_ELEMENT,
    TEST_MISSING_ERROR_DESCRIPTION_ELEMENT,
    TEST_MISSING_RESPONSE_ELEMENT,
)


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
        os.chdir(path.join(path.dirname(path.realpath(__file__)), "xml"))
        cls.httpd = sockserver.TCPServer(
            (LOCALHOST, 0), httpserver.SimpleHTTPRequestHandler
        )
        cls.httpd_thread = threading.Thread(target=cls.httpd.serve_forever)
        cls.httpd_thread.daemon = True
        cls.httpd_thread.start()
        cls.httpd_port = cls.httpd.server_address[1]

        with open("upnp/IGD.xml", "w") as out_f:
            with open("upnp/IGD.xml.templ") as in_f:
                out_f.write(in_f.read().format(port=cls.httpd_port))

        cls.xml_resource = "%s:%s/upnp/IGD.xml" % (HTTP_LOCALHOST, cls.httpd_port)

        cls.loop = asyncio.get_event_loop()
        cls.future = cls.loop.run_until_complete(
            setup_web_server(app, host=LOCALHOST, port=ASYNC_SERVER_PORT)
        )

    @classmethod
    def tearDownClass(cls):
        """
        Shut down the HTTP server and delete the IGD.xml file.
        """
        cls.httpd.shutdown()
        try:
            os.unlink("upnp/IGD.xml")
        except OSError:
            pass

    def setUp(self):
        self.server = upnp.Device(self.xml_resource)

        async def run():
            self.session = aiohttp.ClientSession()
            self.async_server = upnp.Device(
                self.xml_resource,
                use_async=True,
                session=self.session
            )
            await self.async_server.async_init()
        self.loop.run_until_complete(run())

    def tearDown(self):
        mock_resp.clear()

        async def run():
            await self.session.close()
        self.loop.run_until_complete(run())

    @mock.patch("requests.post")
    def test_device_auth(self, mock_post):
        auth = ("myuser", "mypassword")
        device = upnp.Device(self.xml_resource, http_auth=auth)
        ret = mock.Mock()
        ret.content = TEST_DEVICE_AUTH
        mock_post.return_value = ret
        ret = device("GetSubnetMask")
        _, kwargs = mock_post.call_args
        self.assertIn("auth", kwargs)
        self.assertEqual(kwargs["auth"], auth)

    @async_test
    async def test_device_auth_async(self):
        auth = ("myuser", "mypassword")
        device = upnp.Device(self.xml_resource, http_auth=auth, use_async=True)
        await device.async_init()
        device.find_action("GetSubnetMask").url = ASYNC_SERVER_ADDR
        mock_resp.text = TEST_DEVICE_AUTH
        await device("GetSubnetMask")
        basic_auth_string = f"{auth[0]}:{auth[1]}"
        b64 = b64encode(basic_auth_string.encode("utf-8")).decode()
        self.assertEqual("Basic %s" % b64, mock_req.headers["Authorization"])
        await device.session.close()

    @mock.patch("requests.post")
    def test_device_auth_call_override(self, mock_post):
        dev_auth = ("devuser", "devpassword")
        call_auth = ("calluser", "callpassword")
        device = upnp.Device(self.xml_resource, http_auth=dev_auth)
        ret = mock.Mock()
        ret.content = TEST_DEVICE_AUTH
        mock_post.return_value = ret
        ret = device("GetSubnetMask", http_auth=call_auth)
        _, kwargs = mock_post.call_args
        self.assertIn("auth", kwargs)
        self.assertEqual(kwargs["auth"], call_auth)

    @async_test
    async def test_device_auth_call_override_async(self):
        dev_auth = ("devuser", "devpassword")
        call_auth = ("calluser", "callpassword")
        device = upnp.Device(self.xml_resource, http_auth=dev_auth, use_async=True)
        await device.async_init()
        device.find_action("GetSubnetMask").url = ASYNC_SERVER_ADDR
        mock_resp.text = TEST_DEVICE_AUTH
        await device("GetSubnetMask", http_auth=call_auth)
        basic_auth_string = f"{call_auth[0]}:{call_auth[1]}"
        b64 = b64encode(basic_auth_string.encode("utf-8")).decode()
        self.assertEqual("Basic %s" % b64, mock_req.headers["Authorization"])
        await device.session.close()

    @mock.patch("requests.post")
    def test_device_auth_call_override_none(self, mock_post):
        dev_auth = ("devuser", "devpassword")
        call_auth = None
        device = upnp.Device(self.xml_resource, http_auth=dev_auth)
        ret = mock.Mock()
        ret.content = TEST_DEVICE_AUTH
        mock_post.return_value = ret
        ret = device("GetSubnetMask", http_auth=call_auth)
        _, kwargs = mock_post.call_args
        self.assertIn("auth", kwargs)
        self.assertEqual(kwargs["auth"], dev_auth)

    @async_test
    async def test_device_auth_call_override_none_async(self):
        auth = ("myuser", "mypassword")
        call_auth = None
        device = upnp.Device(self.xml_resource, http_auth=auth, use_async=True)
        await device.async_init()
        device.find_action("GetSubnetMask").url = ASYNC_SERVER_ADDR
        mock_resp.text = TEST_DEVICE_AUTH
        await device("GetSubnetMask", http_auth=call_auth)
        basic_auth_string = f"{auth[0]}:{auth[1]}"
        b64 = b64encode(basic_auth_string.encode("utf-8")).decode()
        self.assertEqual("Basic %s" % b64, mock_req.headers["Authorization"])
        await device.session.close()

    @mock.patch("requests.post")
    def test_device_auth_none_override(self, mock_post):
        dev_auth = None
        call_auth = ("calluser", "callpassword")
        device = upnp.Device(self.xml_resource, http_auth=dev_auth)
        ret = mock.Mock()
        ret.content = TEST_DEVICE_AUTH
        mock_post.return_value = ret
        ret = device("GetSubnetMask", http_auth=call_auth)
        _, kwargs = mock_post.call_args
        self.assertIn("auth", kwargs)
        self.assertEqual(kwargs["auth"], call_auth)

    @async_test
    async def test_device_auth_none_override_async(self):
        auth = None
        call_auth = ("myuser", "mypassword")
        device = upnp.Device(self.xml_resource, http_auth=auth, use_async=True)
        await device.async_init()
        device.find_action("GetSubnetMask").url = ASYNC_SERVER_ADDR
        mock_resp.text = TEST_DEVICE_AUTH
        await device("GetSubnetMask", http_auth=call_auth)
        basic_auth_string = f"{call_auth[0]}:{call_auth[1]}"
        b64 = b64encode(basic_auth_string.encode("utf-8")).decode()
        self.assertEqual("Basic %s" % b64, mock_req.headers["Authorization"])
        await device.session.close()

    @mock.patch("requests.post")
    def test_device_headers(self, mock_post):
        headers = dict(test="device")
        device = upnp.Device(self.xml_resource, http_headers=headers)
        ret = mock.Mock()
        ret.content = TEST_DEVICE_AUTH
        mock_post.return_value = ret
        ret = device("GetSubnetMask")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["test"], "device")

    @async_test
    async def test_device_headers_async(self):
        headers = dict(test="device")
        device = upnp.Device(self.xml_resource, http_headers=headers, use_async=True)
        await device.async_init()
        device.find_action("GetSubnetMask").url = ASYNC_SERVER_ADDR
        mock_resp.text = TEST_DEVICE_AUTH
        await device("GetSubnetMask")
        self.assertEqual(mock_req.headers["test"], "device")
        await device.session.close()

    @mock.patch("requests.post")
    def test_device_headers_call_override(self, mock_post):
        dev_headers = dict(test="device")
        call_headers = dict(test="call")
        device = upnp.Device(self.xml_resource, http_headers=dev_headers)
        ret = mock.Mock()
        ret.content = TEST_DEVICE_AUTH
        mock_post.return_value = ret
        ret = device("GetSubnetMask", http_headers=call_headers)
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["test"], "call")

    @async_test
    async def test_device_headers_call_override_async(self):
        dev_headers = dict(test="device")
        call_headers = dict(test="call")
        device = upnp.Device(self.xml_resource, http_headers=dev_headers, use_async=True)
        await device.async_init()
        device.find_action("GetSubnetMask").url = ASYNC_SERVER_ADDR
        mock_resp.text = TEST_DEVICE_AUTH
        await device("GetSubnetMask", http_headers=call_headers)
        self.assertEqual(mock_req.headers["test"], "call")
        await device.session.close()

    @mock.patch("requests.post")
    def test_device_headers_call_override_none(self, mock_post):
        dev_headers = dict(test="device")
        call_headers = None
        device = upnp.Device(self.xml_resource, http_headers=dev_headers)
        ret = mock.Mock()
        ret.content = TEST_DEVICE_AUTH
        mock_post.return_value = ret
        ret = device("GetSubnetMask", http_headers=call_headers)
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["test"], "device")

    @async_test
    async def test_device_headers_call_override_none_async(self):
        dev_headers = dict(test="device")
        call_headers = None
        device = upnp.Device(self.xml_resource, http_headers=dev_headers, use_async=True)
        await device.async_init()
        device.find_action("GetSubnetMask").url = ASYNC_SERVER_ADDR
        mock_resp.text = TEST_DEVICE_AUTH
        await device("GetSubnetMask", http_headers=call_headers)
        self.assertEqual(mock_req.headers["test"], "device")
        await device.session.close()

    @mock.patch("requests.post")
    def test_device_headers_none_override(self, mock_post):
        dev_headers = None
        call_headers = dict(test="call")
        device = upnp.Device(self.xml_resource, http_headers=dev_headers)
        ret = mock.Mock()
        ret.content = TEST_DEVICE_AUTH
        mock_post.return_value = ret
        ret = device("GetSubnetMask", http_headers=call_headers)
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["test"], "call")

    @async_test
    async def test_device_headers_none_override_async(self):
        dev_headers = None
        call_headers = dict(test="call")
        device = upnp.Device(self.xml_resource, http_headers=dev_headers, use_async=True)
        await device.async_init()
        device.find_action("GetSubnetMask").url = ASYNC_SERVER_ADDR
        mock_resp.text = TEST_DEVICE_AUTH
        await device("GetSubnetMask", http_headers=call_headers)
        self.assertEqual(mock_req.headers["test"], "call")
        await device.session.close()

    def test_device_props(self):
        """
        `Device` instance should contain the properties from the XML.
        """
        server = upnp.Device(self.xml_resource)
        self.assertEqual(
            server.device_type, "urn:schemas-upnp-org:device:InternetGatewayDevice:1"
        )
        self.assertEqual(server.friendly_name, "SpeedTouch 5x6 (0320FJ2PZ)")
        self.assertEqual(server.manufacturer, "Pannaway")
        self.assertEqual(server.model_description, "DSL Internet Gateway Device")
        self.assertEqual(server.model_name, "Pannaway")
        self.assertEqual(server.model_number, "RG-210")
        self.assertEqual(server.serial_number, "0320FJ2PZ")

    @async_test
    async def test_device_props_async(self):
        """
        `Device` instance should contain the properties from the XML.
        """
        server = upnp.Device(self.xml_resource, use_async=True)
        await server.async_init()
        await server.session.close()
        self.assertEqual(
            server.device_type, "urn:schemas-upnp-org:device:InternetGatewayDevice:1"
        )
        self.assertEqual(server.friendly_name, "SpeedTouch 5x6 (0320FJ2PZ)")
        self.assertEqual(server.manufacturer, "Pannaway")
        self.assertEqual(server.model_description, "DSL Internet Gateway Device")
        self.assertEqual(server.model_name, "Pannaway")
        self.assertEqual(server.model_number, "RG-210")
        self.assertEqual(server.serial_number, "0320FJ2PZ")
        await server.session.close()

    def test_device_nonexists(self):
        """
        Should return `HTTPError` if the XML is not found on the server.
        """
        self.assertRaises(
            requests.exceptions.HTTPError,
            upnp.Device,
            "http://127.0.0.1:%s/upnp/DOESNOTEXIST.xml" % self.httpd_port,
        )

    @async_test
    async def test_device_nonexists_async(self):
        """
        Should return `ClientResponseError` if the XML is not found on the server.
        """
        server = upnp.Device(
            "http://127.0.0.1:%s/upnp/DOESNOTEXIST.xml" % self.httpd_port,
            use_async=True
        )
        with self.assertRaises(aiohttp.client_exceptions.ClientResponseError):
            await server.async_init()
        await server.session.close()

    @add_async_test
    def test_services(self):
        """
        All of the services from the XML should be present in the server services.
        """
        service_ids = [service.service_id for service in self.server.services]
        self.assertIn("urn:upnp-org:serviceId:layer3f", service_ids)
        self.assertIn("urn:upnp-org:serviceId:lanhcm", service_ids)
        self.assertIn("urn:upnp-org:serviceId:wancic", service_ids)

    @add_async_test
    def test_actions(self):
        """
        Action names should be present in the list of device actions.
        """
        action_names = set()
        for action in self.async_server.actions:
            action_names.add(action.name)
        self.assertIn("SetDefaultConnectionService", action_names)
        self.assertIn("GetCommonLinkProperties", action_names)
        self.assertIn("GetDNSServers", action_names)
        self.assertIn("GetDHCPRelay", action_names)

    @add_async_test
    def test_service_actions(self):
        """
        Action names should be present in the list of service actions.
        """
        action_names = set()
        for service in self.server.services:
            for action in service.actions:
                action_names.add(action.name)
        self.assertIn("SetDefaultConnectionService", action_names)
        self.assertIn("GetCommonLinkProperties", action_names)
        self.assertIn("GetDNSServers", action_names)
        self.assertIn("GetDHCPRelay", action_names)

    @add_async_test
    def test_findaction_server(self):
        """
        Should find and return the correct action.
        """
        action = self.server.find_action("GetSubnetMask")
        self.assertIsInstance(action, upnp.Action)
        self.assertEqual(action.name, "GetSubnetMask")

    @add_async_test
    def test_findaction_server_nonexists(self):
        """
        Should return None if no action is found with the given name.
        """
        action = self.server.find_action("GetNoneExistingAction")
        self.assertEqual(action, None)

    @add_async_test
    def test_findaction_service_nonexists(self):
        """
        Should return None if no action is found with the given name.
        """
        action = self.server.find_action("GetNoneExistingAction")
        self.assertEqual(action, None)

    @mock.patch("requests.post")
    def test_callaction_server(self, mock_post):
        """
        Should be able to call the server with the name of an action.
        """
        ret = mock.Mock()
        ret.content = TEST_DEVICE_AUTH
        mock_post.return_value = ret
        ret = self.server("GetSubnetMask")
        self.assertEqual(ret, dict(NewSubnetMask="255.255.255.0"))

    @async_test
    async def test_callaction_server_async(self):
        """
        Should be able to call the server with the name of an action.
        """
        mock_resp.text = TEST_DEVICE_AUTH
        self.async_server.find_action("GetSubnetMask").url = ASYNC_SERVER_ADDR
        ret = await self.async_server("GetSubnetMask")
        self.assertEqual(ret, dict(NewSubnetMask="255.255.255.0"))

    @mock.patch("requests.post")
    def test_callaction_noparam(self, mock_post):
        """
        Should be able to call an action with no params and get the results.
        """
        ret = mock.Mock()
        ret.content = TEST_CALLACTION_NOPARAM
        mock_post.return_value = ret
        action = self.server.find_action("GetAddressRange")
        self.assertIsInstance(action, upnp.Action)
        response = action()
        self.assertIsInstance(response, dict)
        self.assertEqual(response["NewMinAddress"], "10.0.0.2")
        self.assertEqual(response["NewMaxAddress"], "10.0.0.254")

    @async_test
    async def test_callaction_noparam_async(self):
        """
        Should be able to call an action with no params and get the results.
        """
        mock_resp.text = TEST_CALLACTION_NOPARAM
        action = self.async_server.find_action("GetAddressRange")
        action.url = ASYNC_SERVER_ADDR
        self.assertIsInstance(action, upnp.Action)
        response = await action()
        self.assertIsInstance(response, dict)
        self.assertEqual(response["NewMinAddress"], "10.0.0.2")
        self.assertEqual(response["NewMaxAddress"], "10.0.0.254")

    @mock.patch("requests.post")
    def test_callaction_param(self, mock_post):
        """
        Should be able to call an action with parameters and get the results.
        """
        ret = mock.Mock()
        ret.content = TEST_CALLACTION_PARAM
        mock_post.return_value = ret
        action = self.server.find_action("GetGenericPortMappingEntry")
        response = action(NewPortMappingIndex=0)
        self.assertEqual(response["NewInternalClient"], "10.0.0.1")
        self.assertEqual(response["NewExternalPort"], 51773)
        self.assertEqual(response["NewEnabled"], True)

    @async_test
    async def test_callaction_param_async(self):
        """
        Should be able to call an action with parameters and get the results.
        """
        mock_resp.text = TEST_CALLACTION_PARAM
        action = self.async_server.find_action("GetGenericPortMappingEntry")
        action.url = ASYNC_SERVER_ADDR
        response = await action(NewPortMappingIndex=0)
        self.assertEqual(response["NewInternalClient"], "10.0.0.1")
        self.assertEqual(response["NewExternalPort"], 51773)
        self.assertEqual(response["NewEnabled"], True)

    def test_callaction_param_missing(self):
        """
        Calling an action without its parameters should raise a UPNPError.
        """
        action = self.server.find_action("GetGenericPortMappingEntry")
        self.assertRaises(upnp.UPNPError, action)

    @async_test
    async def test_callaction_param_missing_async(self):
        """
        Calling an action without its parameters should raise a UPNPError.
        """
        action = self.async_server.find_action("GetGenericPortMappingEntry")
        with self.assertRaises(upnp.UPNPError):
            await action()

    def test_callaction_param_invalid_ui2(self):
        """
        Calling an action with an invalid data type should raise a UPNPError.
        """
        action = self.server.find_action("GetGenericPortMappingEntry")
        self.assertRaises(upnp.ValidationError, action, NewPortMappingIndex="ZERO")

    @async_test
    async def test_callaction_param_invalid_ui2_async(self):
        """
        Calling an action with an invalid data type should raise a UPNPError.
        """
        action = self.server.find_action("GetGenericPortMappingEntry")
        with self.assertRaises(upnp.ValidationError):
            await action(NewPortMappingIndex="ZERO")

    @mock.patch("requests.post")
    def test_callaction_param_mashal_out(self, mock_post):
        """
        Values should be marshalled into the appropriate Python data types.
        """
        ret = mock.Mock()
        ret.content = TEST_CALLACTION_PARAM_MASHAL_OUT_ASYNC
        mock_post.return_value = ret
        action = self.server.find_action("GetGenericPortMappingEntry")
        response = action(NewPortMappingIndex=0)

        self.assertIsInstance(response["NewInternalClient"], basestring)
        self.assertIsInstance(response["NewExternalPort"], int)
        self.assertIsInstance(response["NewEnabled"], bool)

    @async_test
    async def test_callaction_param_mashal_out_async(self):
        """
        Values should be marshalled into the appropriate Python data types.
        """
        mock_resp.text = TEST_CALLACTION_PARAM_MASHAL_OUT_ASYNC
        action = self.async_server.find_action("GetGenericPortMappingEntry")
        action.url = ASYNC_SERVER_ADDR
        response = await action(NewPortMappingIndex=0)

        self.assertIsInstance(response["NewInternalClient"], basestring)
        self.assertIsInstance(response["NewExternalPort"], int)
        self.assertIsInstance(response["NewEnabled"], bool)

    def test_callaction_nonexisting(self):
        """
        When a non-existent action is called, an InvalidActionException should be raised.
        """
        service = self.server.services[0]
        try:
            service("NoSuchFunction")
            self.fail("An InvalidActionException should be raised.")
        except upnp.InvalidActionException:
            pass

    @async_test
    async def test_callaction_nonexisting_async(self):
        """
        When a non-existent action is called, an InvalidActionException should be raised.
        """
        service = self.server.services[0]
        try:
            await service("NoSuchFunction")
            self.fail("An InvalidActionException should be raised.")
        except upnp.InvalidActionException:
            pass

    @mock.patch("requests.post")
    def test_callaction_upnperror(self, mock_post):
        """
        UPNPErrors should be raised with the correct error code and description.
        """
        exc = requests.exceptions.HTTPError(500)
        exc.response = mock.Mock()
        exc.response.content = TEST_CALLACTION_UPNPERROR
        mock_post.side_effect = exc
        action = self.server.find_action("SetDefaultConnectionService")
        try:
            action(NewDefaultConnectionService="foo")
        except upnp.soap.SOAPError as exc:
            code, desc = exc.args
            self.assertEqual(code, 401)
            self.assertEqual(desc, "Invalid Action")

    @async_test
    async def test_callaction_upnperror_async(self):
        """
        UPNPErrors should be raised with the correct error code and description.
        """
        mock_resp.status = 500
        mock_resp.text = TEST_CALLACTION_UPNPERROR
        action = self.async_server.find_action("SetDefaultConnectionService")
        action.url = ASYNC_SERVER_ADDR
        try:
            await action(NewDefaultConnectionService="foo")
        except upnp.soap.SOAPError as exc:
            code, desc = exc.args
            self.assertEqual(code, 401)
            self.assertEqual(desc, "Invalid Action")

    @mock.patch("requests.Session.send", side_effect=EndPrematurelyException)
    def test_subscribe(self, mock_send):
        """
        Should perform a well formed HTTP SUBSCRIBE request.
        """
        cb_url = "http://127.0.0.1/"
        try:
            self.server.layer3f.subscribe(cb_url, timeout=123)
        except EndPrematurelyException:
            pass
        req = mock_send.call_args[0][0]
        self.assertEqual(req.method, "SUBSCRIBE")
        self.assertEqual(
            req.url, "http://127.0.0.1:%s/upnp/event/layer3f" % self.httpd_port
        )
        self.assertEqual(req.body, None)
        self.assertEqual(req.headers["NT"], "upnp:event")
        self.assertEqual(req.headers["CALLBACK"], "<%s>" % cb_url)
        self.assertEqual(req.headers["HOST"], "127.0.0.1:%s" % self.httpd_port)
        self.assertEqual(req.headers["TIMEOUT"], "Second-123")

    @async_test
    async def test_subscribe_async(self):
        """
        Should perform a well formed HTTP SUBSCRIBE request.
        """
        cb_url = "http://127.0.0.1:5005"
        self.async_server.layer3f._url_base = ASYNC_SERVER_ADDR
        try:
            await self.async_server.layer3f.async_subscribe(cb_url, timeout=123)
        except UnexpectedResponse:
            pass
        self.assertEqual(mock_req.method, "SUBSCRIBE")
        self.assertEqual(mock_req.body, None)
        self.assertEqual(mock_req.headers["NT"], "upnp:event")
        self.assertEqual(mock_req.headers["CALLBACK"], "<%s>" % cb_url)
        self.assertEqual(mock_req.headers["HOST"], ASYNC_HOST)
        self.assertEqual(mock_req.headers["TIMEOUT"], "Second-123")

    @mock.patch("requests.Session.send", side_effect=EndPrematurelyException)
    def test_renew_subscription(self, mock_send):
        """
        Should perform a well formed HTTP SUBSCRIBE request on sub renewal.
        """
        sid = "abcdef"
        try:
            self.server.layer3f.renew_subscription(sid, timeout=123)
        except EndPrematurelyException:
            pass
        req = mock_send.call_args[0][0]
        self.assertEqual(req.method, "SUBSCRIBE")
        self.assertEqual(
            req.url, "http://127.0.0.1:%s/upnp/event/layer3f" % self.httpd_port
        )
        self.assertEqual(req.body, None)
        self.assertEqual(req.headers["HOST"], "127.0.0.1:%s" % self.httpd_port)
        self.assertEqual(req.headers["SID"], sid)
        self.assertEqual(req.headers["TIMEOUT"], "Second-123")

    @async_test
    async def test_renew_subscription_async(self):
        """
        Should perform a well formed HTTP SUBSCRIBE request on sub renewal.
        """
        sid = "abcdef"
        self.async_server.layer3f._url_base = ASYNC_SERVER_ADDR
        try:
            await self.async_server.layer3f.async_renew_subscription(sid, timeout=123)
        except Exception:
            pass
        self.assertEqual(mock_req.method, "SUBSCRIBE")
        self.assertEqual(mock_req.body, None)
        self.assertEqual(mock_req.headers["HOST"], ASYNC_HOST)
        self.assertEqual(mock_req.headers["SID"], sid)
        self.assertEqual(mock_req.headers["TIMEOUT"], "Second-123")

    @mock.patch("requests.Session.send", side_effect=EndPrematurelyException)
    def test_cancel_subscription(self, mock_send):
        """
        Should perform a well formed HTTP UNSUBSCRIBE request on sub cancellation.
        """
        sid = "abcdef"
        try:
            self.server.layer3f.cancel_subscription(sid)
        except EndPrematurelyException:
            pass
        req = mock_send.call_args[0][0]
        self.assertEqual(req.method, "UNSUBSCRIBE")
        self.assertEqual(
            req.url, "http://127.0.0.1:%s/upnp/event/layer3f" % self.httpd_port
        )
        self.assertEqual(req.body, None)
        self.assertEqual(req.headers["HOST"], "127.0.0.1:%s" % self.httpd_port)
        self.assertEqual(req.headers["SID"], sid)

    @async_test
    async def test_cancel_subscription_async(self):
        """
        Should perform a well formed HTTP UNSUBSCRIBE request on sub cancellation.
        """
        sid = "abcdef"
        self.async_server.layer3f._url_base = ASYNC_SERVER_ADDR
        try:
            await self.async_server.layer3f.async_cancel_subscription(sid)
        except Exception:
            pass
        self.assertEqual(mock_req.method, "UNSUBSCRIBE")
        self.assertEqual(
            mock_req.url, "%s/upnp/event/layer3f" % ASYNC_SERVER_ADDR
        )
        self.assertEqual(mock_req.body, None)
        self.assertEqual(mock_req.headers["HOST"], ASYNC_HOST)
        self.assertEqual(mock_req.headers["SID"], sid)

    @mock.patch("requests.Session.send", side_effect=EndPrematurelyException)
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
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        args_in = list(alphabet)
        try:
            self.server.lanhcm.InArgsTest(**{x: "test" for x in args_in})
        except EndPrematurelyException:
            pass
        req = mock_send.call_args[0][0]
        tree = etree.fromstring(req.body)
        nsmap = tree.nsmap.copy()
        nsmap.update({"m": "urn:schemas-upnp-org:service:LANHostConfigManagement:1"})
        args = [
            x.tag
            for x in tree.xpath("SOAP-ENV:Body/m:InArgsTest", namespaces=nsmap)[
                0
            ].getchildren()
        ]
        self.assertEqual("".join(args), alphabet)

    @add_async_test
    def test_args_order_read_ok(self):
        """
        Make sure that the arguments in the XML are read in order by lxml.
        """
        xpath = (
            's:actionList/s:action/s:name[text()="InArgsTest"]'
            '/../s:argumentList/s:argument/s:name'
        )
        xml = self.server.service_map["lanhcm"].scpd_xml
        args = xml.xpath(xpath, namespaces={"s": xml.nsmap[None]})
        self.assertEqual("".join(x.text for x in args), "ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    # SOAP module tests - see upnpclient/soap.py ---------------------------------------------------

    @mock.patch("requests.post", side_effect=EndPrematurelyException)
    def test_call(self, mock_post):
        url = "http://www.example.com"
        soap = upnp.soap.SOAP(url, "test")
        self.assertRaises(EndPrematurelyException, soap.call, "TestAction")
        mock_post.assert_called()
        args, _ = mock_post.call_args
        call_url, body = args
        self.assertEqual(url, call_url)
        etree.fromstring(body)

    @async_test
    async def test_call_async(self):
        url = ASYNC_SERVER_ADDR
        soap = upnp.soap.SOAP(url, "test", session=self.session)
        with self.assertRaises(Exception):
            await soap.async_call("TestAction")
        self.assertEqual(ASYNC_HOST, mock_req.headers["Host"])

    @mock.patch("requests.post", side_effect=EndPrematurelyException)
    def test_call_with_auth(self, mock_post):
        url = "http://www.example.com"
        auth = ("myuser", "mypassword")
        soap = upnp.soap.SOAP(url, "test")
        self.assertRaises(
            EndPrematurelyException, soap.call, "TestAction", http_auth=auth
        )
        mock_post.assert_called()
        args, kwargs = mock_post.call_args
        call_url, body = args
        self.assertEqual(url, call_url)
        etree.fromstring(body)
        self.assertIn("auth", kwargs)
        self.assertEqual(kwargs["auth"], auth)

    @async_test
    async def test_call_with_auth_async(self):
        mock_resp.status = 400
        auth = ("myuser", "mypassword")
        soap = upnp.soap.SOAP(ASYNC_SERVER_ADDR, "test", session=self.session)
        with self.assertRaises(aiohttp.client_exceptions.ClientResponseError):
            await soap.async_call("TestAction", http_auth=auth)
        basic_auth_string = f"{auth[0]}:{auth[1]}"
        b64 = b64encode(basic_auth_string.encode("utf-8")).decode()
        self.assertEqual("Basic %s" % b64, mock_req.headers["Authorization"])

    @mock.patch("requests.post")
    def test_non_xml_error(self, mock_post):
        exc = requests.exceptions.HTTPError()
        exc.response = mock.Mock()
        exc.response.content = "this is not valid xml"
        mock_post.side_effect = exc
        soap = upnp.soap.SOAP("http://www.example.com", "test")
        self.assertRaises(requests.exceptions.HTTPError, soap.call, "TestAction")

    @async_test
    async def test_non_xml_error_async(self):
        mock_resp.status = 400
        mock_resp.text = "this is not valid xml"
        soap = upnp.soap.SOAP(ASYNC_SERVER_ADDR, "test", session=self.session)
        with self.assertRaises(aiohttp.client_exceptions.ClientResponseError):
            await soap.async_call("TestAction")

    @mock.patch("requests.post")
    def test_missing_error_code_element(self, mock_post):
        exc = requests.exceptions.HTTPError()
        exc.response = mock.Mock()
        exc.response.content = TEST_MISSING_ERROR_CODE_ELEMENT
        mock_post.side_effect = exc
        soap = upnp.soap.SOAP("http://www.example.com", "test")
        self.assertRaises(upnp.soap.SOAPProtocolError, soap.call, "TestAction")

    @async_test
    async def test_missing_error_code_element_async(self):
        mock_resp.status = 400
        mock_resp.text = TEST_MISSING_ERROR_CODE_ELEMENT
        soap = upnp.soap.SOAP(ASYNC_SERVER_ADDR, "test", session=self.session)
        with self.assertRaises(upnp.soap.SOAPProtocolError):
            await soap.async_call("TestAction")

    @mock.patch("requests.post")
    def test_missing_error_description_element(self, mock_post):
        exc = requests.exceptions.HTTPError()
        exc.response = mock.Mock()
        exc.response.content = TEST_MISSING_ERROR_DESCRIPTION_ELEMENT
        mock_post.side_effect = exc
        soap = upnp.soap.SOAP("http://www.example.com", "test")
        self.assertRaises(upnp.soap.SOAPProtocolError, soap.call, "TestAction")

    @async_test
    async def test_missing_error_description_element_async(self):
        mock_resp.status = 400
        mock_resp.text = TEST_MISSING_ERROR_DESCRIPTION_ELEMENT
        soap = upnp.soap.SOAP(ASYNC_SERVER_ADDR, "test", session=self.session)
        with self.assertRaises(upnp.soap.SOAPProtocolError):
            await soap.async_call("TestAction")

    @mock.patch("requests.post")
    def test_missing_response_element(self, mock_post):
        ret = mock.Mock()
        ret.content = TEST_MISSING_RESPONSE_ELEMENT
        mock_post.return_value = ret
        soap = upnp.soap.SOAP("http://www.example.com", "test")
        self.assertRaises(upnp.soap.SOAPProtocolError, soap.call, "TestAction")

    @async_test
    async def test_missing_response_element_async(self):
        mock_resp.status = 400
        mock_resp.text = TEST_MISSING_RESPONSE_ELEMENT
        soap = upnp.soap.SOAP(ASYNC_SERVER_ADDR, "test", session=self.session)
        with self.assertRaises(upnp.soap.SOAPProtocolError):
            await soap.async_call("TestAction")
