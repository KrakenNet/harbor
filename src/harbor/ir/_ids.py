# SPDX-License-Identifier: Apache-2.0
"""Stable ID generation: UUIDv7 run/checkpoint IDs, BLAKE2b fact hashes, slug helpers.

Provides the canonical ID utilities consumed by the IR layer (FR-30, FR-31):

* :func:`new_run_id` and :func:`new_checkpoint_id` -- UUIDv7 strings (sortable).
* :func:`fact_content_hash` -- 32-char BLAKE2b digest over canonical JSON.
* :func:`_slug` -- conservative ``[a-zA-Z0-9]+ -> '-'`` slugifier (max 24).
* :func:`autogen_node_ids`, :func:`autogen_rule_ids`, :func:`autogen_pack_ids` --
  fill missing ``id`` fields with slug-of-name; suffix collisions ``-2``, ``-3``.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

import uuid_utils

__all__ = [
    "_slug",
    "autogen_node_ids",
    "autogen_pack_ids",
    "autogen_rule_ids",
    "fact_content_hash",
    "new_checkpoint_id",
    "new_run_id",
]

_SLUG_RE = re.compile(r"[^a-zA-Z0-9]+")
_SLUG_MAX = 24


def new_run_id() -> str:
    """Return a fresh UUIDv7 string for a run (FR-30)."""
    return str(uuid_utils.uuid7())


def new_checkpoint_id() -> str:
    """Return a fresh UUIDv7 string for a checkpoint (FR-30)."""
    return str(uuid_utils.uuid7())


def fact_content_hash(fact: dict[str, Any]) -> str:
    """Return a 32-char BLAKE2b hex digest over the fact's canonical JSON (FR-31)."""
    canonical = json.dumps(fact, sort_keys=True, separators=(",", ":"))
    return hashlib.blake2b(canonical.encode("utf-8"), digest_size=16).hexdigest()


def _slug(text: str) -> str:
    """Lowercase ``text`` and collapse non-alphanumerics to ``-`` (max 24 chars)."""
    s = _SLUG_RE.sub("-", text).strip("-").lower()
    return s[:_SLUG_MAX]


def _autogen_ids(items: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    """Fill missing ``id`` on items; slug-of-name with ``-2``/``-3`` collision suffixes.

    ``kind`` is reserved for future per-kind behaviour (e.g. namespace prefixes);
    the POC implementation uses uniform slug-of-name semantics.
    """
    del kind  # unused in POC; reserved for Phase 2 namespace prefixes
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in items:
        item = dict(raw)
        if item.get("id"):
            seen.add(str(item["id"]))
        out.append(item)
    for item in out:
        if item.get("id"):
            continue
        base = _slug(str(item.get("name", "") or next(iter(item.values()), "")))
        candidate = base
        n = 2
        while candidate in seen or not candidate:
            candidate = f"{base}-{n}" if base else f"item-{n}"
            n += 1
        item["id"] = candidate
        seen.add(candidate)
    return out


def autogen_node_ids(items: list[dict[str, Any]], kind: str = "node") -> list[dict[str, Any]]:
    """Autogen IDs for node items (FR-30)."""
    return _autogen_ids(items, kind)


def autogen_rule_ids(items: list[dict[str, Any]], kind: str = "rule") -> list[dict[str, Any]]:
    """Autogen IDs for rule items (FR-30)."""
    return _autogen_ids(items, kind)


def autogen_pack_ids(items: list[dict[str, Any]], kind: str = "pack") -> list[dict[str, Any]]:
    """Autogen IDs for pack items (FR-30)."""
    return _autogen_ids(items, kind)
