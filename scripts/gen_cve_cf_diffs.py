# SPDX-License-Identifier: Apache-2.0
"""One-shot generator for ``tests/fixtures/cve_cf_diffs/*.txt`` (FR-56, AC-11.3).

Builds two synthetic ``RunHistory`` pairs (parent + cf) shaped like the CVE
pipeline's broker-mutation and respond-rejection counterfactual scenarios,
computes :func:`harbor.replay.compare.compare`, and writes the rendered
:class:`harbor.replay.compare.RunDiff` to disk as text-archive artifacts.

Pragmatic rationale (per spec task 5.4): the existing CF integration tests
in ``tests/integration/serve/test_counterfactual_*`` pin the entry-point
contracts (cf-fork mints fresh ``cf-<uuid>``, ``derived_graph_hash``
sensitivity, parent byte-identity) but the cf-loop wiring that drives the
mutation through real downstream nodes lands in a later phase. The
diff-archive captured here is the *expected* shape for both scenarios,
synthesized from the cf-pipeline shape spec'd in design §13.3.

Run via:

    uv run python scripts/gen_cve_cf_diffs.py [out_dir]

Default ``out_dir`` is ``tests/fixtures/cve_cf_diffs``.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from harbor.checkpoint import Checkpoint
from harbor.checkpoint.sqlite import SQLiteCheckpointer
from harbor.ir import IRBase
from harbor.ir import dumps as ir_dumps
from harbor.replay.compare import compare
from harbor.replay.history import RunHistory

_PARENT_GRAPH_HASH = "a" * 64
_CF_GRAPH_HASH = "b" * 64


def _ckpt(
    *,
    run_id: str,
    step: int,
    state: dict[str, Any],
    last_node: str = "n",
    next_action: dict[str, Any] | None = None,
    graph_hash: str = _PARENT_GRAPH_HASH,
) -> Checkpoint:
    """Build a deterministic ``Checkpoint`` (fixed timestamp for diff stability)."""
    return Checkpoint(
        run_id=run_id,
        step=step,
        branch_id=None,
        parent_step_idx=None,
        graph_hash=graph_hash,
        runtime_hash="rt-1",
        state=state,
        clips_facts=[],
        last_node=last_node,
        next_action=next_action,
        timestamp=datetime(2026, 4, 30, 0, 0, 0, tzinfo=UTC),
        parent_run_id=None,
        side_effects_hash="0" * 64,
    )


async def _broker_diff(out_dir: Path) -> None:
    """Generate ``broker_mutation_diff.txt`` (broker-output override scenario)."""
    cp = SQLiteCheckpointer(out_dir / "_broker.sqlite")
    await cp.bootstrap()
    parent_id = "parent-cve-broker"
    cf_id = "cf-cve-broker-001"
    parent_steps: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = [
        ("source", {"phase": "init"}, None),
        ("enrich", {"phase": "preflight"}, None),
        (
            "broker_request",
            {
                "phase": "broker",
                "sources_queried": ["A", "B"],
                "broker_data": {"signals": ["s-A", "s-B"]},
            },
            None,
        ),
        ("ml_score", {"phase": "ranked", "ranking": ["s-A", "s-B"]}, None),
        ("summarize", {"phase": "summarized", "summary": "based on A+B signals"}, None),
        (
            "clips_route",
            {"phase": "terminal", "action": "X", "summary": "based on A+B signals"},
            {"kind": "halt", "target": "action_X"},
        ),
    ]
    for i, (node, state, next_action) in enumerate(parent_steps):
        await cp.write(
            _ckpt(run_id=parent_id, step=i, state=state, last_node=node, next_action=next_action)
        )
    cf_steps: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = [
        ("source", {"phase": "init"}, None),
        ("enrich", {"phase": "preflight"}, None),
        (
            "broker_request",
            {
                "phase": "broker",
                "sources_queried": ["C", "D"],
                "broker_data": {"signals": ["s-C", "s-D"]},
            },
            None,
        ),
        ("ml_score", {"phase": "ranked", "ranking": ["s-C", "s-D"]}, None),
        ("summarize", {"phase": "summarized", "summary": "based on C+D signals"}, None),
        (
            "clips_route",
            {"phase": "terminal", "action": "Y", "summary": "based on C+D signals"},
            {"kind": "halt", "target": "action_Y"},
        ),
    ]
    for i, (node, state, next_action) in enumerate(cf_steps):
        gh = _CF_GRAPH_HASH if i >= 2 else _PARENT_GRAPH_HASH
        await cp.write(
            _ckpt(
                run_id=cf_id,
                step=i,
                state=state,
                last_node=node,
                next_action=next_action,
                graph_hash=gh,
            )
        )
    parent = await RunHistory.load(parent_id, checkpointer=cp)
    cf = await RunHistory.load(cf_id, checkpointer=cp)
    diff = compare(parent, cf)
    text = ir_dumps(cast("IRBase", diff))
    (out_dir / "broker_mutation_diff.txt").write_text(
        "# Counterfactual broker-mutation RunDiff (FR-56, AC-11.3, design §13.3).\n"
        "# Scenario: parent CVE pipeline brokered sources [A,B] -> action X.\n"
        "# CF mutation: node_output_overrides[broker_request] = sources [C,D] -> action Y.\n"
        "# Expected divergence: state at steps 2..5, derived_hash, final_status.\n"
        "# Captured 2026-04-30 via scripts/gen_cve_cf_diffs.py.\n\n" + text + "\n"
    )
    await cp.close()


async def _respond_diff(out_dir: Path) -> None:
    """Generate ``respond_rejection_diff.txt`` (HITL respond-override scenario)."""
    cp = SQLiteCheckpointer(out_dir / "_respond.sqlite")
    await cp.bootstrap()
    parent_id = "parent-cve-respond"
    cf_id = "cf-cve-respond-001"
    parent_steps: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = [
        ("source", {"phase": "init"}, None),
        ("work_1", {"phase": "work-1"}, None),
        ("work_2", {"phase": "work-2"}, None),
        ("work_3", {"phase": "work-3"}, None),
        ("approval_gate", {"phase": "awaiting", "awaiting_input": True}, None),
        ("approval_gate", {"phase": "responded", "decision": "approve"}, None),
        (
            "branch_router",
            {"phase": "terminal", "decision": "approve", "action": "notify"},
            {"kind": "halt", "target": "notify"},
        ),
    ]
    for i, (node, state, next_action) in enumerate(parent_steps):
        await cp.write(
            _ckpt(run_id=parent_id, step=i, state=state, last_node=node, next_action=next_action)
        )
    cf_steps: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = [
        ("source", {"phase": "init"}, None),
        ("work_1", {"phase": "work-1"}, None),
        ("work_2", {"phase": "work-2"}, None),
        ("work_3", {"phase": "work-3"}, None),
        ("approval_gate", {"phase": "awaiting", "awaiting_input": True}, None),
        (
            "approval_gate",
            {"phase": "responded", "decision": "reject", "comment": "vetoed"},
            None,
        ),
        (
            "branch_router",
            {"phase": "terminal", "decision": "reject", "action": "drop"},
            {"kind": "halt", "target": "drop"},
        ),
    ]
    for i, (node, state, next_action) in enumerate(cf_steps):
        gh = _CF_GRAPH_HASH if i >= 4 else _PARENT_GRAPH_HASH
        await cp.write(
            _ckpt(
                run_id=cf_id,
                step=i,
                state=state,
                last_node=node,
                next_action=next_action,
                graph_hash=gh,
            )
        )
    parent = await RunHistory.load(parent_id, checkpointer=cp)
    cf = await RunHistory.load(cf_id, checkpointer=cp)
    diff = compare(parent, cf)
    text = ir_dumps(cast("IRBase", diff))
    (out_dir / "respond_rejection_diff.txt").write_text(
        "# Counterfactual respond-rejection RunDiff "
        "(FR-56, AC-11.3, AC-14.7, design §13.3).\n"
        "# Scenario: parent pipeline analyst-approves at the InterruptNode -> action notify.\n"
        "# CF mutation: respond_payloads[step=4] = "
        "{decision: reject, comment: vetoed} -> action drop.\n"
        "# Expected divergence: state at steps 5..6, derived_hash, final_status.\n"
        "# Captured 2026-04-30 via scripts/gen_cve_cf_diffs.py.\n\n" + text + "\n"
    )
    await cp.close()


async def _main() -> int:
    """Build both diff archives in ``out_dir`` (default ``tests/fixtures/cve_cf_diffs``)."""
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tests/fixtures/cve_cf_diffs")
    out.mkdir(parents=True, exist_ok=True)
    await _broker_diff(out)
    await _respond_diff(out)
    for p in out.glob("_*.sqlite*"):
        p.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
