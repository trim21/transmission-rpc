from typing import TYPE_CHECKING
from functools import wraps

from transmission_rpc.error import ServerVersionTooLow

if TYPE_CHECKING:
    from transmission_rpc.client import Client


def arg(kw: str, v: str):
    def wrapper(f):
        @wraps(f)
        def wrapped(self: 'Client', *args, **kwargs):
            if kw in kwargs:
                if self.rpc_version < v:
                    raise ServerVersionTooLow(
                        'arguments {} require rpc version {}, but current server rpc version is {}'
                        .format(kw, v, self.rpc_version)
                    )
            return f(self, *args, **kwargs)

        return wrapped

    return wrapper
