# 2008-12, Erik Svensson <erik.public@gmail.com>
# Copyright (c) 2020 Trim21 <i@trim21.me>
# Licensed under the MIT license.
import time
import datetime

import pytest

import transmission_rpc
import transmission_rpc.utils
import transmission_rpc.constants
from transmission_rpc.torrent import Status


def test_initial():
    with pytest.raises(ValueError, match="Torrent requires an id"):
        transmission_rpc.Torrent(None, {})
    transmission_rpc.Torrent(None, {"id": 42})


def assert_property_exception(exception, ob, prop):
    with pytest.raises(exception):
        getattr(ob, prop)


def test_get_name_string():
    torrent = transmission_rpc.Torrent(None, {"id": 42, "name": "we"})
    name = torrent._get_name_string()  # pylint: disable=W0212
    assert isinstance(name, str)


def test_attributes():
    torrent = transmission_rpc.Torrent(None, {"id": 42})
    assert hasattr(torrent, "id")
    assert torrent.id == 42
    assert_property_exception(KeyError, torrent, "status")
    assert_property_exception(KeyError, torrent, "progress")
    assert_property_exception(KeyError, torrent, "ratio")
    assert_property_exception(KeyError, torrent, "eta")
    assert_property_exception(KeyError, torrent, "date_active")
    assert_property_exception(KeyError, torrent, "date_added")
    assert_property_exception(KeyError, torrent, "date_started")
    assert_property_exception(KeyError, torrent, "date_done")

    with pytest.raises(KeyError):
        torrent.format_eta()
    assert torrent.files() == []

    data = {
        "id": 1,
        "status": 4,
        "sizeWhenDone": 1000,
        "leftUntilDone": 500,
        "uploadedEver": 1000,
        "downloadedEver": 2000,
        "uploadRatio": 0.5,
        "eta": 3600,
        "percentDone": 0.5,
        "activityDate": time.mktime((2008, 12, 11, 11, 15, 30, 0, 0, -1)),
        "addedDate": time.mktime((2008, 12, 11, 8, 5, 10, 0, 0, -1)),
        "startDate": time.mktime((2008, 12, 11, 9, 10, 5, 0, 0, -1)),
        "doneDate": time.mktime((2008, 12, 11, 10, 0, 15, 0, 0, -1)),
    }

    torrent = transmission_rpc.Torrent(None, data)
    assert torrent.id == 1
    assert torrent.leftUntilDone == 500
    assert torrent.status == "downloading"
    assert torrent.progress == 50.0
    assert torrent.ratio == 0.5
    assert torrent.eta == datetime.timedelta(seconds=3600)
    assert torrent.date_active == datetime.datetime(2008, 12, 11, 11, 15, 30)
    assert torrent.date_added == datetime.datetime(2008, 12, 11, 8, 5, 10)
    assert torrent.date_started == datetime.datetime(2008, 12, 11, 9, 10, 5)
    assert torrent.date_done == datetime.datetime(2008, 12, 11, 10, 0, 15)

    assert torrent.format_eta() == transmission_rpc.utils.format_timedelta(torrent.eta)

    torrent = transmission_rpc.Torrent(None, {"id": 42, "eta": -1})
    assert_property_exception(ValueError, torrent, "eta")

    data = {
        "id": 1,
        "status": 4,
        "sizeWhenDone": 1000,
        "leftUntilDone": 500,
        "uploadedEver": 1000,
        "downloadedEver": 2000,
        "uploadRatio": 0.5,
        "eta": 3600,
        "activityDate": time.mktime((2008, 12, 11, 11, 15, 30, 0, 0, -1)),
        "addedDate": time.mktime((2008, 12, 11, 8, 5, 10, 0, 0, -1)),
        "startDate": time.mktime((2008, 12, 11, 9, 10, 5, 0, 0, -1)),
        "doneDate": 0,
    }

    torrent = transmission_rpc.Torrent(None, data)
    assert torrent.date_done is None


def test_status():
    assert Status("downloading").downloading
    assert not Status("downloading").download_pending
    assert Status("download pending").download_pending
    assert Status("some thing") == "some thing"
