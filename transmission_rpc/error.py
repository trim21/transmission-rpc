"""
exception raise by this package
"""

from __future__ import annotations

from typing import Any

import typing_extensions
from urllib3 import BaseHTTPResponse


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
    original: BaseHTTPResponse | None  # original http requests

    def __init__(
        self,
        message: str = "",
        method: Any | None = None,
        argument: Any | None = None,
        response: Any | None = None,
        raw_response: str | None = None,
        original: BaseHTTPResponse | None = None,
    ):
        super().__init__()
        self.message = message
        self.method = method
        self.argument = argument
        self.response = response
        self.raw_response = raw_response
        self.original = original

    def __str__(self) -> str:
        if self.original:
            original_name = type(self.original).__name__
            return f'{self.message} Original exception: {original_name}, "{self.original}"'
        return self.message

    @property
    @typing_extensions.deprecated("use .raw_response instead")
    def rawResponse(self) -> str | None:
        return self.raw_response


class TransmissionAuthError(TransmissionError):
    """Raised when username or password is incorrect"""


class TransmissionConnectError(TransmissionError):
    """raised when client can't connect to transmission daemon"""


class TransmissionTimeoutError(TransmissionConnectError):
    """Timeout"""
