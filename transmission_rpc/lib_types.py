from typing import Any, Tuple, Union, Optional, NamedTuple

from typing_extensions import Literal

from transmission_rpc.utils import format_size

_Number = Union[int, float]
_Timeout = Optional[Union[_Number, Tuple[_Number, _Number]]]


class File(NamedTuple):
    name: str  # file name
    size: int  # file size in bytes
    completed: int  # bytes completed
    priority: Literal["high", "normal", "low"]
    selected: bool  # if selected for download

    def __str__(self):
        size = format_size(self.size)
        human_size = f"{round(size[0],1)} {size[1]}"
        return (
            f"File(name={self.name}, size={human_size}, completed={self.completed}, "
            f"priority={self.priority}, selected={self.selected})"
        )

    __repr__ = __str__


class Field(NamedTuple):
    value: Any
    dirty: bool
