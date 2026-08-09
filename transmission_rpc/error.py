"""
exception raise by this package
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from typing_extensions import deprecated

if TYPE_CHECKING:
    from requests.models import Response


class TransmissionError(Exception):
    """
    This exception is raised when there has occurred an error related to
    communication with Transmission.
    """

    message: str
    method: Any | None  # rpc call method
    argument: Any | None  # rpc call arguments
    response: Any | None  # parsed json response, may be dict with keys 'result' and 'arguments'
    raw_response: str | None  # raw text http response
    original: Response | None  # original http requests

    def __init__(
        self,
        message: str = "",
        method: Any | None = None,
        argument: Any | None = None,
        response: Any | None = None,
        rawResponse: str | None = None,
        original: Response | None = None,
        *,
        raw_response: str | None = None,
    ):
        super().__init__()
        if rawResponse is not None and raw_response is not None:
            raise ValueError("rawResponse and raw_response cannot both be set")
        if rawResponse is not None:
            warnings.warn("rawResponse is deprecated; use raw_response instead", DeprecationWarning, stacklevel=2)
            raw_response = rawResponse
        self.message = message
        self.method = method
        self.argument = argument
        self.response = response
        self.raw_response = raw_response
        self.original = original

    @property
    @deprecated("use .raw_response instead")
    def rawResponse(self) -> str | None:
        return self.raw_response

    @rawResponse.setter
    @deprecated("use .raw_response instead")
    def rawResponse(self, value: str | None) -> None:
        self.raw_response = value

    def __str__(self) -> str:
        if self.original:
            original_name = type(self.original).__name__
            return f'{self.message} Original exception: {original_name}, "{self.original}"'
        return self.message


class TransmissionAuthError(TransmissionError):
    """Raised when username or password is incorrect"""


class TransmissionConnectError(TransmissionError):
    """raised when client can't connect to transmission daemon"""


class TransmissionTimeoutError(TransmissionConnectError):
    """Timeout"""
