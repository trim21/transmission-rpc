# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Licensed under the MIT license.
from typing import Any, Tuple, Union, Literal, Optional, NamedTuple

_Number = Union[int, float]
_Timeout = Optional[Union[_Number, Tuple[_Number, _Number]]]


class File(NamedTuple):
    name: str  # file name
    size: int  # file size in bytes
    completed: int  # bytes completed
    priority: Literal["high", "normal", "low"]
    selected: bool  # if selected for download


class Field(NamedTuple):
    value: Any
    dirty: bool
