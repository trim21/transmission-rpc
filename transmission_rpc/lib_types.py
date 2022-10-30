from typing import Any, Dict, Tuple, Union, Literal, TypeVar, Optional, NamedTuple

_Number = Union[int, float]
_Timeout = Optional[Union[_Number, Tuple[_Number, _Number]]]

T = TypeVar("T")


class Container:
    fields: Dict[str, Any]

    def __init__(self, *, fields: Dict[str, Any]):
        self.fields = fields

    def get(self, key: str, default: T = None) -> Any:
        return self.fields.get(key, default)


class File(NamedTuple):
    name: str  # file name
    size: int  # file size in bytes
    completed: int  # bytes completed
    priority: Literal["high", "normal", "low"]
    selected: bool  # if selected for download
    id: int  # id of the file of this torrent, not should not be used outside the torrent scope.


class Group(Container):
    @property
    def name(self) -> str:
        return self.fields["name"]

    # https://github.com/transmission/transmission/issues/3931

    @property
    def honors_session_limits(self) -> bool:
        return self.fields["honorsSessionLimits"]

    @property
    def speed_limit_down_enabled(self) -> bool:
        return self.fields["downloadLimited"]

    @property
    def speed_limit_down(self) -> int:
        return self.fields["downloadLimit"]

    @property
    def speed_limit_up_enabled(self) -> bool:
        return self.fields["uploadLimited"]

    @property
    def speed_limit_up(self) -> int:
        return self.fields["uploadLimit"]

    # speed_limit_down_enabled: bool = pydantic.Field(alias='speed-limit-down-enabled')
    # speed_limit_down: int = pydantic.Field(alias='speed-limit-down')
    # speed_limit_up_enabled: bool = pydantic.Field(alias='speed-limit-up-enabled')
    # speed_limit_up: int = pydantic.Field(alias='speed-limit-up')
