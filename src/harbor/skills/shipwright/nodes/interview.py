# SPDX-License-Identifier: Apache-2.0
"""Interview nodes — GapCheck (rule-driven floor; LLM ceiling lands in Task 8)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from harbor.nodes.base import ExecutionContext, NodeBase
from harbor.skills.shipwright._pack import fresh_engine, load_pack
from harbor.skills.shipwright.state import Question

if TYPE_CHECKING:
    from pydantic import BaseModel


_QUESTION_PROMPTS = {
    "purpose": "What is the one-sentence purpose of this graph?",
    "nodes": "Which nodes should the graph have? (think → act → observe is a fine default)",
    "state_fields": (
        "What state fields will flow through the graph? "
        "Which should be Mirror-annotated?"
    ),
    "stores": "Which stores does it need? (vector / graph / doc / memory / fact)",
    "triggers": "Which triggers fire it? (manual / cron / webhook)",
    "annotated_state": (
        "You haven't marked any state field as annotated — "
        "rules will see nothing. Mark at least one?"
    ),
}


def _prompt_for(slot: str, kind: str) -> str:
    if slot in _QUESTION_PROMPTS:
        return _QUESTION_PROMPTS[slot]
    if kind == "edge_case":
        return f"Edge case to confirm: `{slot}`."
    return f"Please provide a value for `{slot}`."


class GapCheck(NodeBase):
    async def execute(self, state: BaseModel, ctx: ExecutionContext) -> dict[str, Any]:
        kind = getattr(state, "kind", None)
        if kind is None:
            return {"open_questions": []}

        slots: dict[str, Any] = getattr(state, "slots", {}) or {}

        eng = fresh_engine()
        load_pack(eng, "gaps")
        eng._env.assert_string(f'(spec.kind (value "{kind}"))')  # pyright: ignore[reportPrivateUsage]

        annotated: int | None = None
        for name, slot in slots.items():
            value = getattr(slot, "value", slot)
            eng._env.assert_string(f'(spec.slot (name "{name}") (value "{value!s}"))')  # pyright: ignore[reportPrivateUsage]
            if name == "annotated_count" and isinstance(value, int):
                annotated = value
        if annotated is not None:
            eng._env.assert_string(f"(spec.annotated_count (value {annotated}))")  # pyright: ignore[reportPrivateUsage]

        eng._env.run()  # pyright: ignore[reportPrivateUsage]

        questions: list[Question] = []
        for raw in eng._env.find_template("spec_gap").facts():  # pyright: ignore[reportPrivateUsage]
            fact = dict(raw)
            slot = str(fact["slot"])
            kind_value = str(fact.get("kind", "required"))
            questions.append(
                Question(
                    slot=slot,
                    prompt=_prompt_for(slot, kind_value),
                    kind=kind_value,  # type: ignore[arg-type]
                    schema={"type": "string"},
                    origin="rule",
                )
            )
        return {"open_questions": questions}
