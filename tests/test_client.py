import os
import json
import time
import base64
import os.path
import pathlib
from unittest import mock
from urllib.parse import urljoin

import yarl
import pytest
from typing_extensions import Literal

from transmission_rpc.error import TransmissionAuthError, TransmissionVersionError
from transmission_rpc.utils import _try_read_torrent
from transmission_rpc.client import Client, ensure_location_str
from transmission_rpc.lib_types import File


@pytest.mark.parametrize(
    ("protocol", "username", "password", "host", "port", "path"),
    [
        (
            "https",
            "a+2da/s a?s=d$",
            "a@as +@45/:&*^",
            "127.0.0.1",
            2333,
            "/transmission/",
        ),
        (
            "http",
            "/",
            None,
            "127.0.0.1",
            2333,
            "/transmission/",
        ),
    ],
)
def test_client_parse_url(protocol: Literal["http", "https"], username, password, host, port, path):
    with mock.patch("transmission_rpc.client.Client._request"):
        client = Client(
            protocol=protocol,
            username=username,
            password=password,
            host=host,
            port=port,
            path=path,
        )
        u = str(
            yarl.URL.build(
                scheme=protocol,
                user=username,
                password=password,
                host=host,
                port=port,
                path=urljoin(path, "rpc"),
            )
        )

        assert client.url == u


def hash_to_magnet(h):
    return f"magnet:?xt=urn:btih:{h}"


torrent_hash = "e84213a794f3ccd890382a54a64ca68b7e925433"
magnet_url = f"magnet:?xt=urn:btih:{torrent_hash}"
torrent_hash2 = "9fc20b9e98ea98b4a35e6223041a5ef94ea27809"
torrent_url = "https://releases.ubuntu.com/20.04/ubuntu-20.04-desktop-amd64.iso.torrent"


def test_client_add_kwargs():
    m = mock.Mock(return_value={"hello": "workd"})
    with mock.patch("transmission_rpc.client.Client._request", m):
        c = Client()
        c.protocol_version = 15
        c.add_torrent(
            torrent_url,
            download_dir="dd",
            files_unwanted=[1, 2],
            files_wanted=[3, 4],
            paused=False,
            peer_limit=5,
            priority_high=[6],
            priority_low=[7],
            priority_normal=[8],
            cookies="coo",
            bandwidthPriority=4,
        )
    m.assert_called_with(
        "torrent-add",
        {
            "filename": torrent_url,
            "download-dir": "dd",
            "files-unwanted": [1, 2],
            "files-wanted": [3, 4],
            "paused": False,
            "peer-limit": 5,
            "priority-high": [6],
            "priority-low": [7],
            "priority-normal": [8],
            "cookies": "coo",
            "bandwidthPriority": 4,
        },
        timeout=None,
    )


def test_client_add_url():
    assert _try_read_torrent(torrent_url) is None, "handle http URL with daemon"


def test_client_add_magnet():
    assert _try_read_torrent(magnet_url) is None, "handle magnet URL with daemon"


def test_client_add_base64_raw_data():
    with open("tests/fixtures/iso.torrent", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    with pytest.warns(DeprecationWarning):
        assert _try_read_torrent(b64) == b64, "should skip handle base64 content"


def test_client_add_pathlib_path():
    p = pathlib.Path("tests/fixtures/iso.torrent")
    b64 = base64.b64encode(p.read_bytes()).decode()
    assert _try_read_torrent(p) == b64, "should skip handle base64 content"


def test_client_add_file_protocol():
    with open("tests/fixtures/iso.torrent", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    p = pathlib.Path("tests/fixtures/iso.torrent").absolute()
    with pytest.warns(DeprecationWarning):
        assert _try_read_torrent(f"file://{p}") == b64, "should skip handle base64 content"


def test_client_add_read_file_in_base64():
    with open("tests/fixtures/iso.torrent", "rb") as f:
        content = f.read()
        f.seek(0)
        data = _try_read_torrent(f)

    assert base64.b64encode(content).decode() == data, "should base64 encode torrent file"


def test_client_add_torrent_bytes():
    with open("tests/fixtures/iso.torrent", "rb") as f:
        content = f.read()
    data = _try_read_torrent(content)
    assert base64.b64encode(content).decode() == data, "should base64 bytes"


def test_real_add_magnet(tr_client: Client):
    tr_client.add_torrent(magnet_url)
    assert len(tr_client.get_torrents()) == 1, "transmission should has at least 1 task"


def test_real_add_torrent_fd(tr_client: Client):
    with open("tests/fixtures/iso.torrent", "rb") as f:
        tr_client.add_torrent(f)
    assert len(tr_client.get_torrents()) == 1, "transmission should has at least 1 task"


def test_real_add_torrent_base64(tr_client: Client):
    with open("tests/fixtures/iso.torrent", "rb") as f:
        with pytest.warns(DeprecationWarning, match="base64"):
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
    with pytest.warns(DeprecationWarning):
        tr_client.add_torrent("file://" + fs)
    assert len(tr_client.get_torrents()) == 1, "transmission should has at least 1 task"


def test_real_add_torrent_http(tr_client: Client):
    tr_client.add_torrent("https://github.com/Trim21/transmission-rpc/raw/master/tests/fixtures/iso.torrent")
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


def test_real_torrent_attr_type(tr_client: Client):
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


def test_check_rpc_version_for_args():
    m = mock.Mock(return_value={"hello": "world"})
    with mock.patch("transmission_rpc.client.Client._request", m):
        c = Client()
        c.protocol_version = 7
        with pytest.raises(
            TransmissionVersionError,
            match='Method "torrent-add" Argument "cookies" does not exist in version 7',
        ):
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


def test_warn_deprecated():
    m = mock.Mock(
        return_value=json.dumps(
            {
                "arguments": {"version": "2.10 (hello)", "rpc-version": 10},
                "result": "success",
            }
        )
    )
    with mock.patch("transmission_rpc.client.Client._http_query", m):
        with pytest.warns(PendingDeprecationWarning):
            Client()


@pytest.mark.parametrize(
    "status_code",
    [401, 403],
)
def test_raise_unauthorized(status_code):
    m = mock.Mock(return_value=mock.Mock(status_code=status_code))
    with mock.patch("requests.Session.post", m), pytest.raises(TransmissionAuthError):
        Client()


def test_ensure_location_str_relative():
    with pytest.warns(DeprecationWarning, match="absolute"):
        ensure_location_str(pathlib.Path("."))


def test_ensure_location_str_absolute():
    ensure_location_str(pathlib.Path(".").absolute())
