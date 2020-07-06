# Copyright (c) 2018-2020 Trim21 <i@trim21.me>
# Licensed under the MIT license.
from typing import TYPE_CHECKING, Any, TypeVar, Callable, cast
from warnings import warn
from functools import wraps

from transmission_rpc.error import ServerVersionTooLow

if TYPE_CHECKING:
    from transmission_rpc.client import Client

T = TypeVar('T', bound=Callable[..., Any])


def kwarg(kw: str, v: int) -> Callable[[T], T]:
    def wrapper(f: T) -> T:
        @wraps(f)
        def wrapped(self: 'Client', *args, **kwargs):  # type: ignore
            if kw in kwargs:
                if self.rpc_version < v:
                    raise ServerVersionTooLow(
                        'argument `{}` require rpc version `{}`, but current server rpc version is {}'
                        .format(kw, v, self.rpc_version)
                    )
            return f(self, *args, **kwargs)

        return cast(T, wrapped)

    return wrapper


class ArgumentsReplacedWarning(DeprecationWarning):
    pass


def replaced_by(old_kw: str, new_kw: str, new_v: int) -> Callable[[T], T]:
    def wrapper(f: T) -> T:
        @wraps(f)
        def wrapped(self: 'Client', *args, **kwargs):  # type: ignore

            if old_kw in kwargs:
                if self.rpc_version >= new_v:
                    warn(f'argument `{old_kw}` is replaced by `{new_kw}`', ArgumentsReplacedWarning)
            return f(self, *args, **kwargs)

        return cast(T, wrapped)

    return wrapper
