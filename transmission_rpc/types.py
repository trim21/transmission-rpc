from typing import Any, Dict, NamedTuple, Optional, Tuple, TypeVar, Union

from transmission_rpc.constants import Priority

_Number = Union[int, float]
_Timeout = Optional[Union[_Number, Tuple[_Number, _Number]]]

T = TypeVar("T")


class Container:
    fields: Dict[str, Any]  #: raw response data

    def __init__(self, *, fields: Dict[str, Any]):
        self.fields = fields

    def get(self, key: str, default: Optional[T] = None) -> Any:
        """get the raw value by the **raw rpc response key**"""
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

    begin_piece: Optional[int] = None
    """add in Transmission 4.1.0 rpc-version-semver 5.4.0, rpc-version 18"""

    end_piece: Optional[int] = None
    """add in Transmission 4.1.0 rpc-version-semver 5.4.0, rpc-version 18"""


class Group(Container):
    """
    https://github.com/transmission/transmission/blob/4.0.5/docs/rpc-spec.md#482-bandwidth-group-accessor-group-get
    """

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
        return self.fields["ipProtocol"]
