from __future__ import annotations

from typing import Any, NamedTuple

from transmission_rpc._compat import field_names, to_snake
from transmission_rpc.constants import Priority

_MISSING = object()


def get_field(fields: dict[str, Any], key: str, default: Any = _MISSING) -> Any:
    """Read a canonical snake_case field, falling back to legacy RPC names."""
    for candidate in field_names(key):
        if candidate in fields:
            return fields[candidate]
    if default is _MISSING:
        raise KeyError(key)
    return default


class Container:
    fields: dict[str, Any]  #: raw response data (snake_case when using JSON-RPC 2.0)
    __slots__ = ("fields",)

    def __init__(self, *, fields: dict[str, Any]):
        self.fields = fields

    def _get_field(self, key: str) -> Any:
        """Look up a snake_case field, falling back to its legacy variants.

        Raises KeyError when the field is missing in either form.
        """
        return get_field(self.fields, key)

    def get(self, key: str, default: Any | None = None) -> Any:
        """get the raw value, accepting both the JSON-RPC 2.0 (snake_case)
        and the legacy (kebab-case/camelCase) field name."""
        snake = to_snake(key)
        return get_field(self.fields, snake, default)

    def __repr__(self) -> str:
        return f"<Container fields={self.fields!r}>"


class File(NamedTuple):
    name: str
    """file name"""

    size: int
    """file size in bytes"""

    completed: int
    """bytes completed"""

    priority: Priority | None
    """download priority"""

    selected: bool | None
    """if selected for download"""

    id: int
    """id of the file of this torrent, not should not be used outside the torrent scope"""

    begin_piece: int | None = None
    """added in Transmission 4.1.0 rpc-version-semver 6.0.0, rpc-version 18"""

    end_piece: int | None = None
    """added in Transmission 4.1.0 rpc-version-semver 6.0.0, rpc-version 18"""


class Group(Container):
    """
    https://github.com/transmission/transmission/blob/4.0.5/docs/rpc-spec.md#482-bandwidth-group-accessor-group-get
    """

    __slots__ = ()

    @property
    def name(self) -> str:
        """Bandwidth group name"""
        return self._get_field("name")

    @property
    def honors_session_limits(self) -> bool:
        """true if session upload limits are honored"""
        return self._get_field("honors_session_limits")

    @property
    def speed_limit_down_enabled(self) -> bool:
        """true means enabled"""
        return self._get_field("speed_limit_down_enabled")

    @property
    def speed_limit_down(self) -> int:
        """max global download speed (KBps)"""
        return self._get_field("speed_limit_down")

    @property
    def speed_limit_up_enabled(self) -> bool:
        """true means enabled"""
        return self._get_field("speed_limit_up_enabled")

    @property
    def speed_limit_up(self) -> int:
        """max global upload speed (KBps)"""
        return self._get_field("speed_limit_up")


class PortTestResult(Container):
    """
    api response of :meth:`transmission_rpc.Client.port_test`

    https://github.com/transmission/transmission/blob/5d159e0/docs/rpc-spec.md#44-port-checking
    """

    __slots__ = ()

    @property
    def port_is_open(self) -> bool:
        """available on all transmission version"""
        return self._get_field("port_is_open")

    @property
    def ip_protocol(self) -> str:
        """``ipv4`` if the test was carried out on IPv4,
        ``ipv6`` if the test was carried out on IPv6,
        unset if it cannot be determined

        Available in Transmission 4.1.0 (rpc-version-semver 6.0.0, rpc-version: 18)
        """
        return self._get_field("ip_protocol")


class BitMap:
    __value: bytes
    __slots__ = ("__value",)

    def __init__(self, b: bytes):
        self.__value = b

    def get(self, index: int) -> bool:
        """
        Args:
            index: piece index
        Returns:
            this method always return a bool, even index overflow piece count of torrent.
            This is because there is no reliable way to know piece count only based on `torrent.pieces`.
        """
        try:
            return bool(self.__value[index // 8] & (1 << (7 - (index % 8))))
        except IndexError:
            return False
