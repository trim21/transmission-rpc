from transmission_rpc.session import Session


def test_session_init():
    fields = {"a-b": 1}
    s = Session(fields)

    assert dict(s.items()) == {"a_b": 1}


def test_session_get_attribute():
    fields = {"a-b": 1}
    s = Session(fields)
    assert s._get("a_b") == 1
    assert s._fields["a_b"] == 1


def test_session_set_attribute():
    s = Session()
    download_dir = "download - dir"
    assert s.download_dir == download_dir
    m.set_session.assert_called_once_with(download_dir=download_dir)
