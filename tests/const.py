LOCALHOST = "127.0.0.1"
HTTP_LOCALHOST = "http://%s" % LOCALHOST
ASYNC_SERVER_PORT = 8109
ASYNC_HOST = "%s:%r" % (LOCALHOST, ASYNC_SERVER_PORT)
ASYNC_SERVER_ADDR = "%s:%r" % (HTTP_LOCALHOST, ASYNC_SERVER_PORT)

TEST_CALLACTION_UPNPERROR = """
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

TEST_CALLACTION_PARAM_MASHAL_OUT_ASYNC = """
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
        <s:Body>
            <u:GetGenericPortMappingEntryResponse xmlns:u="urn:schemas-upnp-org:service:Layer3Forwarding:1">
                <NewInternalClient>10.0.0.1</NewInternalClient>
                <NewExternalPort>51773</NewExternalPort>
                <NewEnabled>true</NewEnabled>
            </u:GetGenericPortMappingEntryResponse>
        </s:Body>
    </s:Envelope>
""".strip()

TEST_DEVICE_AUTH = """
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
        <s:Body>
            <u:GetSubnetMaskResponse xmlns:u="urn:schemas-upnp-org:service:LANHostConfigManagement:1">
                <NewSubnetMask>255.255.255.0</NewSubnetMask>
            </u:GetSubnetMaskResponse>
        </s:Body>
    </s:Envelope>
""".strip()

TEST_CALLACTION_NOPARAM = """
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
        <s:Body>
            <u:GetAddressRangeResponse xmlns:u="urn:schemas-upnp-org:service:LANHostConfigManagement:1">
                <NewMinAddress>10.0.0.2</NewMinAddress>
                <NewMaxAddress>10.0.0.254</NewMaxAddress>
            </u:GetAddressRangeResponse>
        </s:Body>
    </s:Envelope>
"""

TEST_CALLACTION_PARAM = """
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

TEST_MISSING_ERROR_CODE_ELEMENT = """
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

TEST_MISSING_ERROR_DESCRIPTION_ELEMENT = """
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

TEST_MISSING_RESPONSE_ELEMENT = """
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
        <s:Body>
            <u:SomeOtherElement xmlns:u="urn:schemas-upnp-org:service:Layer3Forwarding:1">
                <NewEnabled>true</NewEnabled>
            </u:SomeOtherElement>
        </s:Body>
    </s:Envelope>
"""
