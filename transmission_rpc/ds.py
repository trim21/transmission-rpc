"""
dataclasses utils
"""
import dataclasses
from typing import Type, TypeVar, Optional

Model = TypeVar("Model")
alias = "alias"


def from_dict(cls: Type[Model], obj: Optional[dict]) -> Model:
    if obj is None:
        return cls()
    fields = dataclasses.fields(cls)

    data = {}

    for field in fields:
        name = field.name
        if field_alias := field.metadata.get(alias):
            name = field_alias

        if field.default is not dataclasses.MISSING or field.default_factory is not dataclasses.MISSING:
            value = obj.get(name)
        else:
            value = obj[name]

        if dataclasses.is_dataclass(field.type):
            data[field.name] = from_dict(field.type, value)
        else:
            data[field.name] = value

    return cls(**data)
