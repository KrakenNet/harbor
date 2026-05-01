# SPDX-License-Identifier: Apache-2.0
"""Harbor IR version constants and major-divergence check (FR-35, AC-19.2).

This module owns the IR version a given Harbor build consumes. The IR
follows semver-like ``MAJOR.MINOR.PATCH``; a major bump signals a
breaking schema change. :func:`check_version` flags documents whose
``ir_version`` major differs from :data:`HARBOR_IR_VERSION` -- callers
should treat this as a refusal to interpret the document, not a soft
warning, since meaning across majors is undefined.

* :data:`HARBOR_IR_VERSION` -- the single source of truth for the IR
  version this build understands.
* :func:`parse_version` -- splits ``"X.Y.Z"`` into ``(int, int, int)``;
  raises :class:`ValueError` on any malformed input (wrong arity, empty
  segment, non-integer segment).
* :func:`check_version` -- returns a single ``version_mismatch``
  :class:`ValidationError` when the document's major differs, ``[]``
  otherwise. Missing/non-string ``ir_version`` is left to Pydantic
  validation upstream and skipped here.
"""

from __future__ import annotations

from typing import Any

from harbor.errors import ValidationError

__all__ = ["HARBOR_IR_VERSION", "check_version", "parse_version"]


HARBOR_IR_VERSION = "1.0.0"


def parse_version(s: str) -> tuple[int, int, int]:
    """Parse ``"MAJOR.MINOR.PATCH"`` into a 3-tuple of ints.

    Raises :class:`ValueError` if ``s`` does not consist of exactly three
    dot-separated non-empty integer segments (e.g., ``"1.0"``,
    ``"1.0.0.0"``, ``"1.x.0"``, ``"1..0"`` all reject).
    """
    parts = s.split(".")
    if len(parts) != 3:
        raise ValueError(f"version must be MAJOR.MINOR.PATCH, got {s!r}")
    try:
        major, minor, patch = (int(p) for p in parts)
    except ValueError as exc:
        raise ValueError(f"version segments must be integers, got {s!r}") from exc
    return major, minor, patch


def check_version(ir: dict[str, Any]) -> list[ValidationError]:
    """Return a single ``version_mismatch`` error when majors diverge.

    Skips silently (returns ``[]``) when ``ir_version`` is missing or
    non-string -- Pydantic validation upstream is responsible for those.
    Likewise skips when the value is malformed (non-semver), since a
    pattern check belongs to the schema layer; here we care only about
    the major-divergence semantic check.
    """
    raw = ir.get("ir_version")
    if not isinstance(raw, str):
        return []
    try:
        doc_major, _, _ = parse_version(raw)
    except ValueError:
        return []
    expected_major, _, _ = parse_version(HARBOR_IR_VERSION)
    if doc_major == expected_major:
        return []
    return [
        ValidationError(
            "IR version mismatch",
            path="/ir_version",
            expected=f"^{expected_major}\\.",
            actual=raw,
            hint=(
                f"version_mismatch: this Harbor consumes IR major version "
                f"{expected_major}; document is major {doc_major}"
            ),
        )
    ]
