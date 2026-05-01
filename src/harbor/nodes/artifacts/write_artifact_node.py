# SPDX-License-Identifier: Apache-2.0
"""harbor.nodes.artifacts.write_artifact_node -- :class:`WriteArtifactNode` (FR-92, design §10.3).

The node reads a state-resident byte payload (or ``str``, coerced to UTF-8
bytes), persists it through a configured
:class:`~harbor.artifacts.ArtifactStore`, emits an
:class:`~harbor.runtime.events.ArtifactWrittenEvent` on the run's event
bus, and patches the resulting :class:`~harbor.artifacts.ArtifactRef`
into state under :attr:`WriteArtifactNodeConfig.output_field`.

Replay determinism (``side_effects = SideEffects.write``, design §10.3):
``replay_policy="must_stub"`` (default) refuses to call
:meth:`ArtifactStore.put` when ``ctx.is_replay`` is ``True`` -- the
cassette layer is expected to surface the recorded
:class:`~harbor.artifacts.ArtifactRef` upstream of node dispatch.
``replay_policy="fail_loud"`` raises
:class:`~harbor.errors.ArtifactStoreError` on any replay-time call so
mis-wired replay setups surface immediately.

The Phase-1 :class:`~harbor.nodes.base.ExecutionContext` Protocol only
pins ``run_id``; this module declares :class:`WriteArtifactContext` as
the structural surface :class:`WriteArtifactNode` actually requires
(``run_id``, ``step``, ``bus``, ``artifact_store``, ``is_replay``,
``fathom``). The real :class:`~harbor.graph.run.GraphRun` satisfies this
surface as later phases land richer context wiring; tests pass
duck-typed contexts. This mirrors the
:class:`~harbor.nodes.subgraph.SubGraphContext` convention introduced in
task 1.30.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal, Protocol, runtime_checkable

from pydantic import Field

from harbor.errors import ArtifactStoreError
from harbor.ir import IRBase
from harbor.nodes.base import ExecutionContext, NodeBase
from harbor.runtime.events import ArtifactWrittenEvent
from harbor.tools.spec import SideEffects

if TYPE_CHECKING:
    from pydantic import BaseModel

    from harbor.artifacts import ArtifactRef, ArtifactStore

__all__ = [
    "WriteArtifactContext",
    "WriteArtifactNode",
    "WriteArtifactNodeConfig",
]


@runtime_checkable
class WriteArtifactContext(Protocol):
    """Structural surface :class:`WriteArtifactNode` reads from the run context.

    The Phase-1 :class:`~harbor.nodes.base.ExecutionContext` Protocol
    only pins ``run_id``; the artifact-write node additionally requires:

    * ``step`` -- monotonic per-run step index stamped on every emitted
      event and on the persisted :class:`~harbor.artifacts.ArtifactRef`
      provenance fields (matches :class:`harbor.runtime.tool_exec.RunContext`).
    * ``bus`` -- the run's event bus (must expose
      ``async send(event, *, fathom=...)`` matching
      :class:`harbor.runtime.bus.EventBus`).
    * ``artifact_store`` -- the resolved
      :class:`~harbor.artifacts.ArtifactStore` provider for this run.
    * ``is_replay`` -- replay-routing flag, mirrors
      :attr:`harbor.runtime.tool_exec.RunContext.is_replay`. Honored by
      ``replay_policy``.
    * ``fathom`` -- optional :class:`~harbor.fathom.FathomAdapter` for
      ``harbor.transition`` mirroring (parity with the bus-side
      contract in :mod:`harbor.runtime.parallel`).
    """

    run_id: str
    step: int
    bus: Any
    artifact_store: ArtifactStore
    is_replay: bool
    fathom: Any


class WriteArtifactNodeConfig(IRBase):
    """Pydantic config for :class:`WriteArtifactNode` (design §10.3).

    Inherits ``extra="forbid"`` from :class:`IRBase` so unknown keys in
    YAML/JSON IR fail loudly at validation time (FR-6, AC-9.1).
    """

    content_field: str
    """State attribute holding the artifact payload (``bytes`` or ``str``)."""
    name: str
    """Logical filename hint persisted in :class:`ArtifactRef.name`."""
    content_type: str
    """MIME type persisted in sidecar metadata + :class:`ArtifactRef.content_type`."""
    metadata: dict[str, Any] = Field(default_factory=dict[str, Any])
    """Extra free-form metadata merged into the sidecar (under ``content_type``)."""
    output_field: str = "artifact_ref"
    """State key receiving the resulting :class:`ArtifactRef` (``model_dump`` form)."""
    replay_policy: Literal["must_stub", "fail_loud"] = "must_stub"
    """Replay routing per design §10.3 (``side_effects=write`` is replay-sensitive)."""


class WriteArtifactNode(NodeBase):
    """Built-in node that persists a state-resident payload as an artifact (FR-92).

    The node is replay-aware: ``side_effects = SideEffects.write`` marks
    it as a write-side-effect node, and ``replay_policy`` controls what
    happens when ``ctx.is_replay`` is ``True``:

    * ``must_stub`` (default) -- the node does NOT call
      :meth:`ArtifactStore.put`; the upstream cassette layer is expected
      to surface a recorded :class:`ArtifactRef` ahead of dispatch.
      Today the runtime cassette layer for nodes is not yet wired (the
      tool-exec replay path at :mod:`harbor.runtime.tool_exec` only
      handles tool calls), so reaching this branch in replay means the
      cassette wiring is incomplete; the node raises
      :class:`ArtifactStoreError` with a clear message until that lands.
    * ``fail_loud`` -- the node raises immediately on any replay-time
      call, surfacing wiring bugs without ambiguity.

    Configured via :class:`WriteArtifactNodeConfig`; the config is
    attached at construction time (``WriteArtifactNode(config=cfg)``).
    """

    side_effects = SideEffects.write
    """Write-class side effect; replay must stub or fail loud (design §10.3)."""
    config_model = WriteArtifactNodeConfig
    """Pydantic config schema, surfaced for IR validators / registry tooling."""

    def __init__(self, *, config: WriteArtifactNodeConfig) -> None:
        self._config = config

    @property
    def config(self) -> WriteArtifactNodeConfig:
        """Public read-only handle on the validated config (used by tests)."""
        return self._config

    async def execute(
        self,
        state: BaseModel,
        ctx: ExecutionContext,
    ) -> dict[str, Any]:
        """Persist the configured state field as an artifact, emit + patch state.

        Returns a dict patch ``{config.output_field: ref.model_dump()}``
        so the field-merge step (FR-11) writes the
        :class:`ArtifactRef` (JSON-mode dump) into run state under the
        configured key.
        """
        write_ctx = self._require_write_context(ctx)
        content_bytes = self._coerce_content(getattr(state, self._config.content_field))

        if write_ctx.is_replay:
            self._handle_replay()

        store = write_ctx.artifact_store
        sidecar_metadata: dict[str, Any] = {
            "content_type": self._config.content_type,
            **self._config.metadata,
        }
        ref: ArtifactRef = await store.put(
            name=self._config.name,
            content=content_bytes,
            metadata=sidecar_metadata,
            run_id=write_ctx.run_id,
            step=write_ctx.step,
        )

        await self._emit_artifact_written(write_ctx, ref)

        return {self._config.output_field: ref.model_dump(mode="json")}

    # ------------------------------------------------------------------ #
    # internals                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _require_write_context(ctx: ExecutionContext) -> WriteArtifactContext:
        """Narrow ``ctx`` to :class:`WriteArtifactContext` or raise loudly.

        A missing ``artifact_store``, ``bus``, or ``is_replay`` is a
        wiring bug, not a recoverable runtime condition (mirrors the
        :class:`~harbor.nodes.subgraph.SubGraphNode` convention). FR-6
        force-loud: surface the missing attributes at the call site.
        """
        if not isinstance(ctx, WriteArtifactContext):
            raise AttributeError(
                "WriteArtifactNode requires an execution context with "
                "`run_id`, `step`, `bus`, `artifact_store`, `is_replay`, "
                "and `fathom`; got " + type(ctx).__name__
            )
        return ctx

    @staticmethod
    def _coerce_content(value: object) -> bytes:
        """Coerce ``str`` payloads to UTF-8 bytes; pass ``bytes`` through.

        ``bytearray`` and ``memoryview`` are accepted (converted via
        ``bytes(...)``) so callers can stream binary data from buffers.
        Anything else raises :class:`TypeError` -- silent coercion of
        arbitrary objects would mask wiring bugs (FR-6).
        """
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("utf-8")
        if isinstance(value, bytearray):
            return bytes(value)
        if isinstance(value, memoryview):
            return value.tobytes()
        raise TypeError(
            "WriteArtifactNode content_field must be bytes or str; got " + type(value).__name__
        )

    def _handle_replay(self) -> None:
        """Apply the configured ``replay_policy`` when ``ctx.is_replay`` is True.

        Both branches raise today: the runtime cassette layer for
        nodes is not yet wired (only :mod:`harbor.runtime.tool_exec`
        handles replay), so a replay-time call to this node means the
        cassette wiring is incomplete. The error message names the gap
        explicitly per the design's "fail loud on missing wiring"
        contract (FR-6).
        """
        if self._config.replay_policy == "fail_loud":
            raise ArtifactStoreError(
                "WriteArtifactNode invoked in replay context with "
                "replay_policy='fail_loud'; recorded ArtifactRef must "
                "be surfaced via the cassette layer before dispatch.",
                reason="replay-fail-loud",
                backend="harbor.nodes.artifacts.WriteArtifactNode",
            )
        # must_stub: today the node-cassette layer is not yet wired, so
        # we surface the gap loudly rather than silently writing.
        raise ArtifactStoreError(
            "WriteArtifactNode invoked in replay context with "
            "replay_policy='must_stub' but the node-cassette layer is "
            "not yet wired (harbor.runtime.tool_exec covers tool "
            "calls only). The recorded ArtifactRef must be surfaced "
            "ahead of node dispatch -- raising rather than re-writing.",
            reason="replay-stub-missing",
            backend="harbor.nodes.artifacts.WriteArtifactNode",
        )

    async def _emit_artifact_written(
        self,
        ctx: WriteArtifactContext,
        ref: ArtifactRef,
    ) -> None:
        """Publish one :class:`ArtifactWrittenEvent` on the run bus.

        ``provenance`` follows the design §10.3 shape
        (``origin="tool"``, ``source="harbor.artifacts"``); the typed
        ``Provenance`` model from :mod:`harbor.runtime.tool_exec` is not
        yet promoted to a public symbol, so we emit the dict shape the
        :class:`ArtifactWrittenEvent` schema accepts (``dict[str, Any]``).
        """
        # ``confidence=1.0`` and ``timestamp`` close out the
        # ProvenanceBundle tuple (origin, source, run_id, step, confidence,
        # timestamp) the JSONL lineage audit (FR-55, AC-11.2) requires on
        # every audited fact -- system-emitted or user-asserted. The
        # artifact write is a deterministic system output, so confidence
        # is always 1.0; the timestamp is the same wall-clock instant
        # stamped into the event envelope.
        now = datetime.now(UTC)
        provenance: dict[str, Any] = {
            "origin": "tool",
            "source": "harbor.artifacts",
            "run_id": ctx.run_id,
            "step": ctx.step,
            "confidence": 1.0,
            "timestamp": now.isoformat(),
        }
        event = ArtifactWrittenEvent(
            run_id=ctx.run_id,
            step=ctx.step,
            ts=now,
            artifact_ref=ref.model_dump(mode="json"),
            provenance=provenance,
        )
        await ctx.bus.send(event, fathom=ctx.fathom)
