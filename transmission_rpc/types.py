from __future__ import annotations

import re
from typing import Any, NamedTuple

from transmission_rpc.constants import Priority

_RE_CAMEL1 = re.compile(r"(.)([A-Z][a-z]+)")
_RE_CAMEL2 = re.compile(r"([a-z0-9])([A-Z])")


def _to_snake(name: str) -> str:
    """Convert camelCase or kebab-case to snake_case.

    Examples::

        _to_snake("hashString")         -> "hash_string"
        _to_snake("file-count")         -> "file_count"
        _to_snake("trackerStats")       -> "tracker_stats"
        _to_snake("peersGettingFromUs") -> "peers_getting_from_us"
    """
    name = name.replace("-", "_")
    name = _RE_CAMEL1.sub(r"\1_\2", name)
    return _RE_CAMEL2.sub(r"\1_\2", name).lower()


class _FieldDict(dict):  # type: ignore[type-arg]
    """A ``dict`` subclass that transparently falls back to snake_case key lookup.

    When a key is not found, the lookup is retried with the snake_case equivalent of
    the key.  This lets all existing property accessors that use camelCase or
    kebab-case keys work seamlessly with JSON-RPC 2.0 responses, which use snake_case
    field names.

    Example: accessor uses ``self.fields["hashString"]``; if the response contained
    ``hash_string`` (JSON-RPC 2.0), the dict transparently returns the right value.
    """

    def __missing__(self, key: str) -> Any:
        snake = _to_snake(key)
        if snake != key and snake in self:
            return self[snake]
        raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        if super().__contains__(key):
            return True
        if isinstance(key, str):
            snake = _to_snake(key)
            return snake != key and super().__contains__(snake)
        return False

    def get(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        try:
            return self[key]
        except KeyError:
            return default


class Container:
    fields: _FieldDict  #: raw response data
    __slots__ = ("fields",)

    def __init__(self, *, fields: dict[str, Any]):
        self.fields = _FieldDict(fields)

    def get(self, key: str, default: Any | None = None) -> Any:
        """get the raw value by the **raw rpc response key**"""
        return self.fields.get(key, default)

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
    """add in Transmission 4.1.0 rpc-version-semver 5.4.0, rpc-version 18"""

    end_piece: int | None = None
    """add in Transmission 4.1.0 rpc-version-semver 5.4.0, rpc-version 18"""


class Group(Container):
    """
    https://github.com/transmission/transmission/blob/4.0.5/docs/rpc-spec.md#482-bandwidth-group-accessor-group-get
    """

    __slots__ = ()

    @property
    def name(self) -> str:
        """Bandwidth group name"""
        return self.fields["name"]

    @property
    def honors_session_limits(self) -> bool:
        """true if session upload limits are honored"""
        return self.fields["honorsSessionLimits"]

    @property
    def speed_limit_down_enabled(self) -> bool:
        """true means enabled"""
        return self.fields["speed-limit-down-enabled"]

    @property
    def speed_limit_down(self) -> int:
        """max global download speed (KBps)"""
        return self.fields["speed-limit-down"]

    @property
    def speed_limit_up_enabled(self) -> bool:
        """true means enabled"""
        return self.fields["speed-limit-up-enabled"]

    @property
    def speed_limit_up(self) -> int:
        """max global upload speed (KBps)"""
        return self.fields["speed-limit-up"]


class PortTestResult(Container):
    """
    api response of :meth:`transmission_rpc.Client.port_test`

    https://github.com/transmission/transmission/blob/5d159e0/docs/rpc-spec.md#44-port-checking
    """

    __slots__ = ()

    @property
    def port_is_open(self) -> bool:
        """available on all transmission version"""
        return self.fields["port-is-open"]

    @property
    def ip_protocol(self) -> str:
        """``ipv4`` if the test was carried out on IPv4,
        ``ipv6`` if the test was carried out on IPv6,
        unset if it cannot be determined

        Available in Transmission 4.1.0 (rpc-version-semver 5.4.0, rpc-version: 18)
        """
        return self.fields["ip_protocol"]


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


class WebseedEx(Container):
    """
    type for :py:attr:`Torrent.webseeds_ex`

    Added in Transmission 4.2.0 (rpc-version 19).
    """

    __slots__ = ()

    @property
    def url(self) -> str:
        """URL of the webseed."""
        return self.fields["url"]

    @property
    def is_downloading(self) -> bool:
        """True if the webseed is currently downloading."""
        return self.fields["is_downloading"]

    @property
    def download_bytes_per_second(self) -> int:
        """Download rate in bytes per second."""
        return self.fields["download_bytes_per_second"]
