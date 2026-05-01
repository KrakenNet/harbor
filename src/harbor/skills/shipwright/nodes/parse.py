# SPDX-License-Identifier: Apache-2.0
"""ParseBrief — DSPy node that turns a freeform brief into typed slots."""

from __future__ import annotations

from typing import Any

import dspy

from harbor.nodes.base import ExecutionContext, NodeBase
from harbor.skills.shipwright.state import SpecSlot, State


class _BriefSignature(dspy.Signature):
    """Extract the artifact kind, purpose, and any explicit node hints from a brief."""

    brief: str = dspy.InputField()
    kind: str = dspy.OutputField(desc="'graph' or 'pack'")
    purpose: str = dspy.OutputField(desc="one-sentence purpose")
    node_hints: list[str] = dspy.OutputField(desc="node names mentioned, possibly empty")


class ParseBrief(NodeBase):
    """LLM-driven brief parser. `must_stub: true` in topology — replay-deterministic."""

    def __init__(self) -> None:
        self._predictor = dspy.Predict(_BriefSignature)

    def _call_predictor(self, brief: str) -> dict[str, Any]:
        result = self._predictor(brief=brief)
        return {"kind": result.kind, "purpose": result.purpose, "node_hints": result.node_hints}

    async def execute(self, state: State, ctx: ExecutionContext) -> dict[str, Any]:
        if not state.brief:
            return {"slots": {}}
        parsed = self._call_predictor(state.brief)
        slots = {
            name: SpecSlot(name=name, value=value, origin="llm", confidence=0.7)
            for name, value in parsed.items()
        }
        return {"slots": slots}
