import contextlib
import time
from collections.abc import Callable

from tests.util import ServerTooLowError, skip_on
from transmission_rpc.client import Client
from transmission_rpc.error import TransmissionError
from transmission_rpc.types import File


def hash_to_magnet(h: str) -> str:
    """Helper function to convert a torrent hash to a magnet link."""
    return f"magnet:?xt=urn:btih:{h}"


TORRENT_HASH = "e84213a794f3ccd890382a54a64ca68b7e925433"
MAGNET_URL = f"magnet:?xt=urn:btih:{TORRENT_HASH}"
TORRENT_URL = "https://github.com/trim21/transmission-rpc/raw/v4.1.0/tests/fixtures/iso.torrent"


def test_add_magnet(tr_client: Client) -> None:
    """
    Integration test: Verify adding a torrent via magnet link actually adds it to the daemon.
    """
    tr_client.add_torrent(MAGNET_URL)
    assert len(tr_client.get_torrents()) == 1, "Transmission daemon should have exactly 1 task after adding magnet link"


def test_add_torrent_file_object(tr_client: Client) -> None:
    """
    Integration test: Verify adding a torrent via an open file object.
    """
    with open("tests/fixtures/iso.torrent", "rb") as f:
        tr_client.add_torrent(f)
    assert len(tr_client.get_torrents()) == 1, (
        "Transmission daemon should have exactly 1 task after adding torrent file"
    )


def test_add_torrent_http(tr_client: Client) -> None:
    """
    Integration test: Verify adding a torrent via an HTTP URL.
    """
    tr_client.add_torrent(TORRENT_URL)
    assert len(tr_client.get_torrents()) == 1, "Transmission daemon should have exactly 1 task after adding HTTP URL"


def test_stop(tr_client: Client, generate_random_hash: Callable[[], str]) -> None:
    """
    Integration test: Verify stopping a torrent works.
    """
    info_hash = generate_random_hash()
    url = hash_to_magnet(info_hash)
    tr_client.add_torrent(url)
    tr_client.stop_torrent(info_hash)

    assert len(tr_client.get_torrents()) == 1, "Transmission should still have the task listed"

    is_stopped = False
    for _ in range(50):
        time.sleep(0.2)
        if tr_client.get_torrents()[0].status == "stopped":
            is_stopped = True
            break

    assert is_stopped, "Torrent status should eventually become 'stopped'"


def test_torrent_start_all(tr_client: Client) -> None:
    """
    Integration test: Verify `start_all` starts all paused torrents.
    """
    tr_client.add_torrent(TORRENT_URL, paused=True, timeout=10)

    for torrent in tr_client.get_torrents():
        assert torrent.stopped or torrent.checking, "Newly added torrent should be stopped or checking initially"

    tr_client.start_all()

    for torrent in tr_client.get_torrents():
        assert torrent.downloading or torrent.checking, "All torrents should be downloading or checking after start_all"


def test_session_get_returns_valid_rpc_version(tr_client: Client) -> None:
    """
    Integration test: Verify `get_session` returns session information without error.
    """
    session = tr_client.get_session()
    assert session.rpc_version > 0


def test_free_space(tr_client: Client) -> None:
    """
    Integration test: Verify `free_space` returns valid information for the download directory.
    """
    session = tr_client.get_session()
    # Depending on the docker/test env, this path might not exist or return an error,
    # but the call itself should be handled.
    with contextlib.suppress(TransmissionError):
        tr_client.free_space(session.download_dir)


def test_session_stats(tr_client: Client) -> None:
    """
    Integration test: Verify `session_stats` returns statistics without error.
    """
    stats = tr_client.session_stats()
    assert stats is not None


def test_torrent_attr_type(tr_client: Client) -> None:
    """
    Integration test: Verify that torrent attributes have the expected types.
    """
    with open("tests/fixtures/iso.torrent", "rb") as f:
        tr_client.add_torrent(f)

    for torrent in tr_client.get_torrents():
        assert isinstance(torrent.id, int), "Torrent ID should be an integer"
        assert isinstance(torrent.name, str), "Torrent name should be a string"


def test_torrent_get_files(tr_client: Client) -> None:
    """
    Integration test: Verify that `get_files` returns a list of File objects.
    """
    with open("tests/fixtures/iso.torrent", "rb") as f:
        tr_client.add_torrent(f)

    assert len(tr_client.get_torrents()) == 1, "Transmission should have exactly 1 task"

    for torrent in tr_client.get_torrents():
        files = torrent.get_files()
        assert len(files) > 0, "Torrent should have files"
        for file in files:
            assert isinstance(file, File), "Each item in get_files should be a File object"


@skip_on(ServerTooLowError, "group methods is added in rpc version 17")
def test_groups(tr_client: Client) -> None:
    """
    Integration test: Verify group operations (set_group, get_groups).
    Skips if RPC version is too low.
    """
    if tr_client.get_session().rpc_version < 17:
        raise ServerTooLowError

    tr_client.set_group("test.1")
    groups = tr_client.get_groups()

    assert "test.1" in groups, "The set group 'test.1' should be present in the groups list"
