"""
exception raise by this package
"""
# Copyright (c) 2018-2020 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
from typing import Optional

import requests.exceptions
from requests.models import Response


class TransmissionError(Exception):
    """
    This exception is raised when there has occurred an error related to
    communication with Transmission.
    """

    def __init__(self, message: str = "", original: Optional[Response] = None):
        Exception.__init__(self)
        self.message = message
        self.original = original

    def __str__(self) -> str:
        if self.original:
            original_name = type(self.original).__name__
            return '{} Original exception: {}, "{}"'.format(
                self.message, original_name, str(self.original)
            )
        return self.message


class TransmissionAuthError(TransmissionError):
    """Raised when username or password is incorrect"""


class TransmissionConnectError(TransmissionError, requests.exceptions.ConnectionError):
    """raised when client can't connect to transmission daemon"""


class TransmissionTimeoutError(TransmissionConnectError, requests.exceptions.Timeout):
    """Timeout"""
