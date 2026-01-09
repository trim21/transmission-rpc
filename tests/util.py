from functools import wraps

import pytest


class ServerTooLowError(Exception):
    """Raised when the Transmission server version is too low for a specific feature."""


def skip_on(exception, reason="Default reason"):
    """
    Decorator to skip a test if a specific exception is raised.

    This is useful for skipping tests that require a newer version of the Transmission daemon
    than what is currently running.

    Args:
        exception: The exception class to check for.
        reason: The reason to display when the test is skipped.
    """

    # Func below is the real decorator and will receive the test function as param
    def decorator_func(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Try to run the test
                return f(*args, **kwargs)
            except exception:
                # If exception of given type happens
                # just swallow it and raise pytest.Skip with given reason
                pytest.skip(reason)

        return wrapper

    return decorator_func
