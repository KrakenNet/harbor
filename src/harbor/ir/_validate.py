# SPDX-License-Identifier: Apache-2.0
"""Eager structured IR validation -- :func:`validate` never raises.

This module is the single entry point for IR validation (FR-17, FR-18,
AC-12.1, AC-12.2, AC-12.5). :func:`validate` accepts a JSON string or an
already-decoded dict and returns ``list[ValidationError]``: empty on
success, populated on any failure including malformed JSON, missing
required fields, type errors, pattern mismatches, and (Phase 2)
``ir_version`` major divergence.

Each :class:`harbor.errors.ValidationError` carries structured context
(``path``, ``expected``, ``actual``, ``hint``) instead of just a string,
so downstream tools can render diagnostics consistently.

* :data:`_HINTS` maps ``pydantic_core.ErrorDetails.type`` codes to
  actionable suggestions; unknown types fall back to the Pydantic docs URL.
* :func:`_loc_to_pointer` converts a Pydantic ``loc`` tuple to an
  RFC 6901 JSON Pointer (``~`` -> ``~0``, ``/`` -> ``~1``).
* :func:`check_version` (re-exported from :mod:`._versioning`) flags
  documents whose ``ir_version`` major diverges from this build's
  :data:`HARBOR_IR_VERSION` (FR-35, AC-19.2).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from pydantic import ValidationError as PydanticValidationError

from harbor.errors import ValidationError

from ._ids import validate_node_id, validate_pack_id, validate_rule_id
from ._models import IRDocument
from ._versioning import check_version

if TYPE_CHECKING:
    from pydantic_core import ErrorDetails

__all__ = ["check_version", "validate"]


_HINTS: dict[str, str] = {
    "missing": "Add the required field.",
    "extra_forbidden": "Remove this field -- IR forbids unknown keys.",
    "union_tag_invalid": "Set a valid discriminator value (see schema).",
    "union_tag_not_found": "Add the discriminator field.",
    "string_pattern_mismatch": "Match the documented regex (e.g., id format).",
    "greater_than_equal": "Adjust value to meet the bound.",
    "less_than_equal": "Adjust value to meet the bound.",
    "string_too_short": "Adjust length.",
    "string_too_long": "Adjust length.",
    "int_parsing": "Provide a numeric value of the documented type.",
    "decimal_parsing": "Provide a numeric value of the documented type.",
}


def _loc_to_pointer(loc: tuple[int | str, ...]) -> str:
    """Convert a Pydantic ``loc`` tuple to an RFC 6901 JSON Pointer.

    Each segment is escaped: ``~`` -> ``~0`` then ``/`` -> ``~1``.
    Integer segments (list indices) become decimal strings. An empty
    ``loc`` maps to ``""`` (whole-document pointer per RFC 6901).
    """
    if not loc:
        return ""
    parts: list[str] = []
    for segment in loc:
        text = str(segment)
        text = text.replace("~", "~0").replace("/", "~1")
        parts.append(text)
    return "/" + "/".join(parts)


def _to_harbor_error(detail: ErrorDetails) -> ValidationError:
    """Map a Pydantic :class:`ErrorDetails` to a Harbor :class:`ValidationError`."""
    err_type = detail.get("type", "")
    url = detail.get("url", "")
    hint = _HINTS.get(err_type, f"See {url}" if url else detail.get("msg", ""))
    path = _loc_to_pointer(detail.get("loc", ()))
    expected = detail.get("msg", "")
    actual = detail.get("input")
    return ValidationError(
        "IR validation failed",
        path=path,
        expected=expected,
        actual=actual,
        hint=hint,
    )


def validate(ir: dict[str, Any] | str) -> list[ValidationError]:
    """Eager structured validation -- never raises.

    Returns ``[]`` on valid IR; a populated list on any failure
    (malformed JSON, missing required, type/pattern mismatch, version
    divergence). Each error carries ``path``, ``expected``, ``actual``,
    ``hint`` in its ``context`` dict for structured rendering.
    """
    parsed: Any
    if isinstance(ir, str):
        try:
            parsed = json.loads(ir)
        except json.JSONDecodeError as exc:
            return [
                ValidationError(
                    "IR JSON parse error",
                    path="/",
                    expected="valid JSON",
                    actual=ir[:80],
                    hint=str(exc),
                )
            ]
    else:
        parsed = ir

    try:
        doc = IRDocument.model_validate(parsed)
    except PydanticValidationError as exc:
        return [_to_harbor_error(d) for d in exc.errors(include_url=True, include_input=True)]

    # Stable-ID slug enforcement (FR-33) — done outside the IRDocument
    # Pydantic class because FR-7 / AC-13.1 ban ``model_validator`` decorators
    # in ``_models.py`` to keep the JSON Schema round-trip pure.
    id_errors: list[ValidationError] = []
    for idx, node in enumerate(doc.nodes):
        try:
            validate_node_id(node.id)
        except ValueError as exc:
            id_errors.append(
                ValidationError(
                    "IR validation failed",
                    path=f"/nodes/{idx}/id",
                    expected="slug ([a-z0-9][a-z0-9_\\-.]{0,127})",
                    actual=node.id,
                    hint=str(exc),
                ),
            )
    for idx, rule in enumerate(doc.rules):
        try:
            validate_rule_id(rule.id)
        except ValueError as exc:
            id_errors.append(
                ValidationError(
                    "IR validation failed",
                    path=f"/rules/{idx}/id",
                    expected="slug ([a-z0-9][a-z0-9_\\-.]{0,127})",
                    actual=rule.id,
                    hint=str(exc),
                ),
            )
    for idx, pack in enumerate(doc.governance):
        try:
            validate_pack_id(pack.id)
        except ValueError as exc:
            id_errors.append(
                ValidationError(
                    "IR validation failed",
                    path=f"/governance/{idx}/id",
                    expected="slug ([a-z0-9][a-z0-9_\\-.]{0,127})",
                    actual=pack.id,
                    hint=str(exc),
                ),
            )
    if id_errors:
        return id_errors

    if isinstance(parsed, dict):
        return check_version(cast("dict[str, Any]", parsed))
    return []
