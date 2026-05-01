# SPDX-License-Identifier: Apache-2.0
"""Append-only JSONL audit sink (FR-22, design §3.12).

:class:`JSONLAuditSink` writes one ``orjson``-encoded
:data:`harbor.runtime.Event` per line to a file opened with
``O_APPEND`` (atomic append on POSIX for writes <= ``PIPE_BUF``;
single-record events well below that ceiling). Each :meth:`write`
calls :func:`os.write` then :func:`os.fsync` so a crash at any point
leaves only whole-line records on disk -- partial-line tails would be
ambiguous to the replay reader.

Optional Ed25519 signing
------------------------
When constructed with ``signing_key=<Ed25519PrivateKey>`` the on-disk
record is wrapped in a two-field envelope::

    {"event": <event-payload>, "sig": "<hex-ed25519-sig>"}

The signature covers the canonical-JSON ``orjson.dumps`` of the inner
``event`` dict (i.e. the bytes a replay verifier would re-encode).
Unsigned mode keeps the bare event dict as the line payload, preserving
backward-compatibility with Phase 1 readers.

Rotation
--------
The sink tracks bytes written since open. When the file grows past
``max_bytes`` (default 100 MiB per design §3.12) the next :meth:`write`
closes the active fd, renames the file to ``<base>.<N>`` (smallest free
N), and reopens a fresh ``O_APPEND`` handle. The rotation rename
happens before the new record is written so the size cap is a hard
ceiling, not a soft one.

Append-only invariant
---------------------
The sink only ever calls :func:`os.write` on an ``O_APPEND`` fd; it
never seeks. Test ``test_append_only_invariant_no_seek_calls`` enforces
this by patching :func:`os.lseek` and asserting zero invocations.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Protocol

import orjson
from pydantic import TypeAdapter

from harbor.runtime.events import Event

if TYPE_CHECKING:
    from pathlib import Path

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

__all__ = [
    "AuditSink",
    "JSONLAuditSink",
]


# 100 MiB (design §3.12 default rotation ceiling).
_DEFAULT_MAX_BYTES = 100 * 1024 * 1024


# TypeAdapter to dump the Event discriminated-union back to JSON-mode dict
# for orjson encoding (matches the design §3.12 ``ev.model_dump(mode="json")``
# call shape; the alias itself is not a class so we route through the adapter).
_EVENT_ADAPTER: TypeAdapter[Event] = TypeAdapter(Event)


class AuditSink(Protocol):
    """Contract for engine audit log writers (design §3.12).

    Implementors MUST guarantee append-only semantics -- once
    :meth:`write` returns successfully, the record is durably persisted
    and cannot be silently overwritten.
    """

    async def write(self, ev: Event) -> None:
        """Persist a single runtime event."""
        ...

    async def close(self) -> None:
        """Flush and release the underlying handle."""
        ...


class JSONLAuditSink:
    """Append-only JSONL writer with optional Ed25519 signing (FR-22).

    Opens ``path`` with :data:`os.O_WRONLY` | :data:`os.O_CREAT` |
    :data:`os.O_APPEND` so every write lands at the current end of file
    regardless of concurrent writers. Each call to :meth:`write` emits
    exactly one line followed by :func:`os.fsync` for crash-durability.

    Parameters
    ----------
    path:
        Active log file. Rotated siblings are named ``<path>.<N>`` with
        ``N`` starting at 0.
    signing_key:
        Optional :class:`Ed25519PrivateKey`. When supplied each record
        is wrapped in ``{"event": ..., "sig": "<hex>"}``; otherwise the
        bare event dict is the line payload.
    max_bytes:
        Rotation ceiling in bytes (default 100 MiB per design §3.12).
        Set to ``0`` to disable rotation.
    """

    def __init__(
        self,
        path: Path,
        *,
        signing_key: Ed25519PrivateKey | None = None,
        max_bytes: int = _DEFAULT_MAX_BYTES,
    ) -> None:
        self._path = path
        self._signing_key = signing_key
        self._max_bytes = max_bytes
        self._fd: int = self._open(path)
        # Pre-existing file may already have content -- start the byte
        # counter at the on-disk size so rotation triggers at the right
        # cumulative threshold across reopens.
        self._bytes_written: int = os.fstat(self._fd).st_size

    @staticmethod
    def _open(path: Path) -> int:
        # ``0o644`` so audit logs are world-readable (operators / replay
        # tooling) but only the owning process can write.
        return os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            0o644,
        )

    def _rotate(self) -> None:
        """Close active fd, rename to ``<path>.<N>``, reopen fresh."""
        os.close(self._fd)
        n = 0
        while True:
            candidate = self._path.with_name(f"{self._path.name}.{n}")
            if not candidate.exists():
                break
            n += 1
        os.rename(self._path, candidate)
        self._fd = self._open(self._path)
        self._bytes_written = 0

    def _encode(self, ev: Event) -> bytes:
        """Serialize one event to its on-disk line bytes (no trailing newline)."""
        # ``mode="json"`` matches design §3.12 -- datetimes serialize as
        # ISO-8601 strings, enums as their values, no Pydantic-internal
        # types leak into the on-disk format.
        payload = _EVENT_ADAPTER.dump_python(ev, mode="json")
        event_bytes = orjson.dumps(payload)
        if self._signing_key is None:
            return event_bytes
        # Sign the canonical event-bytes so a verifier can re-encode the
        # inner ``event`` field and check the signature without ambiguity
        # over key ordering.
        sig = self._signing_key.sign(event_bytes).hex()
        return orjson.dumps({"event": payload, "sig": sig})

    async def write(self, ev: Event) -> None:
        """Append one JSON-encoded event line to the log."""
        line = self._encode(ev) + b"\n"
        if self._max_bytes and self._bytes_written + len(line) > self._max_bytes:
            self._rotate()
        os.write(self._fd, line)
        os.fsync(self._fd)
        self._bytes_written += len(line)

    async def close(self) -> None:
        """Close the underlying file descriptor."""
        os.close(self._fd)
