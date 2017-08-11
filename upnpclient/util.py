import logging


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
