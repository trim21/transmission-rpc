from typing import Any, Dict, Tuple, Union, TypeVar, Optional

_Number = Union[int, float]
_Timeout = Optional[Union[_Number, Tuple[_Number, _Number]]]

T = TypeVar("T")


class Container:
    fields: Dict[str, Any]  #: raw fields

    def __init__(self, *, fields: Dict[str, Any]):
        self.fields = fields

    def get(self, key: str, default: Optional[T] = None) -> Any:
        """get the raw value from files by the **raw keys**"""
        return self.fields.get(key, default)


class Group(Container):
    @property
    def name(self) -> str:
        return self.fields["name"]

    @property
    def honors_session_limits(self) -> bool:
        return self.fields["honorsSessionLimits"]

    @property
    def speed_limit_down_enabled(self) -> bool:
        return self.fields["speed-limit-down-enabled"]

    @property
    def speed_limit_down(self) -> int:
        return self.fields["speed-limit-down"]

    @property
    def speed_limit_up_enabled(self) -> bool:
        return self.fields["speed-limit-up-enabled"]

    @property
    def speed_limit_up(self) -> int:
        return self.fields["speed-limit-up"]
