# SPDX-License-Identifier: Apache-2.0
"""``harbor run`` subcommand -- POC graph runner (FR-8, design §3.10).

Loads an IR YAML, builds an :class:`harbor.ir.IRDocument`, constructs an
:class:`harbor.graph.Graph`, and drives a fresh :class:`harbor.graph.GraphRun`
through :func:`harbor.graph.loop.execute` to completion. A SQLite checkpointer
is wired (default: ``./.harbor/run.sqlite``); a JSONL audit sink is wired only
when ``--log-file`` is supplied.

Phase 3 ``--inspect`` mode (design §3.10 table -- ``run`` row, FR-8/9):
when ``--inspect`` is supplied, ``cmd`` skips checkpointer + audit-sink
construction entirely, builds the :class:`Graph`, calls
:meth:`Graph.simulate` with synthetic zero-value fixtures (one entry per
IR node), and prints the per-rule firing trace. No node executes; no
file is written; exit is ``0`` on a clean simulation and non-zero on
any :class:`SimulationError` (e.g. fixture-coverage violation).

Remaining Phase-3 deferrals:

* ``--postgres <dsn>`` is deferred; only SQLite is wired.
* The node registry is keyed off :attr:`NodeSpec.kind` and accepts the two
  POC kinds in ``tests/fixtures/sample-graph.yaml`` (``echo``, ``halt``);
  unknown kinds raise loudly so misconfigured fixtures fail fast (FR-6).

Exit code is ``0`` on terminal status ``done`` and non-zero otherwise.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

import typer
import yaml

from harbor.audit.jsonl import JSONLAuditSink
from harbor.checkpoint.sqlite import SQLiteCheckpointer
from harbor.graph import Graph, GraphRun
from harbor.ir import IRDocument
from harbor.ir._ids import new_run_id
from harbor.nodes.base import EchoNode, ExecutionContext, NodeBase
from harbor.runtime.events import ToolCallEvent, ToolResultEvent

if TYPE_CHECKING:
    from pydantic import BaseModel

    from harbor.ir._models import NodeSpec

__all__ = ["cmd"]


class _StubDSPyNode(NodeBase):
    """CLI-local stub DSPy node (VE2-Phase4 wiring).

    The Phase-4 sample graph (``tests/fixtures/sample-graph-phase4.yaml``)
    declares ``node_b`` with ``kind: dspy`` to exercise the FR-14 tool-call
    audit contract end-to-end without standing up a live LLM. The paired
    cassette records zero HTTP interactions, so this node returns a fixed
    answer projection and emits ``tool_call`` / ``tool_result`` events on
    the run bus around the synthetic invocation.

    Wiring DSPy modules via ``harbor.adapters.dspy.bind`` is the production
    path (see :class:`harbor.nodes.dspy.DSPyNode`); this stub is the CLI's
    no-config default for ``kind: dspy`` IRs whose modules are bound at
    runtime by callers who skip the bind step (POC ergonomics).
    """

    async def execute(
        self,
        state: BaseModel,
        ctx: ExecutionContext,
    ) -> dict[str, Any]:
        # ``ExecutionContext`` is a :class:`Protocol`; the live driver
        # passes the concrete :class:`GraphRun`, which carries the bus +
        # fathom handle FR-14 events need. Cast through ``Any`` so this
        # surface stays typed against the protocol while still reaching
        # the structural fields the runtime supplies.
        run: Any = ctx
        call_id = f"{run.run_id}-stub-dspy"
        await run.bus.send(
            ToolCallEvent(
                run_id=run.run_id,
                step=0,
                ts=datetime.now(UTC),
                tool_name="dspy.stub",
                namespace="harbor.tests",
                args={"message": getattr(state, "message", "")},
                call_id=call_id,
            ),
            fathom=run.fathom,
        )
        outputs = {"answer": "stub-answer"}
        await run.bus.send(
            ToolResultEvent(
                run_id=run.run_id,
                step=0,
                ts=datetime.now(UTC),
                call_id=call_id,
                ok=True,
                result=outputs,
            ),
            fathom=run.fathom,
        )
        return outputs


# Phase 1 POC kind -> NodeBase factory map. ``halt`` reuses :class:`EchoNode`
# because the v1 sample graph has no Fathom rules wired into the loop -- the
# loop walks the static IR edge to end-of-list and returns. ``halt`` here is a
# pass-through node (matching the YAML fixture's intent: a marker terminal).
# ``dspy`` resolves to a CLI-local stub that emits FR-14 tool_call/tool_result
# events without a live LLM (VE2-Phase4 wiring).
_NODE_FACTORIES: dict[str, type[NodeBase]] = {
    "echo": EchoNode,
    "halt": EchoNode,
    "dspy": _StubDSPyNode,
}


def _build_node_registry(nodes: list[NodeSpec]) -> dict[str, NodeBase]:
    """Map ``node_id -> NodeBase`` for every node in ``nodes``.

    Raises :class:`typer.BadParameter` (renders cleanly to stderr) on unknown
    ``kind`` values so misconfigured fixtures surface at CLI load time rather
    than mid-run.
    """
    registry: dict[str, NodeBase] = {}
    for node in nodes:
        factory = _NODE_FACTORIES.get(node.kind)
        if factory is None:
            raise typer.BadParameter(
                f"unknown node kind {node.kind!r} for node {node.id!r}; "
                f"POC supports {sorted(_NODE_FACTORIES)}"
            )
        registry[node.id] = factory()
    return registry


async def _drive(
    run: GraphRun,
    audit_sink: JSONLAuditSink | None,
) -> str:
    """Drive ``run`` to completion, optionally tee'ing bus events to JSONL.

    The loop publishes :class:`~harbor.runtime.events.Event` records via
    :attr:`GraphRun.bus`; when ``audit_sink`` is non-``None`` we drain those
    records concurrently and write each as one JSONL line. The bus is closed
    after the loop returns so the reader unblocks and exits cleanly.
    """
    if audit_sink is None:
        summary = await run.start()
        return summary.status

    import contextlib

    import anyio

    async def _reader() -> None:
        with contextlib.suppress(anyio.EndOfStream, anyio.ClosedResourceError):
            while True:
                ev = await run.bus.receive()
                await audit_sink.write(ev)

    status = "failed"
    async with anyio.create_task_group() as tg:
        tg.start_soon(_reader)
        try:
            summary = await run.start()
            status = summary.status
        finally:
            await run.bus.aclose()
    return status


def cmd(
    graph: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to an IR YAML graph definition.",
        ),
    ],
    log_file: Annotated[
        Path | None,
        typer.Option(
            "--log-file",
            help="Append per-event JSONL records to this path (default: no log).",
        ),
    ] = None,
    checkpoint: Annotated[
        Path | None,
        typer.Option(
            "--checkpoint",
            help="SQLite checkpoint DB path (default: ./.harbor/run.sqlite).",
        ),
    ] = None,
    inspect: Annotated[
        bool,
        typer.Option(
            "--inspect",
            help="Print rule-firing trace without executing nodes (FR-8/9).",
        ),
    ] = False,
) -> None:
    """Run a Harbor graph end-to-end (FR-8 POC).

    Loads ``graph`` as IR YAML, validates it, constructs a SQLite-backed
    :class:`GraphRun`, and drives the single-node execution loop to terminal
    state. Exits ``0`` on ``done`` and non-zero on ``failed``.

    With ``--inspect`` the function instead invokes :meth:`Graph.simulate`
    against synthetic zero-value fixtures and prints the rule-firing
    trace. No checkpoint or log file is touched in this mode.
    """
    ir_dict = yaml.safe_load(graph.read_text(encoding="utf-8"))
    ir = IRDocument.model_validate(ir_dict)

    g = Graph(ir)

    if inspect:
        # ``simulate`` requires one fixture per IR node; synthesize empty
        # dict outputs so the trace is callable on any IR. No tools or
        # nodes execute.
        fixtures: dict[str, object] = {n.id: {} for n in ir.nodes}
        result = asyncio.run(g.simulate(fixtures))
        typer.echo(f"graph_hash={g.graph_hash}")
        typer.echo(f"rule_firings={len(result.rule_firings)}")
        for firing in result.rule_firings:
            matched = ",".join(firing.matched_nodes) or "-"
            actions = ",".join(firing.action_kinds) or "-"
            typer.echo(
                f"  rule={firing.rule_id} fired={firing.fired} "
                f"matched=[{matched}] actions=[{actions}]"
            )
        return

    ckpt_path = checkpoint or Path(".harbor") / "run.sqlite"
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    checkpointer = SQLiteCheckpointer(ckpt_path)

    audit_sink: JSONLAuditSink | None = None
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        audit_sink = JSONLAuditSink(log_file)

    # POC initial state: zero-value per declared field. The compiled state
    # schema (``Graph._compile_state_schema``) marks every field required, so
    # we cannot just call ``state_schema()`` -- we synthesize the per-type
    # zero value matching the IR ``state_schema`` dict. Phase 2 grows a
    # ``--state-file`` option for caller-supplied initial values.
    zero_by_type: dict[str, object] = {"str": "", "int": 0, "bool": False, "bytes": b""}
    initial_values = {name: zero_by_type[t] for name, t in ir.state_schema.items()}
    initial_state = g.state_schema(**initial_values)
    node_registry = _build_node_registry(ir.nodes)
    run = GraphRun(
        run_id=new_run_id(),
        graph=g,
        initial_state=initial_state,
        node_registry=node_registry,
        checkpointer=checkpointer,
    )

    async def _bootstrap_and_drive() -> str:
        await checkpointer.bootstrap()
        try:
            return await _drive(run, audit_sink)
        finally:
            await checkpointer.close()
            if audit_sink is not None:
                await audit_sink.close()

    status = asyncio.run(_bootstrap_and_drive())

    typer.echo(f"run_id={run.run_id} status={status}")
    if status != "done":
        raise typer.Exit(code=1)
