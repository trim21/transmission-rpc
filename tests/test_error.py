import pytest

from transmission_rpc.error import TransmissionError


def test_raw_response_name():
    error = TransmissionError(raw_response="response")
    assert error.raw_response == "response"

    with pytest.warns(DeprecationWarning, match="raw_response"):
        assert error.rawResponse == "response"


def test_deprecated_raw_response_constructor_name():
    with pytest.warns(DeprecationWarning, match="raw_response"):
        error = TransmissionError(rawResponse="response")
    assert error.raw_response == "response"


def test_raw_response_names_are_mutually_exclusive():
    with pytest.raises(ValueError, match="cannot both be set"):
        TransmissionError(rawResponse="old", raw_response="new")
