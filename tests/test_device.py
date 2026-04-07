"""Device-related tests converted from unittest to pytest style."""

from unittest.mock import Mock, patch

import pytest
import requests
from lxml import etree

import upnpclient


class EndPrematurelyException(Exception):
    pass


SOAP_RESPONSE_SUBNET = """
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
   <s:Body>
      <u:GetSubnetMaskResponse xmlns:u="urn:schemas-upnp-org:service:LANHostConfigManagement:1">
         <NewSubnetMask>255.255.255.0</NewSubnetMask>
      </u:GetSubnetMaskResponse>
   </s:Body>
</s:Envelope>
"""


def _mock_post_subnet():
    ret = Mock()
    ret.content = SOAP_RESPONSE_SUBNET
    return ret


# -- Auth tests --


def test_device_auth(httpd):
    auth = ("myuser", "mypassword")
    device = upnpclient.Device(
        f"http://127.0.0.1:{httpd}/igd/device.xml", http_auth=auth
    )
    with patch("requests.post", return_value=_mock_post_subnet()) as mock_post:
        device("GetSubnetMask")
        _, kwargs = mock_post.call_args
        assert "auth" in kwargs
        assert kwargs["auth"] == auth


def test_device_auth_call_override(httpd):
    dev_auth = ("devuser", "devpassword")
    call_auth = ("calluser", "callpassword")
    device = upnpclient.Device(
        f"http://127.0.0.1:{httpd}/igd/device.xml", http_auth=dev_auth
    )
    with patch("requests.post", return_value=_mock_post_subnet()) as mock_post:
        device("GetSubnetMask", http_auth=call_auth)
        _, kwargs = mock_post.call_args
        assert "auth" in kwargs
        assert kwargs["auth"] == call_auth


def test_device_auth_call_override_none(httpd):
    dev_auth = ("devuser", "devpassword")
    device = upnpclient.Device(
        f"http://127.0.0.1:{httpd}/igd/device.xml", http_auth=dev_auth
    )
    with patch("requests.post", return_value=_mock_post_subnet()) as mock_post:
        device("GetSubnetMask", http_auth=None)
        _, kwargs = mock_post.call_args
        assert "auth" in kwargs
        assert kwargs["auth"] == dev_auth


def test_device_auth_none_override(httpd):
    call_auth = ("calluser", "callpassword")
    device = upnpclient.Device(
        f"http://127.0.0.1:{httpd}/igd/device.xml", http_auth=None
    )
    with patch("requests.post", return_value=_mock_post_subnet()) as mock_post:
        device("GetSubnetMask", http_auth=call_auth)
        _, kwargs = mock_post.call_args
        assert "auth" in kwargs
        assert kwargs["auth"] == call_auth


# -- Headers tests --


def test_device_headers(httpd):
    headers = dict(test="device")
    device = upnpclient.Device(
        f"http://127.0.0.1:{httpd}/igd/device.xml", http_headers=headers
    )
    with patch("requests.post", return_value=_mock_post_subnet()) as mock_post:
        device("GetSubnetMask")
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["test"] == "device"


def test_device_headers_call_override(httpd):
    dev_headers = dict(test="device")
    call_headers = dict(test="call")
    device = upnpclient.Device(
        f"http://127.0.0.1:{httpd}/igd/device.xml", http_headers=dev_headers
    )
    with patch("requests.post", return_value=_mock_post_subnet()) as mock_post:
        device("GetSubnetMask", http_headers=call_headers)
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["test"] == "call"


def test_device_headers_call_override_none(httpd):
    dev_headers = dict(test="device")
    device = upnpclient.Device(
        f"http://127.0.0.1:{httpd}/igd/device.xml", http_headers=dev_headers
    )
    with patch("requests.post", return_value=_mock_post_subnet()) as mock_post:
        device("GetSubnetMask", http_headers=None)
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["test"] == "device"


def test_device_headers_none_override(httpd):
    call_headers = dict(test="call")
    device = upnpclient.Device(
        f"http://127.0.0.1:{httpd}/igd/device.xml", http_headers=None
    )
    with patch("requests.post", return_value=_mock_post_subnet()) as mock_post:
        device("GetSubnetMask", http_headers=call_headers)
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["test"] == "call"


# -- Device property tests --


def test_device_props(igd_device):
    assert igd_device.device_type == "urn:schemas-upnp-org:device:InternetGatewayDevice:1"
    assert igd_device.friendly_name == "SpeedTouch 5x6 (0320FJ2PZ)"
    assert igd_device.manufacturer == "Pannaway"
    assert igd_device.model_description == "DSL Internet Gateway Device"
    assert igd_device.model_name == "Pannaway"
    assert igd_device.model_number == "RG-210"
    assert igd_device.serial_number == "0320FJ2PZ"


def test_device_malformed_namespace(igd_malformed_ns_device):
    assert igd_malformed_ns_device.device_type == "urn:schemas-upnp-org:device:MediaRenderer:1"
    assert igd_malformed_ns_device.friendly_name == "Marantz SR5008"
    assert igd_malformed_ns_device.manufacturer == "Marantz"


def test_device_nonexists(httpd):
    with pytest.raises(requests.exceptions.HTTPError):
        upnpclient.Device(f"http://127.0.0.1:{httpd}/igd/DOESNOTEXIST.xml")


# -- Service tests --


def test_services(igd_device):
    service_ids = [service.service_id for service in igd_device.services]
    assert "urn:upnp-org:serviceId:layer3f" in service_ids
    assert "urn:upnp-org:serviceId:lanhcm" in service_ids
    assert "urn:upnp-org:serviceId:wancic" in service_ids


def test_actions(igd_device):
    action_names = set()
    for service in igd_device.services:
        for action in service.actions:
            action_names.add(action.name)
    assert "SetDefaultConnectionService" in action_names
    assert "GetCommonLinkProperties" in action_names
    assert "GetDNSServers" in action_names
    assert "GetDHCPRelay" in action_names


# -- Find action tests --


def test_findaction_server(igd_device):
    action = igd_device.find_action("GetSubnetMask")
    assert isinstance(action, upnpclient.Action)
    assert action.name == "GetSubnetMask"


def test_findaction_server_nonexists(igd_device):
    action = igd_device.find_action("GetNoneExistingAction")
    assert action is None


def test_findaction_service_nonexists(igd_device):
    action = igd_device.find_action("GetNoneExistingAction")
    assert action is None


# -- Call action tests --


def test_callaction_server(igd_device):
    with patch("requests.post", return_value=_mock_post_subnet()):
        ret = igd_device("GetSubnetMask")
        assert ret == dict(NewSubnetMask="255.255.255.0")


def test_callaction_noparam(igd_device):
    ret = Mock()
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
    with patch("requests.post", return_value=ret):
        action = igd_device.find_action("GetAddressRange")
        assert isinstance(action, upnpclient.Action)
        response = action()
        assert isinstance(response, dict)
        assert response["NewMinAddress"] == "10.0.0.2"
        assert response["NewMaxAddress"] == "10.0.0.254"


def test_callaction_param(igd_device):
    ret = Mock()
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
    with patch("requests.post", return_value=ret):
        action = igd_device.find_action("GetGenericPortMappingEntry")
        response = action(NewPortMappingIndex=0)
        assert response["NewInternalClient"] == "10.0.0.1"
        assert response["NewExternalPort"] == 51773
        assert response["NewEnabled"] is True


def test_callaction_param_missing(igd_device):
    action = igd_device.find_action("GetGenericPortMappingEntry")
    with pytest.raises(upnpclient.UPNPError):
        action()


def test_callaction_param_invalid_ui2(igd_device):
    action = igd_device.find_action("GetGenericPortMappingEntry")
    with pytest.raises(upnpclient.ValidationError):
        action(NewPortMappingIndex="ZERO")


def test_callaction_param_mashal_out(igd_device):
    ret = Mock()
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
    with patch("requests.post", return_value=ret):
        action = igd_device.find_action("GetGenericPortMappingEntry")
        response = action(NewPortMappingIndex=0)
        assert isinstance(response["NewInternalClient"], str)
        assert isinstance(response["NewExternalPort"], int)
        assert isinstance(response["NewEnabled"], bool)


def test_callaction_nonexisting(igd_device):
    service = igd_device.services[0]
    with pytest.raises(upnpclient.InvalidActionException):
        service("NoSuchFunction")


def test_callaction_upnperror(igd_device):
    exc = requests.exceptions.HTTPError(500)
    exc.response = Mock()
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
    with patch("requests.post", side_effect=exc):
        action = igd_device.find_action("SetDefaultConnectionService")
        try:
            action(NewDefaultConnectionService="foo")
        except upnpclient.soap.SOAPError as soap_exc:
            code, desc = soap_exc.args
            assert code == 401
            assert desc == "Invalid Action"


# -- Subscription tests --


def test_subscribe(igd_device, httpd):
    cb_url = "http://127.0.0.1/"
    with patch("requests.Session.send", side_effect=EndPrematurelyException) as mock_send:
        try:
            igd_device.layer3f.subscribe(cb_url, timeout=123)
        except EndPrematurelyException:
            pass
        req = mock_send.call_args[0][0]
        assert req.method == "SUBSCRIBE"
        assert req.url == f"http://127.0.0.1:{httpd}/upnp/event/layer3f"
        assert req.body is None
        assert req.headers["NT"] == "upnp:event"
        assert req.headers["CALLBACK"] == f"<{cb_url}>"
        assert req.headers["HOST"] == f"127.0.0.1:{httpd}"
        assert req.headers["TIMEOUT"] == "Second-123"


def test_renew_subscription(igd_device, httpd):
    sid = "abcdef"
    with patch("requests.Session.send", side_effect=EndPrematurelyException) as mock_send:
        try:
            igd_device.layer3f.renew_subscription(sid, timeout=123)
        except EndPrematurelyException:
            pass
        req = mock_send.call_args[0][0]
        assert req.method == "SUBSCRIBE"
        assert req.url == f"http://127.0.0.1:{httpd}/upnp/event/layer3f"
        assert req.body is None
        assert req.headers["HOST"] == f"127.0.0.1:{httpd}"
        assert req.headers["SID"] == sid
        assert req.headers["TIMEOUT"] == "Second-123"


def test_cancel_subscription(igd_device, httpd):
    sid = "abcdef"
    with patch("requests.Session.send", side_effect=EndPrematurelyException) as mock_send:
        try:
            igd_device.layer3f.cancel_subscription(sid)
        except EndPrematurelyException:
            pass
        req = mock_send.call_args[0][0]
        assert req.method == "UNSUBSCRIBE"
        assert req.url == f"http://127.0.0.1:{httpd}/upnp/event/layer3f"
        assert req.body is None
        assert req.headers["HOST"] == f"127.0.0.1:{httpd}"
        assert req.headers["SID"] == sid


# -- Argument ordering tests --


def test_args_order(igd_device):
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    with patch("requests.Session.send", side_effect=EndPrematurelyException) as mock_send:
        try:
            igd_device.lanhcm.InArgsTest(**{x: "test" for x in alphabet})
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
        assert "".join(args) == alphabet


def test_args_order_read_ok(igd_device):
    xpath = 's:actionList/s:action/s:name[text()="InArgsTest"]/../s:argumentList/s:argument/s:name'
    xml = igd_device.service_map["lanhcm"].scpd_xml
    args = xml.xpath(xpath, namespaces={"s": xml.nsmap[None]})
    assert "".join(x.text for x in args) == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# -- New fixture-based tests --


def test_marantz_device_props(marantz_device):
    assert marantz_device.friendly_name == "Marantz SR5008"
    assert marantz_device.manufacturer == "Marantz"
    assert marantz_device.device_type == "urn:schemas-upnp-org:device:MediaRenderer:1"


def test_marantz_services(marantz_device):
    service_ids = [s.service_id for s in marantz_device.services]
    assert "urn:upnp-org:serviceId:RenderingControl" in service_ids
    assert "urn:upnp-org:serviceId:ConnectionManager" in service_ids
    assert "urn:upnp-org:serviceId:AVTransport" in service_ids


def test_media_renderer_device_props(media_renderer_device):
    assert media_renderer_device.friendly_name == "Test Media Renderer"
    assert media_renderer_device.manufacturer == "Test Manufacturer"
    assert media_renderer_device.device_type == "urn:schemas-upnp-org:device:MediaRenderer:1"


def test_media_renderer_services(media_renderer_device):
    service_ids = [s.service_id for s in media_renderer_device.services]
    assert "urn:upnp-org:serviceId:RenderingControl" in service_ids
    assert "urn:upnp-org:serviceId:ConnectionManager" in service_ids
    assert "urn:upnp-org:serviceId:AVTransport" in service_ids


def test_chromecast_scpd_404(httpd):
    with pytest.raises(requests.exceptions.HTTPError):
        upnpclient.Device(f"http://127.0.0.1:{httpd}/chromecast/device.xml")


def test_roku_scpd_missing(httpd):
    with pytest.raises(requests.exceptions.HTTPError):
        upnpclient.Device(f"http://127.0.0.1:{httpd}/roku/device.xml")
