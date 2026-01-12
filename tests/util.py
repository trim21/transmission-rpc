import contextlib
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast

import pytest

# Define TypeVars for decorator typing
P = ParamSpec("P")
R = TypeVar("R")


def check_properties(cls: type, obj: Any) -> None:
    """
    Helper function to iterate over all public properties of a class and access them on an instance.
    This ensures that property getters are covered and don't raise unexpected exceptions.
    """
    for prop in dir(cls):
        # Skip private/protected properties
        if prop.startswith("_"):
            continue
        if isinstance(getattr(cls, prop), property):
            with contextlib.suppress(KeyError, DeprecationWarning):
                getattr(obj, prop)


class ServerTooLowError(Exception):
    """Raised when the Transmission server version is too low for a specific feature."""


def skip_on(exception: type[Exception], reason: str = "Default reason") -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to skip a test if a specific exception is raised.

    This is useful for skipping tests that require a newer version of the Transmission daemon
    than what is currently running.

    Args:
        exception: The exception class to check for.
        reason: The reason to display when the test is skipped.

    Returns:
        The decorated function.
    """

    def decorator_func(f: Callable[P, R]) -> Callable[P, R]:
        @wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                # Try to run the test
                return f(*args, **kwargs)
            except exception:
                # If exception of given type happens
                # just swallow it and raise pytest.Skip with given reason
                pytest.skip(reason)
                # Static analysis assistance; pytest.skip raises, but return type must match
                return cast("R", None)

        return wrapper

    return decorator_func
