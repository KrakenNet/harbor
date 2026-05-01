# SPDX-License-Identifier: Apache-2.0
"""Per-tick node dispatch -- one iteration of the §3.1.2 nine-step loop.

:func:`dispatch_node` is the body of :func:`harbor.graph.loop.execute`'s
``while`` loop, lifted into its own function so the loop driver in
``loop.py`` reads as a thin orchestrator (Phase 2 refactor, simplicity).

The function executes steps 1-9 of design §3.1.2 for a single node and
returns the routing outcome -- either the next ``current_id`` to dispatch,
or ``None`` to halt the run. Behavior is unchanged from the inlined
Phase 1 implementation; this is a pure extraction.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from harbor.checkpoint.protocol import Checkpoint
from harbor.ir._models import GotoAction, HaltAction, ParallelAction
from harbor.runtime.action import ContinueAction, translate_actions
from harbor.runtime.events import TransitionEvent

if TYPE_CHECKING:
    from harbor.graph.run import GraphRun
    from harbor.ir._models import NodeSpec

__all__ = ["dispatch_node"]


async def dispatch_node(
    run: GraphRun,
    nodes: list[NodeSpec],
    current_node: NodeSpec,
    state: Any,
    step: int,
) -> tuple[Any, str | None]:
    """Run one §3.1.2 tick for ``current_node``; return ``(new_state, next_id)``.

    ``next_id`` is ``None`` when the tick halts the run (Fathom ``halt``
    decision or end-of-graph on a ``continue`` decision). Caller is
    responsible for the outer ``while`` and the lifecycle transitions on
    :class:`~harbor.graph.run.GraphRun`.

    The Phase 1 POC stubs are preserved verbatim -- Fathom is gated on
    ``run.fathom``, capabilities are not yet enforced here, and the
    ``"parallel"`` decision raises :class:`NotImplementedError` (Phase 3).
    """
    current_id = current_node.id

    # 1. Run node body.
    node_impl = run.node_registry.get(current_id)
    if node_impl is None:
        raise KeyError(f"no node implementation registered for id={current_id!r}")
    outputs = await node_impl.execute(state, run)

    # 2. Apply outputs to state (last-write-wins; FR-11 typed merge later).
    state = state.model_copy(update=outputs)

    # 3. Mirror annotated state -> AssertSpecs (Fathom-gated).
    actions: list[Any] = []
    if run.fathom is not None:
        mirror_specs = run.fathom.mirror_state(state, annotations={})
        run.mirror_scheduler.schedule(mirror_specs, lifecycle="step")

        # 4. Fathom assert + evaluate (sync; off-thread).
        await asyncio.to_thread(_assert_specs, run.fathom, mirror_specs, run.run_id, step)
        actions = await asyncio.to_thread(run.fathom.evaluate)

    # 5. Translate Fathom actions -> single RoutingDecision.
    decision = translate_actions(actions)

    # 6. Emit transition event (back-pressure-safe via the bus).
    target_for_event = (
        decision.target
        if isinstance(decision, GotoAction)
        else (_next_node_id(nodes, current_id) or "")
    )
    event = TransitionEvent(
        run_id=run.run_id,
        step=step,
        ts=datetime.now(UTC),
        from_node=current_id,
        to_node=target_for_event,
        rule_id="",
        reason=decision.kind,
    )
    await run.bus.send(event, fathom=run.fathom)

    # 7. Shielded checkpoint commit (FR-10).
    assert run.checkpointer is not None  # checked by caller
    checkpoint = Checkpoint(
        run_id=run.run_id,
        step=step,
        branch_id=None,
        parent_step_idx=None,
        graph_hash=run.graph.graph_hash,
        runtime_hash=run.graph.runtime_hash,
        state=state.model_dump(mode="json"),
        clips_facts=[],
        last_node=current_id,
        next_action=(
            None if isinstance(decision, ContinueAction) else decision.model_dump(mode="json")
        ),
        timestamp=datetime.now(UTC),
        parent_run_id=run.parent_run_id,
        side_effects_hash="",
    )
    await asyncio.shield(run.checkpointer.write(checkpoint))

    # 8. Mirror lifecycle: retract step-scoped mirrors at the boundary.
    run.mirror_scheduler.retract_step()

    # 9. Routing.
    if isinstance(decision, HaltAction):
        return state, None
    if isinstance(decision, ParallelAction):
        raise NotImplementedError("parallel branches land in Phase 3")
    if isinstance(decision, GotoAction):
        return state, decision.target
    # ContinueAction -- walk the static IR edge.
    return state, _next_node_id(nodes, current_id)


def _next_node_id(nodes: list[NodeSpec], current_id: str) -> str | None:
    """Return the id of the node after ``current_id`` in ``nodes``, or ``None``."""
    for idx, node in enumerate(nodes):
        if node.id == current_id and idx + 1 < len(nodes):
            return nodes[idx + 1].id
    return None


def _assert_specs(fathom: Any, specs: list[Any], run_id: str, step: int) -> None:
    """Assert each AssertSpec via the Fathom adapter with a minimal provenance bundle."""
    from datetime import UTC, datetime
    from decimal import Decimal

    for spec in specs:
        fathom.assert_with_provenance(
            spec.template,
            spec.slots,
            {
                "origin": "state",
                "source": "mirror",
                "run_id": run_id,
                "step": step,
                "confidence": Decimal("1.0"),
                "timestamp": datetime.now(UTC),
            },
        )
