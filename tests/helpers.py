from functools import wraps


class SimpleMock(dict):
    """Case insensitive dict to mock HTTP response."""
    def __init__(self, *args, **kwargs):
        super(SimpleMock, self).__init__(*args, **kwargs)
        for k in list(self.keys()):
            v = super(SimpleMock, self).pop(k)
            self.__setitem__(k, v)

    def __setitem__(self, key, value):
        super(SimpleMock, self).__setitem__(str(key).lower(), value)

    def __getitem__(self, key):
        if key.lower() not in self:
            return None
        return super(SimpleMock, self).__getitem__(key.lower())

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __getattr__(self, key):
        return self.__getitem__(key)


class SimpleMockRequest(SimpleMock):
    """Case insensitive dict interface for an aiohttp Request object."""
    def update(self, request):
        self.clear()
        attributes = [
            "method",
            "host",
            "path",
            "path_qs",
            "query",
            "body"
        ]
        self.headers = SimpleMock(request.headers)
        self.url = str(request.url)  # match requests interface
        self.url_object = request.url
        for attr in attributes:
            try:
                self[attr] = getattr(request, attr)
            except AttributeError:
                self[attr] = None


def async_test(f):
    """
    Decorator to create asyncio context for asyncio methods or functions.
    """
    @wraps(f)
    def g(*args, **kwargs):
        args[0].loop.run_until_complete(f(*args, **kwargs))
    return g


def add_async_test(f):
    """
    Test both the synchronous and async methods of the device (server).
    """
    @wraps(f)
    def g(*args, **kwargs):
        f(*args, **kwargs)  # run the original test
        async_args = [a for a in args]  # make mutable copy of args
        server = async_args[0].server  # save reference to self.server
        async_args[0].server = async_args[0].async_server  # set copy.server to async_server
        f(*async_args, **kwargs)  # run the test using the async instance
        async_args[0].server = server  # point self.server back to original
    return g
