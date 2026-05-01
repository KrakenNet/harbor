# SPDX-License-Identifier: Apache-2.0
"""TriageGate — validates inputs and emits the routing fact for mode."""

from __future__ import annotations

from typing import Any

from harbor.nodes.base import ExecutionContext, NodeBase
from harbor.skills.shipwright.state import State


class TriageGate(NodeBase):
    async def execute(self, state: State, ctx: ExecutionContext) -> dict[str, Any]:
        if state.mode == "new" and not state.brief:
            raise ValueError("brief is required for mode=new")
        if state.mode == "fix" and not state.target_path:
            raise ValueError("target_path is required for mode=fix")
        return {"mode": state.mode}
