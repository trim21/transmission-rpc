# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Licensed under the MIT license.
from typing import Any, Tuple, Union, Literal, Optional, NamedTuple

import pydantic

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


class Group(pydantic.BaseModel):
    name: str

    # https://github.com/transmission/transmission/issues/3931
    honors_session_limits: bool = pydantic.Field(alias="honorsSessionLimits")
    speed_limit_down_enabled: bool = pydantic.Field(alias="downloadLimited")
    speed_limit_down: int = pydantic.Field(alias="downloadLimit")
    speed_limit_up_enabled: bool = pydantic.Field(alias="uploadLimited")
    speed_limit_up: int = pydantic.Field(alias="uploadLimit")

    # speed_limit_down_enabled: bool = pydantic.Field(alias='speed-limit-down-enabled')
    # speed_limit_down: int = pydantic.Field(alias='speed-limit-down')
    # speed_limit_up_enabled: bool = pydantic.Field(alias='speed-limit-up-enabled')
    # speed_limit_up: int = pydantic.Field(alias='speed-limit-up')
