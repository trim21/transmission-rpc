from __future__ import annotations

from typing import Any, NamedTuple, Optional, TypeVar, Union

from transmission_rpc.constants import Priority

_Number = Union[int, float]
_Timeout = Optional[_Number | tuple[_Number, _Number]]

T = TypeVar("T")


class Container:
    fields: dict[str, Any]  #: raw response data

    def __init__(self, *, fields: dict[str, Any]):
        self.fields = fields

    def get(self, key: str, default: T | None = None) -> Any:
        """Get the raw value by the **raw rpc response key**"""
        return self.fields.get(key, default)


class File(NamedTuple):
    name: str
    """file name"""
    size: int
    """file size in bytes"""

    completed: int
    """bytes completed"""

    priority: Priority
    """download priority"""

    selected: bool
    """if selected for download"""

    id: int
    """id of the file of this torrent, not should not be used outside the torrent scope"""


class Group(Container):
    """https://github.com/transmission/transmission/blob/4.0.5/docs/rpc-spec.md#482-bandwidth-group-accessor-group-get"""

    @property
    def name(self) -> str:
        """Bandwidth group name"""
        return self.fields["name"]

    @property
    def honors_session_limits(self) -> bool:
        """True if session upload limits are honored"""
        return self.fields["honorsSessionLimits"]

    @property
    def speed_limit_down_enabled(self) -> bool:
        """True means enabled"""
        return self.fields["speed-limit-down-enabled"]

    @property
    def speed_limit_down(self) -> int:
        """Max global download speed (KBps)"""
        return self.fields["speed-limit-down"]

    @property
    def speed_limit_up_enabled(self) -> bool:
        """True means enabled"""
        return self.fields["speed-limit-up-enabled"]

    @property
    def speed_limit_up(self) -> int:
        """Max global upload speed (KBps)"""
        return self.fields["speed-limit-up"]


class BitMap:
    __value: bytes
    __slots__ = ("__value",)

    def __init__(self, b: bytes):
        self.__value = b

    def get(self, index: int) -> bool:
        return (self.__value[index // 8] & (1 << (8 - index & 8))) != 0
