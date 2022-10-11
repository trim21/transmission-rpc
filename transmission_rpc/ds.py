"""
dataclasses utils
"""
import dataclasses
from typing import Type, TypeVar

Model = TypeVar("Model")
alias_metadata = "alias"


def from_dict(cls: Type["Model"], obj: dict) -> "Model":
    fields = dataclasses.fields(cls)

    data = {}

    for field in fields:
        if alias := field.metadata.get(alias_metadata):
            value = obj[alias]
        else:
            value = obj[field.name]

        if dataclasses.is_dataclass(field.type):
            data[field.name] = from_dict(field.type, value)
        else:
            data[field.name] = value

    return cls(**data)
