from unittest import mock

from transmission_rpc.session import Session


def test_session_init():
    fields = {"a-b": 1}
    s = Session(fields=fields)

    assert dict(s.items()) == {"a_b": 1}


def test_session_get_attribute():
    fields = {"a-b": 1}
    s = Session(fields=fields)
    assert s.a_b == 1


def test_session_set_attribute():
    m = mock.Mock()
    s = Session(m)
    s.download_dir = "download - dir"
    assert s.download_dir == "download - dir"
    m.set_session.assert_called_with(download_dir="download - dir")


def test_session_update():
    m = mock.Mock()
    s = Session(m)
    assert dict(s.items()) == {}

    data = {"a": 1, "b": "2", "c": 3}
    s.update(data)
    m.set_session.assert_called_with(**data)
    assert dict(s.items()) == data
