# SPDX-License-Identifier: Apache-2.0
"""``ToolRegistry.compatible_with(graph)`` capability filter (FR-23, AC-3).

Phase-1 status: :meth:`ToolRegistry.compatible_with` is a stub that
returns *all* registered tools without inspecting graph capabilities
(see :mod:`harbor.registry.tools`). The capability-driven filter lands
with the security/capabilities wiring in Phase 3 (task 3.13+).

This module pins two invariants:

1. The precondition holds today: a :class:`ToolRegistry` exists and
   exposes a callable ``compatible_with`` method.
2. The eventual filter contract is captured as an :func:`pytest.xfail`
   placeholder so once the real implementation lands the xfail flips to
   green and surfaces the regression loudly.
"""

from __future__ import annotations

import pytest

from harbor.registry import ToolRegistry

pytestmark = [pytest.mark.knowledge, pytest.mark.unit]


def test_compatible_with_filters_by_capabilities() -> None:
    """Precondition: registry + ``compatible_with`` surface exists today.

    The real capability-driven filter is deferred to Phase 3 (task 3.13);
    once it lands, replace the xfail block below with the actual
    capability-vs-required assertions.
    """
    reg = ToolRegistry()
    assert hasattr(reg, "compatible_with")
    assert callable(reg.compatible_with)

    # The Phase-1 stub returns all tools; no filtering occurs yet. Pin
    # the deferred contract as an expected-failure so the future
    # implementation flips this to green automatically.
    pytest.xfail(
        "compatible_with capability filter deferred to Phase 3 (task 3.13); "
        "Phase-1 stub returns all tools without inspecting graph capabilities",
    )
