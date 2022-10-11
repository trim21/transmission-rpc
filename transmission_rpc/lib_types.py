# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Licensed under the MIT license.
import dataclasses
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


_Dataclass_Alias_Name = "alias"


@dataclasses.dataclass
class Group:
    name: str

    # https://github.com/transmission/transmission/issues/3931
    honors_session_limits: bool = dataclasses.field(metadata={_Dataclass_Alias_Name: "honorsSessionLimits"})
    speed_limit_down_enabled: bool = dataclasses.field(metadata={_Dataclass_Alias_Name: "downloadLimited"})
    speed_limit_down: int = dataclasses.field(metadata={_Dataclass_Alias_Name: "downloadLimit"})
    speed_limit_up_enabled: bool = dataclasses.field(metadata={_Dataclass_Alias_Name: "uploadLimited"})
    speed_limit_up: int = dataclasses.field(metadata={_Dataclass_Alias_Name: "uploadLimit"})

    # speed_limit_down_enabled: bool = pydantic.Field(alias='speed-limit-down-enabled')
    # speed_limit_down: int = pydantic.Field(alias='speed-limit-down')
    # speed_limit_up_enabled: bool = pydantic.Field(alias='speed-limit-up-enabled')
    # speed_limit_up: int = pydantic.Field(alias='speed-limit-up')

    @classmethod
    def from_dict(cls, d: dict) -> "Group":
        fields = dataclasses.fields(cls)

        data = {}

        for field in fields:
            if alias := field.metadata.get(_Dataclass_Alias_Name):
                data[field.name] = d[alias]
            else:
                data[field.name] = d[field.name]

        return cls(**data)
