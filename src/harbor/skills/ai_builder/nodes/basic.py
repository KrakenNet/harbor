# SPDX-License-Identifier: Apache-2.0
"""BasicChat — plain LLM fallback for the basic route.

Reads `turn` and `history` from state, calls the LLM (or returns a stub
response for Phase A before the model registry decision lands), and writes
the result to `response` (design §3.1).

State contract: reads `turn`, `history`; writes `response`.
No citations, no `child_run_id` (design §3.1).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from harbor.nodes.base import ExecutionContext, NodeBase

if TYPE_CHECKING:
    from pydantic import BaseModel


_SYSTEM_PROMPT = (
    "You are the AI Builder assistant for StarGraph, a Harbor workflow designer. "
    "You help users understand Harbor concepts, debug graphs, and think through "
    "workflow designs. You have access to the conversation history below. "
    "When the user's question is specifically about their own graphs or data, "
    "say you can look that up if they'd like (Inspector mode). When asked about "
    "Harbor framework internals, say you can search the docs. "
    "Keep responses concise and specific to Harbor/StarGraph."
)


def _call_llm(
    turn: str,
    history: list[dict[str, Any]],
    model: Any | None = None,  # noqa: ANN401 -- model registry TBD (§8 Q4)
) -> str:
    """Call the LLM with system prompt + history + turn.

    Phase A stub: returns a canned response. Wire real LLM when model
    registry decision lands (design §8 Q4).
    """
    del model  # unused until model registry lands
    del history  # passed to LLM once wired
    del turn
    # TODO Phase A polish: replace with real LLM call once model registry is decided.
    return "stub: basic chat — LLM not yet wired (Phase A scaffold)"


class BasicChat(NodeBase):
    """Plain LLM chat node. Phase A: stub response; Phase A polish: real LLM."""

    async def execute(self, state: BaseModel, ctx: ExecutionContext) -> dict[str, Any]:
        turn: str = getattr(state, "turn", "")
        history: list[Any] = list(getattr(state, "history", []))

        response = _call_llm(
            turn,
            [h.model_dump() if hasattr(h, "model_dump") else h for h in history],
        )

        return {"response": response, "citations": []}
