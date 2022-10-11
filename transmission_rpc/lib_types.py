# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Licensed under the MIT license.
import dataclasses
from typing import Any, Tuple, Union, Literal, Optional, NamedTuple

from .ds import alias

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


@dataclasses.dataclass(frozen=True)
class Group:
    name: str

    # https://github.com/transmission/transmission/issues/3931
    honors_session_limits: bool = dataclasses.field(metadata={alias: "honorsSessionLimits"})
    speed_limit_down_enabled: bool = dataclasses.field(metadata={alias: "downloadLimited"})
    speed_limit_down: int = dataclasses.field(metadata={alias: "downloadLimit"})
    speed_limit_up_enabled: bool = dataclasses.field(metadata={alias: "uploadLimited"})
    speed_limit_up: int = dataclasses.field(metadata={alias: "uploadLimit"})

    # speed_limit_down_enabled: bool = pydantic.Field(alias='speed-limit-down-enabled')
    # speed_limit_down: int = pydantic.Field(alias='speed-limit-down')
    # speed_limit_up_enabled: bool = pydantic.Field(alias='speed-limit-up-enabled')
    # speed_limit_up: int = pydantic.Field(alias='speed-limit-up')
