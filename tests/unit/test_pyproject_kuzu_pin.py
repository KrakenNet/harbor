# SPDX-License-Identifier: Apache-2.0
"""Pin Kuzu to ``0.11.3`` + carry the RyuGraph swap-path comment (FR-11, AC-12.1).

Kuzu's GitHub repo was archived 2025-10-10 after Apple acquired Kuzu Inc.
Active community fork lives at ``predictable-labs/ryugraph``. Harbor
abstracts Kuzu behind the :class:`harbor.stores.graph.GraphStore`
Protocol so swapping to RyuGraph is a one-file change. Until the fork
story stabilises we hold a tight ``==`` pin and document the swap-path
inline; this test guards both the version and the rationale comment so
a future bump cannot silently drop either.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = [pytest.mark.knowledge, pytest.mark.unit]


_PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def test_kuzu_version_pinned_to_0_11_3() -> None:
    """``kuzu==0.11.3`` exact pin lives under ``[project.optional-dependencies].stores``."""
    data = tomllib.loads(_PYPROJECT.read_text())
    stores = data["project"]["optional-dependencies"]["stores"]
    pins = [dep for dep in stores if dep.startswith("kuzu")]
    assert pins == ["kuzu==0.11.3"], (
        f"expected exact pin 'kuzu==0.11.3' in [project.optional-dependencies].stores, got {pins!r}"
    )


def test_kuzu_pin_has_ryugraph_swap_path_comment() -> None:
    """Pyproject carries the RyuGraph swap-path rationale next to the pin."""
    text = _PYPROJECT.read_text()
    assert "ryugraph" in text.lower(), (
        "pyproject must explain the RyuGraph swap path next to the kuzu pin (FR-11, AC-12.1)"
    )
    # The comment must mention both the Apple acquisition / archived-repo
    # rationale AND the swap-path so future maintainers see why the pin
    # is tight.
    lowered = text.lower()
    assert "archived" in lowered or "apple" in lowered, (
        "swap-path comment must capture WHY the pin is tight (Kuzu repo archived after "
        "Apple acquisition)"
    )
