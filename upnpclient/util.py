import logging
from decimal import Decimal
from uuid import UUID
from base64 import b64decode

from dateutil.parser import parse as parse_date


def _getLogger(name):
    """
    Retrieve a logger instance. Checks if a handler is defined so we avoid the
    'No handlers could be found' message.
    """
    logger = logging.getLogger(name)
    if not logging.root.handlers:
        logger.disabled = 1
    return logger


def _XMLGetNodeText(node):
    """
    Return text contents of an XML node.
    """
    text = []
    for childNode in node.childNodes:
        if childNode.nodeType == node.TEXT_NODE:
            text.append(childNode.data)
    return ''.join(text)


def _XMLFindNodeText(node, tag_name):
    """
    Find the first XML node matching `tag_name` and return its text contents.
    If no node is found, return empty string. Use for non-required nodes.
    """
    target_nodes = node.getElementsByTagName(tag_name)
    try:
        return _XMLGetNodeText(target_nodes[0])
    except IndexError:
        return ''


def marshall_from(datatype, value):
    dt_conv = {
        'ui1': int,
        'ui2': int,
        'ui4': int,
        'i1': int,
        'i2': int,
        'i4': int,
        'int': int,
        'r4': Decimal,
        'r8': Decimal,
        'number': Decimal,
        'fixed.14.4': Decimal,
        'float': Decimal,
        'char': lambda x: x,
        'string': lambda x: x,
        'date': lambda x: parse_date(x).date(),
        'dateTime': parse_date,
        'dateTime.tz': parse_date,
        'time': lambda x: parse_date(x).time(),
        'time.tz': lambda x: parse_date(x).time(),
        'boolean': bool,
        'bin.base64': b64decode,
        'bin.hex': bytearray.fromhex,
        'uri': lambda x: x,
        'uuid': UUID,
    }
    return dt_conv[datatype](value)
