import contextlib
from unittest import mock

import pytest

from tests.conftest import ensure_transmission_running, fake_hash_factory, tr_client


def test_conftest_timeout() -> None:
    # Unwrap fixture
    func = ensure_transmission_running
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__

    # Mock socket to always fail/timeout
    with mock.patch("socket.socket") as mock_sock:
        # Mock connection failure
        mock_sock.return_value.__enter__.return_value.connect.side_effect = ConnectionError
        # Mock time.time to simulate timeout
        with mock.patch("time.time", side_effect=[0, 31]), pytest.raises(ConnectionError, match="timeout"):
            func()


def test_tr_client_fixture() -> None:
    # tr_client is a fixture. access wrapped
    func = tr_client
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__

    # Mock Client
    with mock.patch("tests.conftest.Client") as mock_client_cls:
        c = mock_client_cls.return_value.__enter__.return_value
        c.get_torrents.return_value = [mock.Mock(id=1)]

        # Generator
        gen = func(ensure_transmission_running=None)
        next(gen)  # Setup
        # Verify remove_torrent called
        c.remove_torrent.assert_called_with(1, delete_data=True)

        with contextlib.suppress(StopIteration):
            next(gen)  # Teardown
        # Verify remove_torrent called again
        assert c.remove_torrent.call_count == 2


def test_conftest_success() -> None:
    func = ensure_transmission_running
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__

    with mock.patch("socket.socket") as mock_sock:
        # Connect succeeds
        func()
        # Verify connect called
        mock_sock.return_value.__enter__.return_value.connect.assert_called()


def test_fake_hash_factory() -> None:
    func = fake_hash_factory
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__

    # It returns a lambda
    factory = func()
    # Call lambda
    assert len(factory()) == 40
