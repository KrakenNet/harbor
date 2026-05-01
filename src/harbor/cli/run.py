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

Interactive mode (Plan 1):
``--inputs key=value`` seeds typed initial state; live progress is rendered
via :class:`ProgressPrinter`; ``WaitingForInputEvent`` events are resolved
by :class:`HITLHandler` (or fail under ``--non-interactive``); the
end-of-run :class:`SummaryRenderer` prints status + writes artifacts.
"""

from __future__ import annotations

import asyncio
import contextlib
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

import anyio
import typer
import yaml
from rich.console import Console

from harbor.audit.jsonl import JSONLAuditSink
from harbor.checkpoint.sqlite import SQLiteCheckpointer
from harbor.cli._inputs import parse_inputs
from harbor.cli._progress import ProgressPrinter
from harbor.cli._prompts import HITLHandler
from harbor.cli._summary import SummaryRenderer
from harbor.graph import Graph, GraphRun
from harbor.ir import IRDocument
from harbor.ir._ids import new_run_id
from harbor.nodes.base import EchoNode, ExecutionContext, NodeBase
from harbor.runtime.events import ToolCallEvent, ToolResultEvent

if TYPE_CHECKING:
    from pydantic import BaseModel

    from harbor.checkpoint.protocol import RunSummary
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


async def _drive_interactive(
    run: GraphRun,
    audit_sink: JSONLAuditSink | None,
    progress: ProgressPrinter,
    hitl: HITLHandler | None,
    console: Console,
) -> RunSummary:
    """Tee bus events to: audit_sink (jsonl), progress (stdout), hitl (input prompts).

    Returns the :class:`RunSummary` produced by :meth:`GraphRun.start`.
    """
    summary_holder: dict[str, Any] = {}

    async def _reader() -> None:
        with contextlib.suppress(anyio.EndOfStream, anyio.ClosedResourceError):
            while True:
                ev: Any = await run.bus.receive()
                if audit_sink is not None:
                    await audit_sink.write(ev)
                if ev.type == "waiting_for_input":
                    if hitl is None:
                        console.print(
                            "[red]✗ run paused for HITL but --non-interactive set[/red]"
                        )
                        raise typer.Exit(2)
                    await hitl.handle(ev, run)
                progress.feed(ev)
                if ev.type == "result":
                    progress.finalize(ev.ts)
                    return

    async with anyio.create_task_group() as tg:
        tg.start_soon(_reader)
        try:
            summary_holder["summary"] = await run.start()
        finally:
            await run.bus.aclose()
    return summary_holder["summary"]


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
    inputs: Annotated[
        list[str] | None,
        typer.Option(
            "--inputs",
            "-i",
            help="key=value initial state field (repeatable; key must match IR state_schema)",
        ),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="suppress per-step progress output"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="print tool result payloads inline"),
    ] = False,
    no_summary: Annotated[
        bool,
        typer.Option("--no-summary", help="skip end-of-run summary block"),
    ] = False,
    summary_json: Annotated[
        bool,
        typer.Option("--summary-json", help="emit summary as JSON instead of text"),
    ] = False,
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive",
            help="fail on awaiting-input instead of prompting",
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
    if quiet and verbose:
        raise typer.BadParameter("--quiet and --verbose are mutually exclusive")

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

    run_id = new_run_id()

    ckpt_path = checkpoint or Path(".harbor") / "run.sqlite"
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    checkpointer = SQLiteCheckpointer(ckpt_path)

    audit_sink: JSONLAuditSink | None = None
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        audit_sink = JSONLAuditSink(log_file)

    artifacts_dir = Path(".harbor") / "runs" / run_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    initial_values = parse_inputs(inputs or [], ir.state_schema)
    initial_state = g.state_schema(**initial_values)
    node_registry = _build_node_registry(ir.nodes)
    run = GraphRun(
        run_id=run_id,
        graph=g,
        initial_state=initial_state,
        node_registry=node_registry,
        checkpointer=checkpointer,
    )

    console = Console()
    progress = ProgressPrinter(console, quiet=quiet, verbose=verbose)
    hitl: HITLHandler | None = None if non_interactive else HITLHandler(console)

    async def _bootstrap_and_drive() -> RunSummary:
        await checkpointer.bootstrap()
        try:
            return await _drive_interactive(run, audit_sink, progress, hitl, console)
        finally:
            await checkpointer.close()
            if audit_sink is not None:
                await audit_sink.close()

    try:
        summary = asyncio.run(_bootstrap_and_drive())
    except KeyboardInterrupt:
        console.print("[yellow]cancelled[/yellow]")
        raise typer.Exit(code=130) from None

    if not no_summary:
        # Reconstruct final state model from the ResultEvent's snapshot.
        final_state_dict = progress.final_state_dict() or {}
        try:
            final_state = g.state_schema(**final_state_dict)
        except Exception:
            # If the schema can't validate (e.g. on failure paths), fall back
            # to the run's initial state so the renderer still has something
            # to dump non-default fields from.
            final_state = initial_state
        renderer = SummaryRenderer(
            console, json_mode=summary_json, suppress=no_summary
        )
        renderer.render(
            summary=summary,
            final_state=final_state,
            stats=progress.stats(),
            artifacts_dir=artifacts_dir,
            run_id=run.run_id,
            checkpoint=ckpt_path,
        )

    # Stable single-line marker, last line of stdout — downstream parsers
    # (test_cli_inspect, test_counterfactual_e2e) split on this.
    typer.echo(f"run_id={run.run_id} status={summary.status}")

    if summary.status != "done":
        raise typer.Exit(code=1)
