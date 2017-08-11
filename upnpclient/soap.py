import xml.dom.minidom

import requests

from .util import _getLogger, _XMLGetNodeText
from .const import HTTP_TIMEOUT

class SOAPError(Exception):
    pass


class SOAP(object):
    """SOAP (Simple Object Access Protocol) implementation
    This class defines a simple SOAP client.
    """
    def __init__(self, url, service_type):
        self.url = url
        self.service_type = service_type
        self._host = self.url.split('//', 1)[1].split('/', 1)[0] # Get hostname portion of url
        self._log = _getLogger('SOAP')


    def call(self, action_name, arg_in=None):
        if arg_in is None:
            arg_in = {}
        arg_values = '\n'.join( ['<%s>%s</%s>' % (k, v, k) for k, v in arg_in.items()] )
        body = \
            '<?xml version="1.0"?>\n' \
            '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n' \
            '  <SOAP-ENV:Body>\n' \
            '    <m:%(action_name)s xmlns:m="%(service_type)s">\n' \
            '      %(arg_values)s\n' \
            '    </m:%(action_name)s>\n' \
            '   </SOAP-ENV:Body>\n' \
            '</SOAP-ENV:Envelope>\n' % {
                'action_name': action_name,
                'service_type': self.service_type,
                'arg_values': arg_values,
            }
        headers = {
            'SOAPAction': '"%s#%s"' % (self.service_type, action_name),
            'Host': self._host,
            'Content-Type': 'text/xml',
            'Content-Length': str(len(body)),
        }

        # Uncomment this for debugging.
        # urllib2.install_opener(urllib2.build_opener(urllib2.HTTPHandler(debuglevel=1)))
        try:
            resp = requests.post(self.url, body, headers=headers, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            soap_error_xml = xml.dom.minidom.parseString(str(e))
            raise SOAPError(
                int(_XMLGetNodeText(soap_error_xml.getElementsByTagName('errorCode')[0])),
                _XMLGetNodeText(soap_error_xml.getElementsByTagName('errorDescription')[0]),
            )

        print(resp.text)
        raw_xml = resp.text.strip()
        contents = xml.dom.minidom.parseString(raw_xml)

        params_out = {}
        for node in contents.getElementsByTagName('*'):
            if node.localName.lower().endswith('response'):
                print(node)
                for param_out_node in node.childNodes:
                    if param_out_node.nodeType == param_out_node.ELEMENT_NODE:
                        print(param_out_node)
                        params_out[param_out_node.localName] = _XMLGetNodeText(param_out_node)

        print(params_out)
        return params_out
