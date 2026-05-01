# SPDX-License-Identifier: Apache-2.0
"""Skills module for the ``beta`` synthetic plugin (loaded only at stage 2)."""

from __future__ import annotations

LOADED: bool = True


def register_skills() -> list[object]:
    """Hookimpl-shaped function returning an empty skill list."""
    return []
