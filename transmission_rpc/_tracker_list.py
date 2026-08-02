from __future__ import annotations

from collections.abc import Iterable


def parse_tracker_list(value: str) -> list[list[str]]:
    """Parse Transmission's tracker-list wire format into tracker tiers."""
    tiers: list[list[str]] = []
    current_tier: list[str] = []

    for line in value.split("\n"):
        tracker = line.removesuffix("\r").strip()
        if tracker:
            current_tier.append(tracker)
        elif current_tier:
            tiers.append(current_tier)
            current_tier = []

    if current_tier:
        tiers.append(current_tier)

    return tiers


def serialize_tracker_list(tracker_list: Iterable[Iterable[str]]) -> str:
    """Serialize tracker tiers into Transmission's tracker-list wire format."""
    if isinstance(tracker_list, str):
        raise TypeError("tracker_list must be an iterable of tracker tiers, not a string")

    serialized_tiers: list[str] = []

    for tier in tracker_list:
        if isinstance(tier, str):
            raise TypeError("tracker_list must contain tracker tiers, not tracker URL strings")
        if not isinstance(tier, Iterable):
            raise TypeError("each tracker tier must be an iterable of tracker URLs")

        trackers = [_normalize_tracker_url(tracker) for tracker in tier]
        if not trackers:
            raise ValueError("tracker tiers must not be empty")

        serialized_tiers.append("\n".join(trackers))

    return "\n\n".join(serialized_tiers)


def _normalize_tracker_url(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("tracker URLs must be strings")
    if "\r" in value or "\n" in value:
        raise ValueError("tracker URLs must not contain CR or LF")

    value = value.strip()
    if not value:
        raise ValueError("tracker URLs must not be empty")

    return value
