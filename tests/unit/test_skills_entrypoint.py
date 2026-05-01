# SPDX-License-Identifier: Apache-2.0
"""``harbor.skills`` entry-point group is discovered by the loader.

The two-stage pluggy loader enumerates entry points across
:data:`harbor.plugin.loader.GROUPS`. This test pins the contract that
``"harbor.skills"`` is one of those groups so plugin distributions can
contribute skills via ``[project.entry-points."harbor.skills"]``.
"""

from __future__ import annotations

import pytest

from harbor.plugin.loader import GROUPS

pytestmark = [pytest.mark.knowledge, pytest.mark.unit]


def test_harbor_skills_group_in_groups_tuple() -> None:
    """``"harbor.skills"`` is one of the four discovered entry-point groups."""
    assert "harbor.skills" in GROUPS
