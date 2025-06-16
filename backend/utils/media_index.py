"""Utility helpers for reading/writing the media index (media/index.json).

This consolidates all access in one place so multiple endpoints and the
DisplayPlayer can share a single canonical schema:

{
    "media": {
        "<slug>": { ...metadata... },
        ...
    },
    "loop": ["slug1", "slug2", ...],
    "active": "slug1",            # optional currently-playing slug
    "last_updated": 1700000000
}
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from utils.logger import get_logger

LOGGER = get_logger("media_index")

MEDIA_INDEX_PATH = Path("media/index.json")
_MEDIA_DEFAULT = {"media": {}, "loop": [], "active": None, "last_updated": None}


def _read_raw() -> Dict:
    if MEDIA_INDEX_PATH.exists():
        try:
            with open(MEDIA_INDEX_PATH, "r") as f:
                return json.load(f)
        except Exception as exc:
            LOGGER.error("Failed to read media index: %s", exc)
    return _MEDIA_DEFAULT.copy()


def _write_raw(data: Dict) -> None:
    try:
        MEDIA_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        data["last_updated"] = int(time.time())
        with open(MEDIA_INDEX_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as exc:
        LOGGER.error("Failed to write media index: %s", exc)


# Public helpers -----------------------------------------------------------


def list_media() -> List[Dict]:
    """Return all media objects (order not guaranteed)."""
    return list(_read_raw().get("media", {}).values())


def list_loop() -> List[str]:
    """Return the current loop slug list."""
    return _read_raw().get("loop", [])


def get_active() -> Optional[str]:
    return _read_raw().get("active")


# Mutations ----------------------------------------------------------------


def add_media(meta: Dict, make_active: bool = True) -> None:
    slug = meta.get("slug")
    if not slug:
        raise ValueError("Metadata missing slug")

    data = _read_raw()
    media_dict = data.setdefault("media", {})
    media_dict[slug] = meta

    # Append to loop by default
    if make_active:
        loop = data.setdefault("loop", [])
        if slug not in loop:
            loop.append(slug)
        # If first media, mark active
        if data.get("active") is None:
            data["active"] = slug

    _write_raw(data)


def remove_media(slug: str) -> None:
    data = _read_raw()
    media_dict = data.setdefault("media", {})
    media_dict.pop(slug, None)
    # Also remove from loop list if present
    loop = data.setdefault("loop", [])
    data["loop"] = [s for s in loop if s != slug]
    if data.get("active") == slug:
        data["active"] = data["loop"][0] if data["loop"] else None
    _write_raw(data)


def add_to_loop(slug: str) -> None:
    data = _read_raw()
    if slug not in data.get("media", {}):
        raise KeyError("Unknown media slug")
    loop = data.setdefault("loop", [])
    if slug not in loop:
        loop.append(slug)
        _write_raw(data)


def remove_from_loop(slug: str) -> None:
    data = _read_raw()
    loop = data.setdefault("loop", [])
    if slug in loop:
        loop = [s for s in loop if s != slug]
        data["loop"] = loop
        if data.get("active") == slug:
            data["active"] = loop[0] if loop else None
        _write_raw(data)


def reorder_loop(new_order: List[str]) -> None:
    data = _read_raw()
    media_slugs = set(data.get("media", {}).keys())
    data["loop"] = [s for s in new_order if s in media_slugs]
    _write_raw(data)


# Convenience: update "active" pointer (no validation of slug order)

def set_active(slug: Optional[str]) -> None:
    data = _read_raw()
    if slug is not None and slug not in data.get("media", {}):
        raise KeyError("Unknown media slug")
    data["active"] = slug
    _write_raw(data) 