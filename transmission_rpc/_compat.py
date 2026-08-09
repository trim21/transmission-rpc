"""Compatibility helpers for JSON-RPC 2.0 and Transmission's legacy RPC."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from transmission_rpc._compat_table import SNAKE_TO_LEGACY

_EXTRA_LEGACY_NAMES: dict[str, tuple[str, ...]] = {
    # api-compat.cc special case: camelCase for torrent-get/set, kebab-case elsewhere.
    "download_dir": ("downloadDir",),
}

LEGACY_TO_SNAKE = {
    legacy: snake
    for snake, names in SNAKE_TO_LEGACY.items()
    for legacy in (*names, *_EXTRA_LEGACY_NAMES.get(snake, ()))
}

_CAMEL_SPLIT_1 = re.compile(r"(.)([A-Z][a-z]+)")
_CAMEL_SPLIT_2 = re.compile(r"([a-z0-9])([A-Z])")


def to_snake(name: str) -> str:
    """Convert a legacy (kebab-case/camelCase) field name to snake_case."""
    if name in LEGACY_TO_SNAKE:
        return LEGACY_TO_SNAKE[name]
    s = name.replace("-", "_")
    s = _CAMEL_SPLIT_1.sub(r"\1_\2", s)
    s = _CAMEL_SPLIT_2.sub(r"\1_\2", s)
    return s.lower()


def legacy_name(snake: str, *, torrent: bool) -> str:
    """Convert a snake_case field name to its legacy variant for a request.

    `torrent` must be true for torrent-get/set, where ``download_dir``
    historically used camelCase instead of kebab-case.
    """
    snake = to_snake(snake)
    if torrent and snake == "download_dir":
        return "downloadDir"
    variants = SNAKE_TO_LEGACY.get(snake)
    if variants is None:
        return snake  # not a known RPC field; pass through unchanged
    return variants[0]


def field_names(snake: str) -> tuple[str, ...]:
    """Return the canonical field name followed by every legacy alias."""
    return (snake, *SNAKE_TO_LEGACY.get(snake, ()), *_EXTRA_LEGACY_NAMES.get(snake, ()))


def convert_jsonrpc_args(args: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize request arguments supplied with legacy spellings to JSON-RPC 2.0."""
    out: dict[str, Any] = {}
    for key, value in args.items():
        converted = to_snake(key)
        converted_value = value
        if converted == "fields" and isinstance(value, list):
            converted_value = [to_snake(item) if isinstance(item, str) else item for item in value]
        elif converted == "ids" and value == "recently-active":
            converted_value = "recently_active"
        elif converted == "encryption" and value == "tolerated":
            converted_value = "allowed"
        out[converted] = converted_value
    return out


def convert_request_args(args: Mapping[str, Any], *, torrent: bool) -> dict[str, Any]:
    """Convert snake_case request argument names to their legacy variants.

    The ``fields`` argument holds field names and the ``ids`` argument may hold
    the special ``recently_active`` value, so those values are converted too.
    """
    out: dict[str, Any] = {}
    for key, value in args.items():
        converted = legacy_name(key, torrent=torrent)
        if key == "fields" and isinstance(value, list):
            out[converted] = [legacy_name(item, torrent=torrent) if isinstance(item, str) else item for item in value]
        elif key == "ids" and isinstance(value, str):
            out[converted] = legacy_name(value, torrent=torrent)
        elif key == "encryption" and value == "allowed":
            out[converted] = "tolerated"
        else:
            out[converted] = value
    return out
