import contextlib
from typing import Any, cast

import pytest

from transmission_rpc.client import Client


@pytest.mark.parametrize("arg", [float(1), "non_hash_string"])
def test_start_torrent_raises_on_invalid_id(mock_network: Any, success_response: Any, arg: Any) -> None:
    """
    Verify that invalid torrent IDs raise ValueError.
    We use start_torrent to trigger ID parsing validation.
    """
    mock_network.return_value = success_response()
    c = Client()
    with pytest.raises(ValueError, match="torrent id"):
        c.start_torrent(ids=arg)


@pytest.mark.parametrize(
    ("arg", "expected_ids"),
    [
        ("recently_active", "recently_active"),
        ("51ba7d0dd45ab9b9564329c33f4f97493b677924", ["51ba7d0dd45ab9b9564329c33f4f97493b677924"]),
        ((2, "51ba7d0dd45ab9b9564329c33f4f97493b677924"), [2, "51ba7d0dd45ab9b9564329c33f4f97493b677924"]),
        (3, [3]),
        (None, None),
        ([], None),
    ],
)
def test_parse_torrent_ids_structure(mock_network: Any, success_response: Any, arg: Any, expected_ids: Any) -> None:
    """
    Verify that passing various ID formats results in the correct 'ids' argument in the RPC call.
    """
    mock_network.return_value = success_response()
    c = Client()

    c.start_torrent(ids=arg)

    # Check what was sent to the network
    sent_json = mock_network.call_args[1]["json"]
    sent_ids = sent_json["params"].get("ids")

    assert sent_ids == expected_ids


@pytest.mark.parametrize("arg", [None, []])
def test_stop_torrent_requires_ids(mock_network: Any, success_response: Any, arg: Any) -> None:
    """Verify that allowing empty ids for start actions does not change methods that require ids."""
    mock_network.return_value = success_response()
    c = Client()

    with pytest.raises(ValueError, match="request require ids"):
        c.stop_torrent(ids=arg)


@pytest.mark.parametrize("arg", ["not_recently_active", "non_hash_string", -1, 1.1, "5:10", "5,6,8,9,10"])
def test_parse_torrent_ids_value_error(mock_network: Any, success_response: Any, arg: Any) -> None:
    """
    Verify that invalid ID inputs raise ValueError via the public API.
    """
    mock_network.return_value = success_response()
    c = Client()
    with pytest.raises(ValueError, match="torrent id"):
        c.start_torrent(ids=arg)


def test_public_api_validates_torrent_ids(mock_network: Any, success_response: Any) -> None:
    """
    Verify validation logic for invalid IDs (length, content, type) when accessed through public methods like get_torrent.
    """
    mock_network.return_value = success_response()
    c = Client()

    # Test invalid string length via get_torrent
    with pytest.raises(ValueError, match="not valid torrent id"):
        c.get_torrent("a")  # too short

    # Test invalid string content
    with pytest.raises(ValueError, match="not valid torrent id"):
        c.get_torrent("z" * 40)

    # Test invalid type
    with pytest.raises(ValueError, match="Invalid torrent id"):
        c.start_torrent(ids=cast("Any", 1.5))

    # Test valid hash string
    h = "a" * 40
    mock_network.side_effect = [success_response({"torrents": []})]
    with contextlib.suppress(KeyError):
        c.get_torrent(h)
