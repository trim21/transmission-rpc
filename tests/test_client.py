import os
import json
import time
import base64
import os.path
import secrets
from unittest import mock

import pytest

from transmission_rpc import LOGGER
from transmission_rpc.client import Client
from transmission_rpc.lib_types import File

HOST = os.getenv("TR_HOST", "127.0.0.1")
PORT = int(os.getenv("TR_PORT", "9091"))
USER = os.getenv("TR_USER", "admin")
PASSWORD = os.getenv("TR_PASSWORD", "password")


def test_client_parse_url(mock_version):
    with mock.patch("transmission_rpc.client.Client._request"):
        client = Client()
        assert client.url == "http://127.0.0.1:9091/transmission/rpc"


def hash_to_magnet(h):
    return f"magnet:?xt=urn:btih:{h}"


torrent_hash = "e84213a794f3ccd890382a54a64ca68b7e925433"
magnet_url = f"magnet:?xt=urn:btih:{torrent_hash}"
torrent_hash2 = "9fc20b9e98ea98b4a35e6223041a5ef94ea27809"
torrent_url = "https://releases.ubuntu.com/20.04/ubuntu-20.04-desktop-amd64.iso.torrent"


@pytest.fixture()
def mock_version():
    v = property(lambda x: "2.80 (hello)")
    rpc_v = property(lambda x: 14)
    with mock.patch("transmission_rpc.session.Session.version", v), mock.patch(
        "transmission_rpc.session.Session.rpc_version", rpc_v
    ):
        yield


@pytest.fixture()
def tr_client():
    LOGGER.setLevel("INFO")
    with Client(host=HOST, port=PORT, username=USER, password=PASSWORD) as c:
        for torrent in c.get_torrents():
            c.remove_torrent(torrent.id, delete_data=True)
        yield c
        for torrent in c.get_torrents():
            c.remove_torrent(torrent.id, delete_data=True)


@pytest.fixture()
def fake_hash_factory():
    return lambda: secrets.token_hex(20)


def test_client_add_url(mock_version):
    m = mock.Mock(return_value={"hello": "world"})
    with mock.patch("transmission_rpc.client.Client._request", m):
        assert Client().add_torrent(torrent_url) == "world"
        m.assert_called_with("torrent-add", {"filename": torrent_url}, timeout=None)


def test_client_add_magnet(mock_version):
    m = mock.Mock(return_value={"hello": "world"})
    with mock.patch("transmission_rpc.client.Client._request", m):
        assert Client().add_torrent(magnet_url) == "world"
        m.assert_called_with("torrent-add", {"filename": magnet_url}, timeout=None)


def test_client_add_base64_raw_data(mock_version):
    m = mock.Mock(return_value={"hello": "world"})
    with mock.patch("transmission_rpc.client.Client._request", m):
        with open("tests/fixtures/iso.torrent", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        assert Client().add_torrent(b64) == "world"
        m.assert_called_with("torrent-add", {"metainfo": b64}, timeout=None)


def test_real_add_magnet(tr_client: Client):
    tr_client.add_torrent(magnet_url)
    assert len(tr_client.get_torrents()) == 1, "transmission should has at least 1 task"


def test_real_add_torrent_fd(tr_client: Client):
    with open("tests/fixtures/iso.torrent", "rb") as f:
        tr_client.add_torrent(f)
    assert len(tr_client.get_torrents()) == 1, "transmission should has at least 1 task"


def test_real_add_torrent_base64(tr_client: Client):
    with open("tests/fixtures/iso.torrent", "rb") as f:
        tr_client.add_torrent(base64.b64encode(f.read()).decode())
    assert len(tr_client.get_torrents()) == 1, "transmission should has at least 1 task"


def test_real_add_torrent_file_protocol(tr_client: Client):
    fs = os.path.abspath(
        os.path.join(
            os.path.dirname(
                __file__,
            ),
            "fixtures/iso.torrent",
        )
    )
    tr_client.add_torrent("file://" + fs)
    assert len(tr_client.get_torrents()) == 1, "transmission should has at least 1 task"


def test_real_add_torrent_http(tr_client: Client):
    tr_client.add_torrent(
        "https://github.com/Trim21/transmission-rpc/raw/master/tests/fixtures/iso.torrent"
    )
    assert len(tr_client.get_torrents()) == 1, "transmission should has at least 1 task"


def test_real_add_torrent_not_endswith_torrent(tr_client: Client):
    # The shorten url is ref to
    # "https://github.com/Trim21/transmission-rpc/raw/master/tests/fixtures/iso.torrent"
    tr_client.add_torrent("https://git.io/JJUVt")
    assert len(tr_client.get_torrents()) == 1, "transmission should has at least 1 task"


def test_real_stop(tr_client: Client, fake_hash_factory):
    info_hash = fake_hash_factory()
    url = hash_to_magnet(info_hash)
    tr_client.add_torrent(url)
    tr_client.stop_torrent(info_hash)
    assert len(tr_client.get_torrents()) == 1, "transmission should has only 1 task"
    ret = False

    for _ in range(50):
        time.sleep(0.2)
        if tr_client.get_torrents()[0].status == "stopped":
            ret = True
            break

    assert ret, "torrent should be stopped"


def test_real_torrent_start_all(tr_client: Client, fake_hash_factory):
    tr_client.add_torrent(hash_to_magnet(fake_hash_factory()), paused=True, timeout=1)
    tr_client.add_torrent(hash_to_magnet(fake_hash_factory()), paused=True, timeout=1)
    for torrent in tr_client.get_torrents():
        assert torrent.status == "stopped", "all torrent should be stopped"

    tr_client.start_all()
    for torrent in tr_client.get_torrents():
        assert torrent.status == "downloading", "all torrent should be downloading"


def test_real_get_files(tr_client: Client):
    with open("tests/fixtures/iso.torrent", "rb") as f:
        tr_client.add_torrent(f)
    assert len(tr_client.get_torrents()) == 1, "transmission should has at least 1 task"
    for tid, files in tr_client.get_files(1).items():
        assert files
        assert isinstance(tid, int)
        for file in files:
            assert isinstance(file, File)


def test_real_session_get(tr_client: Client):
    tr_client.get_session()


def test_real_free_space(tr_client: Client):
    session = tr_client.get_session()
    tr_client.free_space(session.download_dir)


def test_real_session_stats(tr_client: Client):
    tr_client.session_stats()


def test_wrong_logger():
    with pytest.raises(TypeError):
        Client(logger="something")


def test_real_torrent_attr_type(tr_client: Client, fake_hash_factory):
    with open("tests/fixtures/iso.torrent", "rb") as f:
        tr_client.add_torrent(f)
    for torrent in tr_client.get_torrents():
        assert isinstance(torrent.id, int)
        assert isinstance(torrent.name, str)


def test_real_torrent_get_files(tr_client: Client):
    with open("tests/fixtures/iso.torrent", "rb") as f:
        tr_client.add_torrent(f)
    assert len(tr_client.get_torrents()) == 1, "transmission should has at least 1 task"
    for torrent in tr_client.get_torrents():
        for file in torrent.files():
            assert isinstance(file, File)


def test_check_rpc_version_for_args(mock_version):
    m = mock.Mock(return_value={"hello": "world"})
    with mock.patch("transmission_rpc.client.Client._request", m):
        c = Client()
        c.protocol_version = 7
        with pytest.raises(ValueError):
            c.add_torrent(magnet_url, cookies="")


def test_parse_server_version():
    m = mock.Mock(
        return_value=json.dumps(
            {
                "arguments": {"version": "2.80 (hello)", "rpc-version": 14},
                "result": "success",
            }
        )
    )
    with mock.patch("transmission_rpc.client.Client._http_query", m):
        c = Client()
        assert c.server_version == (2, 80, "hello")
