# SPDX-License-Identifier: Apache-2.0
"""Tool-call cassette layer for replay-safety (FR-21, FR-28).

Per requirements §amendment-6: ``(tool_name, args_hash) -> result`` map. The
cassette is checkpoint-resident -- the engine serializes it under
``state_snapshot["__cassette_tools"]`` so re-hydrating a checkpoint restores
every tool stub.

The hashing strategy is canonical-JSON (sorted keys, no whitespace) hashed
with SHA-256. JSON-serializability is the same constraint Harbor already
imposes on tool args (jsonschema-validated input), so this is consistent
with the rest of the data path.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

__all__ = [
    "ToolCallCassette",
    "args_hash",
]


def args_hash(args: dict[str, Any]) -> str:
    """Return a stable SHA-256 hash of ``args`` (canonical JSON, sorted keys)."""
    canonical = json.dumps(args, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ToolCallCassette:
    """In-memory ``(tool_name, args_hash) -> result`` cassette store.

    Implements the :class:`harbor.runtime.tool_exec.CassetteStore` Protocol
    (structural -- no inheritance needed). Serializes to/from a plain dict
    for checkpoint persistence under ``state_snapshot["__cassette_tools"]``.
    """

    __slots__ = ("_entries",)

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], dict[str, Any]] = {}

    def record(
        self,
        tool_id: str,
        args: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Persist ``result`` for the ``(tool_id, args)`` pair."""
        self._entries[(tool_id, args_hash(args))] = dict(result)

    def get(
        self,
        tool_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Return the recorded result or ``None`` on cache miss."""
        recorded = self._entries.get((tool_id, args_hash(args)))
        return None if recorded is None else dict(recorded)

    def to_state(self) -> list[dict[str, Any]]:
        """Serialize the cassette for checkpoint persistence.

        Emits a list of ``{tool_id, args_hash, result}`` records -- a
        list (not a dict) because JSON object keys cannot be tuples.
        """
        return [
            {"tool_id": tid, "args_hash": ahash, "result": dict(result)}
            for (tid, ahash), result in self._entries.items()
        ]

    @classmethod
    def from_state(cls, state: list[dict[str, Any]]) -> ToolCallCassette:
        """Restore a cassette from :meth:`to_state` output."""
        cassette = cls()
        for entry in state:
            tid = entry["tool_id"]
            ahash = entry["args_hash"]
            result = entry["result"]
            cassette._entries[(tid, ahash)] = dict(result)
        return cassette
