from collections.abc import Iterable

import pytest

from transmission_rpc._tracker_list import parse_tracker_list, serialize_tracker_list


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", []),
        ("https://tracker.example/announce", [["https://tracker.example/announce"]]),
        (
            "https://a.example/announce\nhttps://b.example/announce\n\nhttps://backup.example/announce\n",
            [
                ["https://a.example/announce", "https://b.example/announce"],
                ["https://backup.example/announce"],
            ],
        ),
        (
            "\r\n  https://a.example/announce  \r\n\r\n\r\nhttps://backup.example/announce\r\n\r\n",
            [["https://a.example/announce"], ["https://backup.example/announce"]],
        ),
    ],
)
def test_parse_tracker_list(raw: str, expected: list[list[str]]) -> None:
    assert parse_tracker_list(raw) == expected


@pytest.mark.parametrize(
    ("tracker_list", "expected"),
    [
        ([], ""),
        ([["  https://tracker.example/announce  "]], "https://tracker.example/announce"),
        (
            (
                ("https://a.example/announce", "https://b.example/announce"),
                ("https://backup.example/announce",),
            ),
            "https://a.example/announce\nhttps://b.example/announce\n\nhttps://backup.example/announce",
        ),
    ],
)
def test_serialize_tracker_list(tracker_list: Iterable[Iterable[str]], expected: str) -> None:
    assert serialize_tracker_list(tracker_list) == expected


def test_serialize_tracker_list_accepts_generators() -> None:
    tiers = ((tracker for tracker in tier) for tier in (("tracker-a", "tracker-b"), ("tracker-c",)))

    assert serialize_tracker_list(tiers) == "tracker-a\ntracker-b\n\ntracker-c"


@pytest.mark.parametrize(
    ("tracker_list", "exception", "message"),
    [
        ("https://tracker.example/announce", TypeError, "iterable of tracker tiers"),
        (["https://tracker.example/announce"], TypeError, "contain tracker tiers"),
        ([1], TypeError, "each tracker tier must be an iterable"),
        ([[1]], TypeError, "tracker URLs must be strings"),
        ([[]], ValueError, "tracker tiers must not be empty"),
        ([[""]], ValueError, "tracker URLs must not be empty"),
        ([["  "]], ValueError, "tracker URLs must not be empty"),
        ([["https://tracker.example/announce\nhttps://other.example/announce"]], ValueError, "contain CR or LF"),
        ([["https://tracker.example/announce\r"]], ValueError, "contain CR or LF"),
    ],
)
def test_serialize_tracker_list_rejects_invalid_values(
    tracker_list: object, exception: type[Exception], message: str
) -> None:
    with pytest.raises(exception, match=message):
        serialize_tracker_list(tracker_list)  # type: ignore[arg-type]
