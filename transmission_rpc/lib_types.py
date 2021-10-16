# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Licensed under the MIT license.
from copy import deepcopy
from typing import Any, Dict, Tuple, Union, Optional, Generator, NamedTuple

from transmission_rpc.utils import _to_snake
from transmission_rpc.constants import Priority

_Number = Union[int, float]
_Timeout = Optional[Union[_Number, Tuple[_Number, _Number]]]


class File(NamedTuple):
    name: str  # file name
    size: int  # file size in bytes
    completed: int  # bytes completed
    priority: Priority
    selected: bool  # if selected for download


class _Base:
    _fields: Dict[str, Any]

    def __init__(self, other: Dict[str, Any] = None):
        self._fields: Dict[str, Any] = {}
        if isinstance(other, dict):
            for key, value in other.items():
                self._fields[_to_snake(key)] = value
        elif isinstance(other, _Base):
            for key in list(other._fields.keys()):
                self._fields[_to_snake(key)] = deepcopy(other._fields[key])
        elif other is None:
            pass
        else:
            raise ValueError("Cannot update with supplied data")

    def __getattr__(self, name: str) -> Any:
        if name in self._fields:
            return self._fields[name]
        raise KeyError(f"Attribute '{name}' not available")

    def items(self) -> Generator[Tuple[str, Any], None, None]:
        for key, field in self._fields.items():
            yield _to_snake(key), field
