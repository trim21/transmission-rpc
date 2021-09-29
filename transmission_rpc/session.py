# Copyright (c) 2018-2021 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
from typing import TYPE_CHECKING, Any, Dict, Tuple, Union, Generator

from typing_extensions import Literal

from transmission_rpc.lib_types import Field

if TYPE_CHECKING:
    from transmission_rpc.client import Client


class Session:
    """
    Session is a dict-like class holding the session data for a Transmission daemon.

    Access the session field can be done through attributes.
    The attributes available are the same as the session arguments in the
    Transmission RPC specification, but with underscore instead of hyphen.


    get ``'download-dir'`` with ``session.download_dir``.

    .. code-block:: python

        session = Client().get_session()

        current = session.download_dir


    there are also setter like ``Session().download_dir = '/path/to/download'``

    .. code-block:: python

        session = Client().get_session()

        session.download_dir = '/path/to/new/download/dir'


    if you want to batch update a session, call ``.update(data)``

    .. code-block:: python

        session = Client().get_session()

        session.update({'k1': 'v1', "k2": "v2"})


    if you have to access to the private ``Session()._fields``,
    keys are stored with underscore.
    """

    def __init__(self, client: "Client", fields: Dict[str, Any] = None):
        self._client = client
        self._fields: Dict[str, Field] = {}
        if fields is not None:
            self._update(fields)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._fields[name].value
        except KeyError as e:
            raise AttributeError(f"No attribute {name}") from e

    def _set(self, key: str, value: Any, commit: bool = False) -> None:
        key = key.replace("-", "_")
        current_field = self._fields.get(key)
        if current_field is None:
            self._fields[key] = Field(value, True)
        else:
            if current_field.value != value:
                self._fields[key] = Field(value, True)
        if commit:
            self._commit(key, value)

    def __str__(self) -> str:
        text = ""
        max_length = max(len(x) for x in self._fields.keys()) + 1
        for key, value in sorted(self._fields.items(), key=lambda x: x[0]):
            text += f"{key.ljust(max_length)}: {value.value!r}\n"
        return text

    def _commit(self, key: str = None, value: Any = None) -> None:
        """submit all dirty field to client"""
        dirty = {}

        if key is not None and value is not None:
            dirty[key] = value
        else:
            for k, v in self._fields.items():
                if v.dirty:
                    dirty[k] = v.value

        self._client.set_session(**dirty)

    def _update(self, other: Union[Dict[str, Any], "Session"]) -> None:
        if isinstance(other, dict):
            for key, value in other.items():
                self._set(key, value)
        elif isinstance(other, Session):
            for key, value in other._fields.items():
                self._set(key, value.value)
        else:
            raise ValueError("Cannot update with supplied data")

    def update(self, other: Union[Dict[str, Any], "Session"]) -> None:
        """
        Update the session data from a Transmission JSON-RPC arguments dictionary
        """
        self._update(other)
        self._commit()

    def keys(self) -> Generator[str, None, None]:
        """
        session keys with underscore (eg: ``download_dir``)
        """
        yield from self._fields.keys()

    def values(self) -> Generator[Any, None, None]:
        for value in self._fields.values():
            yield value.value

    def items(self) -> Generator[Tuple[str, Any], None, None]:
        """
        iter key,value pair

        hyphen in key is replace by underscore. (eg: ``'download_dir'``)
        """
        for key, field in self._fields.items():
            yield key, field.value

    @property
    def download_dir(self) -> str:
        """default download location

        - rpc version 12
        - transmission version 2.20
        :return:
        """
        return self.__getattr__("download_dir")

    @download_dir.setter
    def download_dir(self, location: str) -> None:
        """Enable/disable peer exchange."""
        if isinstance(location, str) and location:
            self._set("download_dir", location, True)
        else:
            raise TypeError(f"{location!r} if not a valid 'download-dir'")

    @property
    def version(self) -> str:
        """
        - rpc version 3
        - transmission version 1.41
        """
        return self.__getattr__("version")

    @property
    def rpc_version(self) -> int:
        """
        - rpc version 4
        - transmission version 1.50
        """
        return self.__getattr__("rpc_version")

    @property
    def peer_port(self) -> int:
        """Get the peer port.

        - rpc version 5
        - transmission version 1.60
        """
        return self.__getattr__("peer_port")

    @peer_port.setter
    def peer_port(self, port: int) -> None:
        """Set the peer port.

        - rpc version 5
        - transmission version 1.60
        """
        if isinstance(port, int):
            self._set("peer_port", port, True)
        else:
            raise ValueError("Not a valid limit")

    @property
    def pex_enabled(self) -> bool:
        """Is peer exchange enabled

        - rpc version 5
        - transmission version 1.60"""
        return self.__getattr__("pex_enabled")

    @pex_enabled.setter
    def pex_enabled(self, enabled: bool) -> None:
        """Enable/disable peer exchange."""
        if isinstance(enabled, bool):
            self._set("pex_enabled", enabled, True)
        else:
            raise TypeError("Not a valid type")

    @property
    def encryption(self) -> str:
        return self.__getattr__("encryption")

    @encryption.setter
    def encryption(self, value: Literal["required", "preferred", "tolerated"]) -> None:
        if value in {"required", "preferred", "tolerated"}:
            self._set("encryption", value, commit=True)
        else:
            raise ValueError(
                "Not a valid encryption, can only be one of ['required', 'preferred', 'tolerated']"
            )
