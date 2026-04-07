from unittest.mock import patch, Mock

import pytest
import requests
from lxml import etree

import upnpclient


class EndPrematurelyException(Exception):
    pass


def test_call():
    url = "http://www.example.com"
    soap = upnpclient.soap.SOAP(url, "test")
    with patch("requests.post", side_effect=EndPrematurelyException) as mock_post:
        with pytest.raises(EndPrematurelyException):
            soap.call("TestAction")
        mock_post.assert_called()
        args, _ = mock_post.call_args
        call_url, body = args
        assert url == call_url
        etree.fromstring(body)  # Should not raise


def test_call_with_auth():
    url = "http://www.example.com"
    auth = ("myuser", "mypassword")
    soap = upnpclient.soap.SOAP(url, "test")
    with patch("requests.post", side_effect=EndPrematurelyException) as mock_post:
        with pytest.raises(EndPrematurelyException):
            soap.call("TestAction", http_auth=auth)
        mock_post.assert_called()
        args, kwargs = mock_post.call_args
        call_url, body = args
        assert url == call_url
        etree.fromstring(body)  # Should not raise
        assert "auth" in kwargs
        assert kwargs["auth"] == auth


def test_non_xml_error():
    exc = requests.exceptions.HTTPError()
    exc.response = Mock()
    exc.response.content = "this is not valid xml"
    with patch("requests.post", side_effect=exc):
        soap = upnpclient.soap.SOAP("http://www.example.com", "test")
        with pytest.raises(requests.exceptions.HTTPError):
            soap.call("TestAction")


def test_missing_error_code_element():
    exc = requests.exceptions.HTTPError()
    exc.response = Mock()
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
    with patch("requests.post", side_effect=exc):
        soap = upnpclient.soap.SOAP("http://www.example.com", "test")
        with pytest.raises(upnpclient.soap.SOAPProtocolError):
            soap.call("TestAction")


def test_missing_error_description_element():
    exc = requests.exceptions.HTTPError()
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
            </UPnPError>
          </detail>
        </s:Fault>
      </s:Body>
    </s:Envelope>
    """.strip()
    with patch("requests.post", side_effect=exc):
        soap = upnpclient.soap.SOAP("http://www.example.com", "test")
        with pytest.raises(upnpclient.soap.SOAPProtocolError):
            soap.call("TestAction")


def test_missing_response_element():
    ret = Mock()
    ret.content = """
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
       <s:Body>
          <u:SomeOtherElement xmlns:u="urn:schemas-upnp-org:service:Layer3Forwarding:1">
             <NewEnabled>true</NewEnabled>
          </u:SomeOtherElement>
       </s:Body>
    </s:Envelope>
    """
    with patch("requests.post", return_value=ret):
        soap = upnpclient.soap.SOAP("http://www.example.com", "test")
        with pytest.raises(upnpclient.soap.SOAPProtocolError):
            soap.call("TestAction")
