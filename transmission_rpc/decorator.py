# Copyright (c) 2018-2020 Trim21 <i@trim21.me>
# Licensed under the MIT license.

from typing import TYPE_CHECKING
from warnings import warn
from functools import wraps

from transmission_rpc.error import ServerVersionTooLow

if TYPE_CHECKING:
    from transmission_rpc.client import Client


def arg(kw: str, v: int):
    def wrapper(f):
        @wraps(f)
        def wrapped(self: 'Client', *args, **kwargs):
            if kw in kwargs:
                if self.rpc_version < v:
                    raise ServerVersionTooLow(
                        'argument `{}` require rpc version `{}`, but current server rpc version is {}'
                        .format(kw, v, self.rpc_version)
                    )
            return f(self, *args, **kwargs)

        return wrapped

    return wrapper


class ArgumentsReplacedWarning(DeprecationWarning):
    pass


def replaced_by(old_kw: str, new_kw: str, new_v: int):
    def wrapper(f):
        @wraps(f)
        def wrapped(self: 'Client', *args, **kwargs):
            if old_kw in kwargs:
                if self.rpc_version >= new_v:
                    warn(f'argument `{old_kw}` is replaced by `{new_kw}`', ArgumentsReplacedWarning)
            return f(self, *args, **kwargs)

        return wrapped

    return wrapper
