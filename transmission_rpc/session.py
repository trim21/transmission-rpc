# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
from typing import TYPE_CHECKING, Any, Dict, Tuple, Union, Generator

from transmission_rpc.lib_types import Field

if TYPE_CHECKING:
    pass


class Session:
    """
    Session is a class holding the session data for a Transmission daemon.

    Access the session field can be done through attributes.
    The attributes available are the same as the session arguments in the
    Transmission RPC specification, but with underscore instead of hyphen.
    ``download-dir`` -> ``download_dir``.
    """

    def __init__(self, fields: Dict[str, Any] = None):
        self._fields: Dict[str, Field] = {}
        if fields is not None:
            self._update_fields(fields)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._fields[name.replace("_", "-")].value
        except KeyError as e:
            raise AttributeError(f"No attribute {name}") from e

    def __str__(self) -> str:
        text = ""
        max_length = max(len(x) for x in self._fields.keys()) + 1
        for key, value in sorted(self._fields.items(), key=lambda x: x[0]):
            text += f"{key.ljust(max_length)}: {value.value!r}\n"
        return text

    def _update_fields(self, other: Union[Dict[str, Any], "Session"]) -> None:
        """
        Update the session data from a Transmission JSON-RPC arguments dictionary
        """
        if isinstance(other, dict):
            for key, value in other.items():
                self._fields[key] = Field(value, False)
        elif isinstance(other, Session):
            for key in list(other._fields.keys()):
                self._fields[key] = Field(other._fields[key].value, False)
        else:
            raise ValueError("Cannot update with supplied data")

    def items(self) -> Generator[Tuple[str, Any], None, None]:
        for key, field in self._fields.items():
            yield key, field.value

    def from_request(self, data: dict) -> None:
        """Update the session information."""
        self._update_fields(data)

    @property
    def download_dir(self) -> str:
        """default download location

        rpc version 12
        transmission version 2.20
        :return:
        """
        return self.__getattr__("version")

    @property
    def version(self) -> str:
        """
        rpc version 3
        transmission version 1.41
        """
        return self.__getattr__("version")

    @property
    def rpc_version(self) -> int:
        """
        rpc version 4
        transmission version 1.50
        """
        return self.__getattr__("rpc-version")

    @property
    def peer_port(self) -> int:
        """Get the peer port.

        rpc version 5
        transmission version 1.60
        """
        return self.__getattr__("peer-port")

    @property
    def pex_enabled(self) -> bool:
        """Is peer exchange enabled

        rpc version 5
        transmission version 1.60"""
        return self.__getattr__("pex-enabled")
