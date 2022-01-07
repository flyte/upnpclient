[![Build Status](https://travis-ci.org/flyte/upnpclient.svg?branch=develop)](https://travis-ci.org/flyte/upnpclient)

uPnPclient
============

_uPnP client library for Python 3._

This library can be used to discover and consume uPnP devices and their services.

It's originally based on [Ferry Boender's work](https://github.com/fboender/pyupnpclient) and his blog post entitled [Exploring UPnP with Python](https://www.electricmonk.nl/log/2016/07/05/exploring-upnp-with-python/).

### Installation

```bash
pip install upnpclient
```

### Usage

Typical usage:

```python
In [1]: import upnpclient

In [2]: devices = upnpclient.discover()

In [3]: devices
Out[3]: 
[<Device 'OpenWRT router'>,
 <Device 'Harmony Hub'>,
 <Device 'walternate: root'>]

In [4]: d = devices[0]

In [5]: d.WANIPConn1.GetStatusInfo()
Out[5]: 
{'NewConnectionStatus': 'Connected',
 'NewLastConnectionError': 'ERROR_NONE',
 'NewUptime': 14851479}

In [6]: d.WANIPConn1.GetNATRSIPStatus()
Out[6]: {'NewNATEnabled': True, 'NewRSIPAvailable': False}

In [7]: d.WANIPConn1.GetExternalIPAddress()
Out[7]: {'NewExternalIPAddress': '123.123.123.123'}
```

If you know the URL for the device description XML, you can access it directly.

```python
In [1]: import upnpclient

In [2]: d = upnpclient.Device("http://192.168.1.1:5000/rootDesc.xml")

In [3]: d.services
Out[3]: 
[<Service service_id='urn:upnp-org:serviceId:Layer3Forwarding1'>,
 <Service service_id='urn:upnp-org:serviceId:WANCommonIFC1'>,
 <Service service_id='urn:upnp-org:serviceId:WANIPConn1'>]

In [4]: d.Layer3Forwarding1.actions
Out[4]: 
[<Action 'SetDefaultConnectionService'>,
 <Action 'GetDefaultConnectionService'>]

In [5]: d.Layer3Forwarding1.GetDefaultConnectionService()
Out[5]: {'NewDefaultConnectionService': 'uuid:46cb370a-d7f2-490f-ac01-fb0db6c8b22b:WANConnectionDevice:1,urn:upnp-org:serviceId:WANIPConn1'}
```

Sometimes the service or action name isn't a valid property name. In which case, service and actions can be accessed other ways:

```python
In [1]: d["Layer3Forwarding1"]["GetDefaultConnectionService"]()
Out[1]: {'NewDefaultConnectionService': 'uuid:46cb370a-d7f2-490f-ac01-fb0db6c8b22b:WANConnectionDevice:1,urn:upnp-org:serviceId:WANIPConn1'}
```

To view the arguments required to call a given action:

```python
In [1]: d.WANIPConn1.AddPortMapping.argsdef_in
Out[1]: 
[('NewRemoteHost',
  {'allowed_values': set(), 'datatype': 'string', 'name': 'RemoteHost'}),
 ('NewExternalPort',
  {'allowed_values': set(), 'datatype': 'ui2', 'name': 'ExternalPort'}),
 ('NewProtocol',
  {'allowed_values': {'TCP', 'UDP'},
   'datatype': 'string',
   'name': 'PortMappingProtocol'}),
 ('NewInternalPort',
  {'allowed_values': set(), 'datatype': 'ui2', 'name': 'InternalPort'}),
 ('NewInternalClient',
  {'allowed_values': set(), 'datatype': 'string', 'name': 'InternalClient'}),
 ('NewEnabled',
  {'allowed_values': set(),
   'datatype': 'boolean',
   'name': 'PortMappingEnabled'}),
 ('NewPortMappingDescription',
  {'allowed_values': set(),
   'datatype': 'string',
   'name': 'PortMappingDescription'}),
 ('NewLeaseDuration',
  {'allowed_values': set(),
   'datatype': 'ui4',
   'name': 'PortMappingLeaseDuration'})]
```

and then to call the action using those arguments:

```python
In [1]: d.WANIPConn1.AddPortMapping(
   ...:     NewRemoteHost='0.0.0.0',
   ...:     NewExternalPort=12345,
   ...:     NewProtocol='TCP',
   ...:     NewInternalPort=12345,
   ...:     NewInternalClient='192.168.1.10',
   ...:     NewEnabled='1',
   ...:     NewPortMappingDescription='Testing',
   ...:     NewLeaseDuration=10000)
Out[1]: {}
```

Similarly, the arguments you can expect to receive in response are listed:

```python
In [1]: d.WANIPConn1.GetGenericPortMappingEntry.argsdef_out
Out[1]: 
[('NewRemoteHost',
  {'allowed_values': set(), 'datatype': 'string', 'name': 'RemoteHost'}),
 ('NewExternalPort',
  {'allowed_values': set(), 'datatype': 'ui2', 'name': 'ExternalPort'}),
 ('NewProtocol',
  {'allowed_values': {'TCP', 'UDP'},
   'datatype': 'string',
   'name': 'PortMappingProtocol'}),
 ('NewInternalPort',
  {'allowed_values': set(), 'datatype': 'ui2', 'name': 'InternalPort'}),
 ('NewInternalClient',
  {'allowed_values': set(), 'datatype': 'string', 'name': 'InternalClient'}),
 ('NewEnabled',
  {'allowed_values': set(),
   'datatype': 'boolean',
   'name': 'PortMappingEnabled'}),
 ('NewPortMappingDescription',
  {'allowed_values': set(),
   'datatype': 'string',
   'name': 'PortMappingDescription'}),
 ('NewLeaseDuration',
  {'allowed_values': set(),
   'datatype': 'ui4',
   'name': 'PortMappingLeaseDuration'})]
```

#### HTTP Auth/Headers

You may pass a
[requests compatible](http://docs.python-requests.org/en/master/user/authentication/)
authentication object and/or a dictionary containing headers to use on the HTTP
calls to your uPnP device.

These may be set on the `Device` itself on creation for use with every HTTP
call:

```python
device = upnpclient.Device(
    "http://192.168.1.1:5000/rootDesc.xml"
    http_auth=('myusername', 'mypassword'),
    http_headers={'Some-Required-Header': 'somevalue'}
)
```

Or on a per-call basis:

```python
device.Layer3Forwarding1.GetDefaultConnectionService(
    http_auth=('myusername', 'mypassword'),
    http_headers={'Some-Required-Header': 'somevalue'}
)
```

If you've set either at `Device` level, they can be overridden per-call by
setting them to `None`.


#### HTTPS Certificate

UPnP DeviceProtection:1 Standardized secured SSL connection to Devices (server):
[UPnP-gw-DeviceProtection-V1-Service](http://upnp.org/specs/gw/UPnP-gw-DeviceProtection-V1-Service.pdf)

From §1.1.2: `Devices and Control Points will generate their own CA certificates`.

This means two things:
- your control-point (client) must accept Device (server) certificate, which might not be signed by trusted autorithy - eg self-signed.
- your control-point (client) must provide a certificate to the Device (server), wich also can be self-signed.

In order to do that, two paramters have been added to kwargs:
- `AllowSelfSignedSSL`: a boolean allowing upnpclient to connect to not-trusted devices
- `cert`: to allow user-provided certificate to be used for connection

```python
mycert = ("C:\\fooo.crt", "C:\\fooo.key")
device = upnpclient.Device(
    "https://192.168.1.1:5000/rootDesc.xml",
    AllowSelfSignedSSL = True,
	cert = mycert,
)
```

Or

```python
devices = upnpclient.discover(AllowSelfSignedSSL=True,AllowSelfSignedSSL = True,cert = mycert)
```

Note: At the moment, upnpclient will not try to access the SSL URL in discover mode (described in §2.3.1 as `SECURELOCATION.UPNP.ORG` header extension)


#### Custom SSDP inbound port 

SSDP protocol is not well supported by firewalls (like netfilter/conntrack) so if you run this control-point client on a critical device, you may have problems setting filter rules.

Main problem is the defaut SSDP behavior which use random inbound UDP port to receive SSDP responses.

To address that problem, we add a workaround option that let you fix this udp input port:

```python
device = upnpclient.Device(
    "https://192.168.1.1:5000/rootDesc.xml",
	SSDPInPort=20000
)
```

Or

```python
devices = upnpclient.discover(AllowSelfSignedSSL=True,SSDPInPort=30000)
```

Then you can allow this path in your firewall configuration.

Example for iptables:

```iptables -A INPUT [-i <<control-point input interface>>] -d <<control-point ip address>>  -p udp --dport <<control-point fixed ssdp input port>> -j ACCEPT```