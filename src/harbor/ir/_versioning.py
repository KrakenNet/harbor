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

from typing import TYPE_CHECKING, Any

from harbor.errors import PackCompatError, ValidationError

if TYPE_CHECKING:
    from ._models import PackMount

__all__ = [
    "HARBOR_IR_VERSION",
    "check_pack_compat",
    "check_version",
    "parse_version",
]


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


def check_pack_compat(
    pack_mount: PackMount,
    harbor_facts_version: str,
    api_version: str,
) -> None:
    """Verify a pack mount's ``requires`` matches the host versions (FR-39).

    Per harbor-serve-and-bosun design §3.2 / §7.4 / AC-3.2: a Bosun rule
    pack mount may declare ``requires.harbor_facts_version`` and/or
    ``requires.api_version`` -- the harbor-facts schema version + plugin
    api_version it was authored against. This function is the load-time
    gate (NOT runtime): mismatches surface :class:`PackCompatError` so
    silent runtime drift is impossible (FR-6 force-loud).

    Comparison is **pinned-string equality** (POC slice). Semver-aware
    matching is a Phase-3+ refinement; for v1 pack authors pin the
    exact target version. ``None`` on either side of a field means
    "no requirement on this field" -- the unset slot is skipped.

    Args:
        pack_mount: The :class:`harbor.ir.PackMount` whose ``requires``
            block (if any) is being checked.
        harbor_facts_version: The harbor-facts schema version the host
            consumes (e.g. ``"1.0"``).
        api_version: The plugin api_version the host exposes (e.g. ``"1"``).

    Raises:
        PackCompatError: when ``pack_mount.requires`` is set and any
            populated field disagrees with the corresponding host
            version. Context fields: ``pack_id``, ``field``,
            ``required``, ``actual``.
    """
    requires = pack_mount.requires
    if requires is None:
        # Legacy two-field mount (or explicit "no requirement"). Accept
        # for back-compat -- existing PackMount(id=..., version=...)
        # callers must keep loading without surprise.
        return

    if (
        requires.harbor_facts_version is not None
        and requires.harbor_facts_version != harbor_facts_version
    ):
        raise PackCompatError(
            f"pack {pack_mount.id!r} requires harbor_facts_version "
            f"{requires.harbor_facts_version!r}, host has {harbor_facts_version!r}",
            pack_id=pack_mount.id,
            field="harbor_facts_version",
            required=requires.harbor_facts_version,
            actual=harbor_facts_version,
        )

    if requires.api_version is not None and requires.api_version != api_version:
        raise PackCompatError(
            f"pack {pack_mount.id!r} requires api_version "
            f"{requires.api_version!r}, host has {api_version!r}",
            pack_id=pack_mount.id,
            field="api_version",
            required=requires.api_version,
            actual=api_version,
        )
