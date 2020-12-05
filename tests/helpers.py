from functools import wraps


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
