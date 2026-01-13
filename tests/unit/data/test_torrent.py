import calendar
import datetime
import time
from typing import Any

import pytest

import transmission_rpc
import transmission_rpc.constants
import transmission_rpc.utils
from tests.util import check_properties
from transmission_rpc.torrent import FileStat, Status, Torrent, get_status


def assert_property_exception(exception: type[Exception], ob: Any, prop: str) -> None:
    """Helper to assert that accessing a property raises a specific exception."""
    with pytest.raises(exception):
        getattr(ob, prop)


def test_torrent_missing_optional_fields() -> None:
    """Verify Torrent initialization handles missing optional fields (priorities, wanted) gracefully."""
    # files present but priorities/wanted missing
    fields = {
        "id": 1,
        "files": [{"length": 1, "name": "f", "bytesCompleted": 0}],
    }
    t = Torrent(fields=fields)
    assert len(t.get_files()) == 1
    assert t.get_files()[0].priority is None
    assert t.get_files()[0].selected is None


def test_torrent_status_and_idle_mode_mapping() -> None:
    """Verify `seed_idle_mode` enum conversion and `status` property string mapping."""
    fields = {
        "id": 1,
        "seedIdleMode": 0,  # global
        "status": 4,  # downloading
    }
    t = Torrent(fields=fields)
    assert t.seed_idle_mode.value == 0
    # Use public API 'status' which returns a Status(str) enum
    assert t.status == "downloading"


def test_torrent_defaults_and_basic_props() -> None:
    """Verify default values, basic properties, and error handling for missing fields."""
    fields = {
        "id": 1,
        "file-count": 5,
        "primary-mime-type": "text/plain",
        "hashString": "hash",
        "files": [{"length": 100, "name": "f1", "bytesCompleted": 100}],
        "pieces": "",
    }
    t = Torrent(fields=fields)

    # Basic properties
    assert t.file_count == 5
    assert t.primary_mime_type == "text/plain"

    # Deprecated into_hash
    with pytest.warns(DeprecationWarning, match="typo"):
        assert t.into_hash == "hash"

    # get_files defaults (when priorities/wanted are missing)
    files = t.get_files()
    assert len(files) == 1
    assert files[0].priority is None
    assert files[0].selected is None

    # pieces
    assert t.pieces is not None

    # Init missing id
    with pytest.raises(ValueError, match="requires field 'id'"):
        Torrent(fields={})

    # Minimal fields (asserting exceptions)
    torrent_minimal = transmission_rpc.Torrent(fields={"id": 42})
    assert torrent_minimal.id == 42
    assert_property_exception(KeyError, torrent_minimal, "status")
    assert_property_exception(KeyError, torrent_minimal, "progress")
    assert_property_exception(KeyError, torrent_minimal, "ratio")
    assert_property_exception(KeyError, torrent_minimal, "eta")
    assert_property_exception(KeyError, torrent_minimal, "activity_date")
    assert_property_exception(KeyError, torrent_minimal, "added_date")
    assert_property_exception(KeyError, torrent_minimal, "start_date")
    assert_property_exception(KeyError, torrent_minimal, "done_date")

    with pytest.raises(KeyError):
        torrent_minimal.format_eta()
    with pytest.raises(KeyError):
        torrent_minimal.get_files()


def test_torrent_progress_and_availability() -> None:
    """Verify calculations for progress, availability, and ratio, including division by zero checks."""
    fields = {
        "id": 1,
        "sizeWhenDone": 100,
        "leftUntilDone": 50,
        "uploadRatio": 1.0,
        "percentDone": 0.5,
        "totalSize": 100,
        "fileStats": [{"bytesCompleted": 100, "wanted": True, "priority": 1}],
        "desiredAvailable": 0,
    }
    t = Torrent(fields=fields)

    # available
    # bytes_done = 100
    # bytes_avail = 0 + 100 = 100
    # ratio = 100 / 100 = 1.0 => 100.0
    assert t.available == 100.0

    # Ratio
    assert t.ratio == 1.0

    # Progress ZeroDivisionError check
    # Create new fields dict with percentDone missing to trigger calculation
    # and sizeWhenDone/leftUntilDone as 0
    fields_zero = {
        "id": 1,
        "sizeWhenDone": 0,
        "leftUntilDone": 0,
    }
    t_zero = Torrent(fields=fields_zero)
    # Should catch ZeroDivisionError and return 0.0
    assert t_zero.progress == 0.0


def test_torrent_representation() -> None:
    """Verify string representations, ETA formatting, and date handling."""
    fields = {
        "id": 1,
        "name": "test",
        "hashString": "hash",
        "eta": -1,
    }
    t = Torrent(fields=fields)

    # __str__ and __repr__
    assert str(t) == "<transmission_rpc.Torrent 'test'>"
    assert repr(t) == "<transmission_rpc.Torrent hashString='hash'>"

    # format_eta edge cases
    assert t.format_eta() == "not available"

    fields_unknown = fields.copy()
    fields_unknown["eta"] = -2
    t_unknown = Torrent(fields=fields_unknown)
    assert t_unknown.format_eta() == "unknown"

    fields_valid = fields.copy()
    fields_valid["eta"] = 3600
    t_valid = Torrent(fields=fields_valid)
    assert t_valid.format_eta() == "0 01:00:00"

    # Date fields
    data_full = {
        "id": 1,
        "status": 4,
        "sizeWhenDone": 1000,
        "leftUntilDone": 500,
        "uploadedEver": 1000,
        "downloadedEver": 2000,
        "uploadRatio": 0.5,
        "eta": 3600,
        "percentDone": 0.5,
        "activityDate": calendar.timegm((2008, 12, 11, 11, 15, 30, 0, 0, -1)),
        "addedDate": calendar.timegm((2008, 12, 11, 8, 5, 10, 0, 0, -1)),
        "startDate": calendar.timegm((2008, 12, 11, 9, 10, 5, 0, 0, -1)),
        "doneDate": calendar.timegm((2008, 12, 11, 10, 0, 15, 0, 0, -1)),
    }

    torrent_dates = transmission_rpc.Torrent(fields=data_full)
    assert torrent_dates.id == 1
    assert torrent_dates.activity_date == datetime.datetime(2008, 12, 11, 11, 15, 30, tzinfo=datetime.timezone.utc)
    assert torrent_dates.added_date == datetime.datetime(2008, 12, 11, 8, 5, 10, tzinfo=datetime.timezone.utc)
    assert torrent_dates.start_date == datetime.datetime(2008, 12, 11, 9, 10, 5, tzinfo=datetime.timezone.utc)
    assert torrent_dates.done_date == datetime.datetime(2008, 12, 11, 10, 0, 15, tzinfo=datetime.timezone.utc)
    assert torrent_dates.format_eta() == transmission_rpc.utils.format_timedelta(torrent_dates.eta)

    # Zero date check
    data_zero_date = {
        "id": 1,
        "activityDate": time.mktime((2008, 12, 11, 11, 15, 30, 0, 0, -1)),
        "addedDate": time.mktime((2008, 12, 11, 8, 5, 10, 0, 0, -1)),
        "startDate": time.mktime((2008, 12, 11, 9, 10, 5, 0, 0, -1)),
        "doneDate": 0,
    }

    torrent_zero = transmission_rpc.Torrent(fields=data_zero_date)
    assert torrent_zero.done_date is None


def test_torrent_properties_access() -> None:
    """Verify that all properties of a Torrent instance can be accessed without error."""
    t = Torrent(fields={"id": 1})
    check_properties(Torrent, t)


def test_file_stat_properties_access() -> None:
    """Verify that all properties of a FileStat instance can be accessed without error."""
    f = FileStat(fields={})
    check_properties(FileStat, f)


def test_status_mapping() -> None:
    """Verify that Status objects correctly report boolean states (e.g., stopped, checking) and string representation."""
    s = Status("checking")
    assert s.checking
    assert not s.stopped

    s = Status("check pending")
    assert s.check_pending

    s = Status("downloading")
    assert s.downloading

    s = Status("download pending")
    assert s.download_pending

    s = Status("seeding")
    assert s.seeding

    s = Status("seed pending")
    assert s.seed_pending

    s = Status("stopped")
    assert s.stopped is True
    assert s.check_pending is False
    assert str(s) == "stopped"

    check_properties(Status, s)


def test_eta_and_date_handling() -> None:
    """Verify formatting of ETA, handling of idle ETA, and conversion of epoch timestamps to datetime objects."""
    fields = {
        "id": 1,
        "eta": -1,
        "etaIdle": -1,
        "pieces": "AA==",  # base64 for 0x00
        "fileStats": [],
        "files": [],
        "priorities": [],
        "wanted": [],
        "peers": [],
        "trackers": [],
        "trackerStats": [],
        "trackerList": "",
        "status": 0,
        "activityDate": 0,
        "addedDate": 0,
        "startDate": 0,
        "doneDate": 0,
    }
    t = Torrent(fields=fields)
    assert t.format_eta() == "not available"
    assert t.eta is None
    assert t.eta_idle is None
    assert t.done_date is None

    fields_unknown = fields.copy()
    fields_unknown["eta"] = -2
    t = Torrent(fields=fields_unknown)
    assert t.format_eta() == "unknown"

    fields_valid = fields.copy()
    fields_valid["eta"] = 3600
    fields_valid["etaIdle"] = 60
    fields_valid["doneDate"] = 1000000000
    t = Torrent(fields=fields_valid)
    assert str(t.eta) == "1:00:00"
    assert str(t.eta_idle) == "0:01:00"
    assert t.done_date is not None


def test_status_unknown() -> None:
    """Verify that `get_status` returns a formatted unknown string for invalid status codes."""
    assert get_status(999) == "unknown status 999"


def test_activity_date_handles_zero_value() -> None:
    """
    Verify that a Torrent object correctly handles the 'activityDate' field being 0 (non-active).
    """
    data = {
        "id": 1,
        "activityDate": 0,
    }

    torrent = transmission_rpc.Torrent(fields=data)
    assert torrent.activity_date
