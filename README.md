[![CI](https://github.com/flyte/upnpclient/actions/workflows/ci.yml/badge.svg)](https://github.com/flyte/upnpclient/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/upnpclient)](https://pypi.org/project/upnpclient/)
[![Python](https://img.shields.io/pypi/pyversions/upnpclient)](https://pypi.org/project/upnpclient/)
[![License](https://img.shields.io/pypi/l/upnpclient)](https://github.com/flyte/upnpclient/blob/develop/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/upnpclient)](https://pypi.org/project/upnpclient/)

uPnPclient
============

_uPnP client library for Python 3._

This library can be used to discover and consume uPnP devices and their services.

It's originally based on [Ferry Boender's work](https://github.com/fboender/pyupnpclient) and his blog post entitled [Exploring UPnP with Python](https://www.electricmonk.nl/log/2016/07/05/exploring-upnp-with-python/).

### Requirements

Python 3.9+

### Installation

```bash
pip install upnpclient
```

### Usage

#### Discovering devices

```python
>>> import upnpclient
>>> devices = upnpclient.discover()
>>> devices
[<Device 'OpenWRT router'>,
 <Device 'Harmony Hub'>,
 <Device 'walternate: root'>]
```

If you already know the URL for a device's description XML, you can create it directly:

```python
>>> d = upnpclient.Device("http://192.168.1.1:5000/rootDesc.xml")
```

#### Listing services and actions

Each device exposes different services depending on what it is. Check what's available:

```python
>>> d.services
[<Service service_id='urn:upnp-org:serviceId:Layer3Forwarding1'>,
 <Service service_id='urn:upnp-org:serviceId:WANCommonIFC1'>,
 <Service service_id='urn:upnp-org:serviceId:WANIPConn1'>]
```

Services are accessed by the last part of their `service_id`. For example, `urn:upnp-org:serviceId:WANIPConn1` becomes `d.WANIPConn1`:

```python
>>> d.WANIPConn1.actions
[<Action 'GetStatusInfo'>,
 <Action 'GetNATRSIPStatus'>,
 <Action 'GetExternalIPAddress'>,
 <Action 'AddPortMapping'>,
 ...]
```

If the service name isn't a valid Python attribute, use dictionary-style access:

```python
>>> d["WANIPConn1"]["GetStatusInfo"]()
```

#### Calling actions

```python
>>> d.WANIPConn1.GetStatusInfo()
{'NewConnectionStatus': 'Connected',
 'NewLastConnectionError': 'ERROR_NONE',
 'NewUptime': 14851479}

>>> d.WANIPConn1.GetExternalIPAddress()
{'NewExternalIPAddress': '123.123.123.123'}
```

#### Inspecting action arguments

To see what arguments an action expects:

```python
>>> d.WANIPConn1.AddPortMapping.argsdef_in
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

Then call it with those arguments:

```python
>>> d.WANIPConn1.AddPortMapping(
...     NewRemoteHost='0.0.0.0',
...     NewExternalPort=12345,
...     NewProtocol='TCP',
...     NewInternalPort=12345,
...     NewInternalClient='192.168.1.10',
...     NewEnabled='1',
...     NewPortMappingDescription='Testing',
...     NewLeaseDuration=10000)
{}
```

Similarly, `argsdef_out` shows what an action returns:

```python
>>> d.WANIPConn1.GetStatusInfo.argsdef_out
[('NewConnectionStatus',
  {'allowed_values': {'Connected', 'Disconnected', 'Connecting'},
   'datatype': 'string',
   'name': 'ConnectionStatus'}),
 ('NewLastConnectionError',
  {'allowed_values': set(),
   'datatype': 'string',
   'name': 'LastConnectionError'}),
 ('NewUptime',
  {'allowed_values': set(), 'datatype': 'ui4', 'name': 'Uptime'})]
```

#### HTTP Auth/Headers

You may pass a
[requests compatible](https://docs.python-requests.org/en/latest/user/authentication/)
authentication object and/or a dictionary containing headers to use on the HTTP
calls to your uPnP device.

These may be set on the `Device` itself on creation for use with every HTTP
call:

```python
device = upnpclient.Device(
    "http://192.168.1.1:5000/rootDesc.xml",
    http_auth=('myusername', 'mypassword'),
    http_headers={'Some-Required-Header': 'somevalue'},
)
```

Or on a per-call basis:

```python
device.Layer3Forwarding1.GetDefaultConnectionService(
    http_auth=('myusername', 'mypassword'),
    http_headers={'Some-Required-Header': 'somevalue'},
)
```

If you've set either at `Device` level, they can be overridden per-call by
setting them to `None`.
