# SPDX-License-Identifier: Apache-2.0
"""harbor.skills public surface (design §3.6, §3.7, §3.9).

Re-exports the :class:`Skill` base class + supporting taxonomy, the
:class:`SalienceScorer` Protocol with its v1 :class:`RuleBasedScorer`,
and the :class:`ReactSkill` POC tool-loop subgraph (FR-25).
"""

from __future__ import annotations

from harbor.skills import refs
from harbor.skills.base import Example, Skill, SkillKind
from harbor.skills.react import ReactSkill, ReactState, ReactStep, ToolCallRecord
from harbor.skills.salience import RuleBasedScorer, SalienceContext, SalienceScorer

__all__ = [
    "Example",
    "ReactSkill",
    "ReactState",
    "ReactStep",
    "RuleBasedScorer",
    "SalienceContext",
    "SalienceScorer",
    "Skill",
    "SkillKind",
    "ToolCallRecord",
    "refs",
]
