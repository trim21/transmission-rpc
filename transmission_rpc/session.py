# Copyright (c) 2018-2020 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
from typing import TYPE_CHECKING, Any, Dict, List, Union

from transmission_rpc.lib_types import Field, _Timeout

if TYPE_CHECKING:
    from transmission_rpc.client import Client


class Session:
    """
    Session is a class holding the session data for a Transmission daemon.

    Access the session field can be done through attributes.
    The attributes available are the same as the session arguments in the
    Transmission RPC specification, but with underscore instead of hyphen.
    ``download-dir`` -> ``download_dir``.
    """

    def __init__(self, client: "Client", fields: Dict[str, Any] = None):
        self._client = client
        self._fields: Dict[str, Field] = {}
        if fields is not None:
            self._update_fields(fields)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._fields[name].value
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
                self._fields[key.replace("-", "_")] = Field(value, False)
        elif isinstance(other, Session):
            for key in list(other._fields.keys()):
                self._fields[key] = Field(other._fields[key].value, False)
        else:
            raise ValueError("Cannot update with supplied data")

    def _dirty_fields(self) -> List[str]:
        """Enumerate changed fields"""
        outgoing_keys = ["peer_port", "pex_enabled"]
        fields = []
        for key in outgoing_keys:
            if key in self._fields and self._fields[key].dirty:
                fields.append(key)
        return fields

    def _push(self) -> None:
        """Push changed fields to the server"""
        dirty = self._dirty_fields()
        args = {}
        for key in dirty:
            args[key] = self._fields[key].value
            self._fields[key] = self._fields[key]._replace(dirty=False)
        if len(args) > 0:
            self._client.set_session(**args)

    def update(self, timeout: _Timeout = None) -> None:
        """Update the session information."""
        self._push()
        session = self._client.get_session(timeout=timeout)
        self._update_fields(session)
        session = self._client.session_stats(timeout=timeout)
        self._update_fields(session)

    def from_request(self, data: dict) -> None:
        """Update the session information."""
        self._update_fields(data)

    @property
    def peer_port(self) -> int:
        """
        Get the peer port.
        """
        return self._fields["peer_port"].value

    @peer_port.setter
    def peer_port(self, port: int) -> None:
        """
        Set the peer port.
        """
        if isinstance(port, int):
            self._fields["peer_port"] = Field(port, True)
            self._push()
        else:
            raise ValueError("Not a valid limit")

    @property
    def pex_enabled(self) -> bool:
        """Is peer exchange enabled?"""
        return self._fields["pex_enabled"].value

    @pex_enabled.setter
    def pex_enabled(self, enabled: bool) -> None:
        """Enable/disable peer exchange."""
        if isinstance(enabled, bool):
            self._fields["pex_enabled"] = Field(enabled, True)
            self._push()
        else:
            raise TypeError("Not a valid type")
