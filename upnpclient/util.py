import logging


def _getLogger(name):
    """
    Retrieve a logger instance. Checks if a handler is defined so we avoid the
    'No handlers could be found' message.
    """
    logger = logging.getLogger(name)
    # if not logging.root.handlers:
    #     logger.disabled = 1
    return logger
