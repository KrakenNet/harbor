# SPDX-License-Identifier: Apache-2.0
""":class:`Scheduler` -- async cron loop + per-graph concurrency (design §6.1, §6.2).

Phase 2 upgrade of the task-1.21 POC. The scheduler now runs three
concurrent loops inside an internal :class:`anyio` task group:

* **``_cron_loop``** -- polls registered :class:`~harbor.triggers.cron.CronSpec`
  rows every ~50ms, computes ``cronsim.next_fire`` per spec, and enqueues
  a run when the fire time has passed. Idempotency keys
  (``sha256(trigger_id || scheduled_fire)`` per design §6.1) prevent double
  fires across restarts when paired with Checkpointer-backed pending state.
  The 50ms poll matches NFR-3 (±100ms scheduler precision).
* **``_dispatcher_loop``** -- consumes from the in-memory pending queue,
  acquires the per-``graph_hash`` :class:`anyio.CapacityLimiter`, and
  spawns one run task per item. The limiter map is populated lazily on
  first :meth:`enqueue` per graph (one limiter instance per
  ``graph_id``); same-graph runs serialize, different-graph runs proceed
  in parallel up to each limiter's capacity.
* **Pending durability** -- when a :class:`PendingStore` is supplied to
  the constructor, every enqueue writes a :class:`PendingRun` row to the
  store *before* the in-memory queue push, and run-completion deletes it
  on terminal state. Restart replays any rows still present, so in-flight
  triggers survive a process kill (FR-9, FR-10, NFR-3).

  The :class:`PendingStore` Protocol is defined locally rather than
  bolted onto :class:`harbor.checkpoint.Checkpointer` -- the v1
  Checkpointer Protocol covers per-step checkpoint snapshots, not
  scheduler queue state, and adding ``put_pending``/``take_pending`` to
  it would require touching the postgres + sqlite drivers in the same
  task. Phase-2 task 2.14 picks up the SQLite-side implementation; for
  now the scheduler accepts ``pending_store=None`` and degrades to
  in-memory (the POC default).

Backwards compatibility (no breaking changes vs task 1.21):

* Constructor takes only optional kwargs; existing call sites
  (``cli/serve.py`` task 1.28, FastAPI ``POST /v1/runs`` route task 1.24)
  continue to work without modification.
* :meth:`enqueue` keeps its sync signature and returns an
  :class:`asyncio.Future` resolving to a :class:`RunSummary`.
* :meth:`start` / :meth:`stop` keep their async lifecycle contract.

Cooperative cancellation (commit 869cdd3, task 1.8): the scheduler does
not reimplement cancel/pause -- it honors :meth:`GraphRun.cancel` /
:meth:`GraphRun.pause` on the live run handles. The dispatcher exits
cleanly when :meth:`stop` cancels its task group; in-flight workers
observe :class:`anyio.get_cancelled_exc_class` and propagate.

Design refs: §6.1 (async cron loop), §6.2 (per-``graph_hash``
concurrency), §6.5 (run-history pairing -- task 2.14). FR-7, FR-8, FR-9,
FR-10, NFR-3, NFR-14.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from zoneinfo import ZoneInfo

import anyio
import cronsim

from harbor.checkpoint.protocol import RunSummary
from harbor.errors import HarborRuntimeError

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from harbor.serve.history import RunHistory, TriggerSource
    from harbor.triggers.cron import CronSpec

_logger = logging.getLogger(__name__)


__all__ = [
    "PendingRun",
    "PendingStore",
    "QueueItem",
    "Scheduler",
]


#: Default per-``graph_hash`` concurrency limit. The IR has no
#: ``concurrency_limit`` field yet (design §6.2 expects one); ``1`` keeps
#: per-graph runs sequential -- safe POC default. Phase 2 reads
#: ``graph.concurrency_limit`` from the parent IR (task 2.22+).
_DEFAULT_GRAPH_CONCURRENCY = 1

#: Cron-loop polling interval. NFR-3 mandates ±100ms scheduler precision;
#: 50ms gives a 2x margin so the worst-case "fire missed by one tick"
#: case still lands well inside the budget.
_CRON_POLL_INTERVAL_S = 0.05


class PendingRun:
    """Single durable pending-run row (design §6.1).

    Carries the trigger payload (``graph_id`` + ``params``) plus the
    idempotency key used to dedupe across restarts (cron:
    ``sha256(trigger_id || scheduled_fire)``; webhook:
    ``sha256(trigger_id || body_hash)``; manual: caller-supplied UUID).

    A pending row is inserted before the in-memory queue push and removed
    on terminal state (success or failure); restart loads remaining rows
    and re-pushes them onto the queue so in-flight work survives a
    process kill. The ``run_id`` is assigned at enqueue time so the
    Checkpointer's ``runs`` row (task 2.14) can reference it directly.

    Attributes:
        run_id: Stable identifier for this run; format depends on the
            trigger source. Cron uses ``cron-{trigger_id}-{iso_fire}``;
            webhook uses ``webhook-{trigger_id}-{body_sha8}``; manual
            uses ``manual-{idempotency_key[:12]}``. Formatting is the
            scheduler's responsibility -- callers don't construct it.
        graph_id: Target graph hash / id; doubles as the
            ``graph_hash`` key for the :class:`anyio.CapacityLimiter`
            map (design §6.2 expects ``graph.concurrency_limit`` once
            the IR field lands).
        params: JSON-serializable parameter dict forwarded to the run.
        idempotency_key: Pre-computed dedup key per design §6.1.
        scheduled_fire: Wall-clock instant the trigger fired (cron) or
            was received (webhook/manual). Used by the catchup probe in
            :meth:`Scheduler.replay_pending`.
    """

    __slots__ = (
        "graph_id",
        "idempotency_key",
        "params",
        "run_id",
        "scheduled_fire",
    )

    def __init__(
        self,
        *,
        run_id: str,
        graph_id: str,
        params: Mapping[str, Any],
        idempotency_key: str,
        scheduled_fire: datetime,
    ) -> None:
        self.run_id = run_id
        self.graph_id = graph_id
        self.params = params
        self.idempotency_key = idempotency_key
        self.scheduled_fire = scheduled_fire


@runtime_checkable
class PendingStore(Protocol):
    """Durable pending-run state contract (design §6.1, §6.2).

    Defined locally so the scheduler can accept a checkpointer-shaped
    object without forcing the v1 :class:`harbor.checkpoint.Checkpointer`
    Protocol to grow scheduler-specific methods. A SQLite implementation
    lands in task 2.14 alongside the ``runs`` table; until then the
    scheduler accepts ``pending_store=None`` and degrades to in-memory.

    The contract is intentionally narrow -- four async methods, no
    transactional guarantees beyond per-call durability. The scheduler
    handles dedupe (idempotency key uniqueness) and crash-recovery
    (replay on startup).
    """

    async def put_pending(self, run: PendingRun) -> None:
        """Persist ``run`` so it survives a process restart."""
        ...

    async def delete_pending(self, run_id: str) -> None:
        """Remove the pending row for ``run_id`` (terminal state reached)."""
        ...

    async def list_pending(self) -> list[PendingRun]:
        """Return all pending rows (used at startup for replay)."""
        ...

    async def has_pending_for_key(self, idempotency_key: str) -> bool:
        """Return ``True`` if a pending row already exists for ``idempotency_key``."""
        ...


class QueueItem:
    """Single enqueued unit of work (in-memory queue row).

    Pairs a :class:`PendingRun` with the caller's awaiting
    :class:`asyncio.Future`. The dispatcher resolves the future on
    success or sets the worker's exception on failure.
    """

    __slots__ = ("future", "pending")

    def __init__(
        self,
        *,
        pending: PendingRun,
        future: asyncio.Future[RunSummary],
    ) -> None:
        self.pending = pending
        self.future = future


class Scheduler:
    """Async cron loop + per-``graph_hash`` concurrency + durable pending state.

    Lifecycle:

    * ``Scheduler(pending_store=None)`` -- created (idle). The optional
      :class:`PendingStore` enables crash-recovery; if ``None`` the
      scheduler is in-memory only (POC fallback).
    * ``await scheduler.start()`` -- replays any persisted pending rows,
      then spawns the ``_cron_loop`` and ``_dispatcher_loop`` tasks
      inside an internal :class:`anyio` task group (via dedicated
      :class:`asyncio.Task` shells so :meth:`stop` is callable from any
      task). After ``start()`` returns, :meth:`enqueue` and
      :meth:`register_cron` may be called.
    * ``await scheduler.stop()`` -- cancels both loops cleanly, awaits
      their exit, then cancels any pending-queue futures so callers do
      not hang. Cooperative cancellation propagates to in-flight runs
      via the standard anyio cancel scope path.

    Per-graph concurrency: ``self._limiters[graph_id]`` is created lazily
    on first :meth:`enqueue` per graph. Default capacity is
    :data:`_DEFAULT_GRAPH_CONCURRENCY` (1) until the IR ``concurrency_limit``
    field lands (Phase 2 task 2.22+).

    Cron-loop precision: ``_cron_loop`` polls every
    :data:`_CRON_POLL_INTERVAL_S` seconds (50ms), so a fire-time
    deadline is observed within ``[0, 50ms]`` of the cron-tick instant
    (well inside the NFR-3 ±100ms target). Per-spec idempotency keys
    prevent double fires within the polling tolerance.
    """

    _queue: asyncio.Queue[QueueItem | None]
    _limiters: dict[str, anyio.CapacityLimiter]
    _running: bool
    _shutdown: bool
    _consumer_task: asyncio.Task[None] | None
    _cron_task: asyncio.Task[None] | None
    _pending_store: PendingStore | None
    _run_history: RunHistory | None
    _cron_specs: list[tuple[CronSpec, ZoneInfo]]
    _cron_last_fire: dict[str, datetime]
    _enqueue_started_at: dict[str, datetime]

    def __init__(
        self,
        *,
        pending_store: PendingStore | None = None,
        run_history: RunHistory | None = None,
    ) -> None:
        # ``maxsize=0`` (unbounded) is the POC default. Phase 2 may bound
        # the queue + reject with HTTP 503 when full -- that ties into
        # the per-graph concurrency policy in §6.2.
        #
        # ``run_history`` is the design-§6.5 ``runs_history`` table
        # writer. When supplied, the scheduler calls
        # :meth:`RunHistory.insert_pending` on enqueue and
        # :meth:`RunHistory.update_status` on terminal transitions so
        # the ``GET /runs?status=&since=&limit=`` query path has a
        # canonical row to read. ``RunHistory`` also satisfies the
        # :class:`PendingStore` Protocol, so a single instance can be
        # passed for both ``pending_store=`` and ``run_history=`` (the
        # common Phase-2 wiring); they remain separate kwargs so tests
        # can supply an in-memory ``PendingStore`` while still
        # exercising the run-history write path against a real DB
        # (or vice versa).
        self._queue = asyncio.Queue()
        self._limiters = {}
        self._running = False
        self._shutdown = False
        self._consumer_task = None
        self._cron_task = None
        self._pending_store = pending_store
        self._run_history = run_history
        self._cron_specs = []
        self._cron_last_fire = {}
        # Captures the wall-clock instant at enqueue so the dispatcher
        # can compute ``duration_ms = now - started_at`` on terminal
        # transition. Cleared on terminal write to bound the dict size.
        self._enqueue_started_at = {}

    # ------------------------------------------------------------------ #
    # Lifecycle                                                          #
    # ------------------------------------------------------------------ #

    async def start(self) -> None:
        """Replay persisted pending rows, then spawn loops. Idempotent.

        Sequence:

        1. If a :class:`PendingStore` is wired, ``await
           pending_store.list_pending()`` and re-push each row onto the
           in-memory queue with a fresh :class:`asyncio.Future`. Caller
           futures from the pre-restart process are unrecoverable
           (cross-process futures are not supported by asyncio); the
           replayed runs still complete and update Checkpointer state,
           which is what FR-9 requires.
        2. Spawn ``_dispatcher_loop`` and ``_cron_loop`` as top-level
           :class:`asyncio.Task` objects. The two are independent: the
           cron loop may be idle (no specs registered) while the
           dispatcher serves manual / webhook enqueues, or vice versa.

        Each loop runs as its own :class:`asyncio.Task` rather than
        inside a shared :class:`anyio.create_task_group` because the
        scheduler's lifetime is decoupled from any single task group --
        :meth:`stop` cancels them individually.
        """
        if self._running:
            return
        self._running = True
        self._shutdown = False

        # Replay durable pending rows (no-op if pending_store is None).
        await self._replay_pending()

        self._consumer_task = asyncio.create_task(
            self._dispatcher_loop(),
            name="harbor.serve.scheduler.dispatcher",
        )
        self._cron_task = asyncio.create_task(
            self._cron_loop(),
            name="harbor.serve.scheduler.cron",
        )

    async def stop(self) -> None:
        """Cancel both loops, drain pending futures, await clean exit.

        Sequence:

        1. Flip ``_shutdown=True`` so the cron loop exits its poll cycle
           and the dispatcher exits after draining its current item.
        2. Push a ``None`` sentinel to wake a blocked
           :meth:`asyncio.Queue.get` so the dispatcher observes the
           shutdown flag promptly.
        3. Cancel the cron task (it may be sleeping in
           ``anyio.sleep``); await both tasks. We suppress
           :class:`asyncio.CancelledError` because it is the expected
           exit path.
        4. Cancel any pending-queue futures so awaiting callers see a
           :class:`asyncio.CancelledError` rather than hanging forever.
        """
        if not self._running:
            return
        self._running = False
        self._shutdown = True
        # Wake a blocked dispatcher.
        await self._queue.put(None)
        # Cancel the cron task (it may be sleeping).
        if self._cron_task is not None:
            self._cron_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cron_task
            self._cron_task = None
        if self._consumer_task is not None:
            with contextlib.suppress(asyncio.CancelledError):
                await self._consumer_task
            self._consumer_task = None
        # Drain leftover items (queued after stop() returned control but
        # before the sentinel was pulled). Cancel each caller's future
        # so awaiters do not hang.
        while not self._queue.empty():
            item = self._queue.get_nowait()
            if item is None:
                continue
            if not item.future.done():
                item.future.cancel()

    # ------------------------------------------------------------------ #
    # Public enqueue + cron registration                                 #
    # ------------------------------------------------------------------ #

    def enqueue(
        self,
        graph_id: str,
        params: Mapping[str, Any],
        idempotency_key: str | None = None,
        *,
        trigger_source: TriggerSource = "manual",
    ) -> asyncio.Future[RunSummary]:
        """Enqueue a run; return an awaitable resolving to :class:`RunSummary`.

        Sync to preserve the task-1.21 POC contract used by the FastAPI
        ``POST /v1/runs`` route + ``CronTrigger._fire``. The durable
        pending-row write + the ``runs_history`` insert are scheduled
        as background :class:`asyncio.Task` instances (no caller await
        needed) so the route handler returns ``202 Accepted``
        immediately.

        ``trigger_source`` records the originating subsystem (manual,
        cron, webhook) so the ``runs_history`` row can be filtered by
        source per design §6.5. Defaults to ``"manual"`` to preserve
        backwards compatibility for existing call sites; the cron loop
        passes ``"cron"`` and the webhook trigger plugin passes
        ``"webhook"``.

        Eagerly creates the :class:`anyio.CapacityLimiter` for ``graph_id``
        on first call (lazy per design §6.2) so concurrent enqueues for
        the same ``graph_id`` see the same limiter instance.

        Raises :class:`HarborRuntimeError` if :meth:`start` has not been
        called -- the dispatcher must be live for the future to ever
        resolve.
        """
        if not self._running:
            raise HarborRuntimeError(
                "Scheduler.enqueue() requires Scheduler.start() to have been called; "
                "the dispatcher task is not running"
            )
        # Eagerly create the limiter so concurrent enqueues for the same
        # graph race-free see the same instance.
        self._get_limiter(graph_id)

        now = datetime.now(UTC)
        # Caller-supplied idempotency key wins; otherwise synthesize one
        # so PendingStore rows always have a primary key.
        key = idempotency_key or self._synth_idempotency_key(graph_id, now)
        run_id = self._derive_run_id(graph_id, key)
        pending = PendingRun(
            run_id=run_id,
            graph_id=graph_id,
            params=params,
            idempotency_key=key,
            scheduled_fire=now,
        )
        loop = asyncio.get_running_loop()
        future: asyncio.Future[RunSummary] = loop.create_future()
        item = QueueItem(pending=pending, future=future)
        # In-memory queue push first (cheap, never blocks); the durable
        # write happens in the background so route handlers stay sync.
        self._queue.put_nowait(item)
        # Capture started_at so the dispatcher can compute duration_ms
        # on terminal write. Stored under run_id to survive the queue
        # pop boundary.
        self._enqueue_started_at[run_id] = now
        if self._pending_store is not None:
            asyncio.create_task(  # noqa: RUF006 - fire-and-forget; logged on failure
                self._persist_pending(pending),
                name=f"harbor.serve.scheduler.put_pending.{run_id}",
            )
        if self._run_history is not None:
            asyncio.create_task(  # noqa: RUF006 - fire-and-forget; logged on failure
                self._record_history_pending(run_id, graph_id, trigger_source),
                name=f"harbor.serve.scheduler.history_insert.{run_id}",
            )
        return future

    def register_cron(self, spec: CronSpec) -> None:
        """Register a :class:`CronSpec` with the scheduler's internal cron loop.

        The Scheduler's own ``_cron_loop`` polls registered specs and
        enqueues runs at fire time (design §6.1's canonical pattern).
        :class:`~harbor.triggers.cron.CronTrigger` instances may *also*
        spawn their own per-spec fire loops (their existing task-2.10
        behavior) -- both paths converge on :meth:`enqueue`, and the
        idempotency key dedupes against the :class:`PendingStore`. This
        dual-path arrangement keeps cross-task-group fire timing
        accurate even when one cron loop is briefly starved.

        Each call appends; duplicates by ``trigger_id`` are not
        deduplicated here (the caller -- typically the lifespan factory
        in task 2.30 -- owns spec registration ordering).
        """
        zone = ZoneInfo(spec.tz)
        # Validate the cron expression eagerly so a bad spec fails at
        # registration, not at first poll.
        cronsim.CronSim(spec.cron_expression, datetime.now(zone))
        self._cron_specs.append((spec, zone))

    # ------------------------------------------------------------------ #
    # Internal loops                                                     #
    # ------------------------------------------------------------------ #

    async def _cron_loop(self) -> None:
        """Poll registered cron specs and enqueue at fire time (design §6.1).

        Runs every :data:`_CRON_POLL_INTERVAL_S` seconds (50ms). For each
        registered spec, computes the next fire time relative to the
        last-known fire (or "now" on first iteration) and, if that
        moment has passed, enqueues a run with the canonical idempotency
        key ``sha256(trigger_id || scheduled_fire)``.

        The 50ms interval gives ±50ms worst-case observation latency,
        which is well inside the NFR-3 ±100ms scheduler precision target.

        On :class:`asyncio.CancelledError` (from :meth:`stop`), exits
        cleanly. Per-iteration exceptions are logged and swallowed so
        one bad spec cannot kill the whole loop (FR-2 isolation spirit).
        """
        while not self._shutdown:
            try:
                now_utc = datetime.now(UTC)
                for spec, zone in list(self._cron_specs):
                    self._maybe_fire_cron(spec, zone, now_utc)
                await anyio.sleep(_CRON_POLL_INTERVAL_S)
            except asyncio.CancelledError:
                return
            except Exception:  # pragma: no cover - defensive
                _logger.exception("Scheduler._cron_loop iteration failed")
                # Avoid a tight failure loop.
                await anyio.sleep(1.0)

    def _maybe_fire_cron(
        self,
        spec: CronSpec,
        zone: ZoneInfo,
        now_utc: datetime,
    ) -> None:
        """Fire ``spec`` if its next scheduled instant has passed.

        Uses ``last_fire`` (cron tick, in spec's tz) as the cursor: the
        loop computes the next fire after the last one and fires when
        wall clock catches up. On first observation (no ``last_fire``),
        the cursor starts at the previous cron tick so a startup-time
        catchup happens for any minute boundary the system was down for
        (the ``fire_once_catchup`` policy from design §6.1; the
        ``skip`` policy is honored by the per-:class:`CronTrigger` path
        only -- the Scheduler's internal loop is opt-in via
        :meth:`register_cron` for tests + future direct callers).
        """
        now_in_zone = now_utc.astimezone(zone)
        last = self._cron_last_fire.get(spec.trigger_id)
        # First observation: prime the cursor at "now" so we don't fire
        # historical ticks; subsequent iterations use the last fire so
        # cronsim returns the next fire after it.
        base = now_in_zone if last is None else last
        try:
            fire_at = next(cronsim.CronSim(spec.cron_expression, base))
        except StopIteration:  # pragma: no cover - cronsim is infinite
            return
        if fire_at > now_in_zone:
            return
        # Tick has passed (or is now): fire once, advance the cursor.
        key = self._cron_idempotency_key(spec.trigger_id, fire_at)
        try:
            self.enqueue(
                graph_id=spec.graph_id,
                params=spec.params,
                idempotency_key=key,
                trigger_source="cron",
            )
        except HarborRuntimeError:  # pragma: no cover - shutdown race
            return
        self._cron_last_fire[spec.trigger_id] = fire_at

    async def _dispatcher_loop(self) -> None:
        """Pull items off the queue and dispatch each under its limiter.

        Uses an :class:`anyio.create_task_group` so per-item workers run
        concurrently across distinct ``graph_id`` values while the
        per-``graph_hash`` :class:`anyio.CapacityLimiter` serializes
        same-graph work. The task group exits when ``_shutdown`` is
        observed *and* the queue has been drained -- the sentinel push
        from :meth:`stop` wakes the ``queue.get()`` so we observe the
        flag transition promptly.
        """
        async with anyio.create_task_group() as tg:
            while True:
                item = await self._queue.get()
                if item is None:
                    # Sentinel: stop() was called. The shutdown flag
                    # flipped before the push, so this is unconditional
                    # exit -- in-flight workers complete via task-group
                    # join below.
                    break
                tg.start_soon(self._run_under_limiter, item)
        # Task-group exit awaits all in-flight workers; nothing else.

    async def _run_under_limiter(self, item: QueueItem) -> None:
        """Acquire the per-``graph_hash`` limiter, dispatch, mark terminal.

        On terminal state (success or failure), removes the durable
        pending row so a restart does not replay the same work and
        writes the terminal status + duration_ms into ``runs_history``
        when a :class:`RunHistory` is wired. The limiter is released
        by exiting the ``async with`` block.
        """
        limiter = self._get_limiter(item.pending.graph_id)
        async with limiter:
            try:
                summary = await self._run_one(item)
            except BaseException as exc:
                if not item.future.done():
                    item.future.set_exception(exc)
                # Terminal: clear the pending row + record failure
                # even on exception.
                await self._clear_pending(item.pending.run_id)
                await self._record_history_terminal(item.pending.run_id, status="error")
                # Re-raise CancelledError so the task group sees the
                # cancel; other exceptions are isolated per-item (one
                # bad run does not tear down the dispatcher).
                if isinstance(exc, asyncio.CancelledError):
                    raise
                return
            if not item.future.done():
                item.future.set_result(summary)
        # Release-on-terminal-state per design §6.2: the limiter is
        # released by the ``async with`` exit above. Pending row removal
        # happens after the limiter release so the next same-graph run
        # can begin promptly.
        await self._clear_pending(item.pending.run_id)
        await self._record_history_terminal(item.pending.run_id, status=summary.status)

    async def _run_one(self, item: QueueItem) -> RunSummary:
        """Drive one run to completion. POC stub returns a synthetic summary.

        The real Phase 2 implementation (task 2.30 lifespan wiring):

        1. Loads the parent :class:`harbor.graph.Graph` via the registry
           keyed on ``item.pending.graph_id``.
        2. Constructs a :class:`harbor.graph.GraphRun` with the wired
           checkpointer + bus + capabilities.
        3. ``await run.start()`` to drive the loop and return its
           :class:`RunSummary`.

        For now, returns a synthetic terminal :class:`RunSummary` so
        cron-loop + dispatcher + limiter behavior can be verified
        without a real graph + IR + Fathom adapter. The
        ``side_effects_hash`` slot is a deterministic placeholder
        derived from the ``run_id`` so two synthetic summaries are
        distinguishable in tests; the lifespan factory replaces the
        entire body.
        """
        now = datetime.now(UTC)
        return RunSummary(
            run_id=item.pending.run_id,
            graph_hash=item.pending.graph_id,
            started_at=now,
            last_step_at=now,
            status="done",
            parent_run_id=None,
        )

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _get_limiter(self, graph_id: str) -> anyio.CapacityLimiter:
        """Return (creating if absent) the per-``graph_hash`` limiter."""
        limiter = self._limiters.get(graph_id)
        if limiter is None:
            limiter = anyio.CapacityLimiter(_DEFAULT_GRAPH_CONCURRENCY)
            self._limiters[graph_id] = limiter
        return limiter

    @staticmethod
    def _cron_idempotency_key(trigger_id: str, scheduled_fire: datetime) -> str:
        """``sha256(trigger_id || iso_fire)``; see design §6.1.

        Static so callers (cron path, tests, the catchup probe) can
        compute the key without a Scheduler instance. ISO format
        includes the tz offset so the same wall-clock-instant in
        different zones produces distinct keys (correct: a 09:00
        America/New_York fire and a 09:00 UTC fire are different
        events).
        """
        payload = f"{trigger_id}|{scheduled_fire.isoformat()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _synth_idempotency_key(graph_id: str, now: datetime) -> str:
        """Synthesize an idempotency key for callers that supply none.

        Uses ``sha256(graph_id || iso_now)`` so two enqueues at
        sub-microsecond intervals still produce distinct keys (the
        Python ``datetime.now`` resolution is microsecond on Linux).
        Manual triggers typically pass an explicit caller-supplied UUID;
        this fallback is for the FastAPI route's omitted-key path.
        """
        payload = f"{graph_id}|{now.isoformat()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _derive_run_id(graph_id: str, idempotency_key: str) -> str:
        """Stable per-pending-row run_id.

        Format ``run-{graph_id_8}-{key_12}`` keeps the id short enough
        for log lines while still globally unique across the deployment
        (graph hashes are sha256-prefixed; collisions across distinct
        graph hashes are infeasible at v1 scale). The Phase 2 lifespan
        factory may replace this with a UUID once the persisted
        ``runs`` table (task 2.14) takes ownership of run-id minting.
        """
        return f"run-{graph_id[:8]}-{idempotency_key[:12]}"

    async def _persist_pending(self, pending: PendingRun) -> None:
        """Write ``pending`` to the :class:`PendingStore`; log + swallow on error.

        Background-task entry point: the route handler does not await
        this. Failures are logged so an out-of-band monitor can surface
        them; the in-memory queue still drives the run, so a transient
        store failure does not drop work (only restart durability is
        compromised, which the admin can recover from).
        """
        if self._pending_store is None:
            return
        try:
            await self._pending_store.put_pending(pending)
        except Exception:  # pragma: no cover - defensive
            _logger.exception(
                "Scheduler._persist_pending failed for run_id=%s",
                pending.run_id,
            )

    async def _clear_pending(self, run_id: str) -> None:
        """Remove the durable pending row on terminal state."""
        if self._pending_store is None:
            return
        try:
            await self._pending_store.delete_pending(run_id)
        except Exception:  # pragma: no cover - defensive
            _logger.exception(
                "Scheduler._clear_pending failed for run_id=%s",
                run_id,
            )

    async def _record_history_pending(
        self,
        run_id: str,
        graph_hash: str,
        trigger_source: TriggerSource,
    ) -> None:
        """Insert a fresh ``runs_history`` row on enqueue (best-effort)."""
        if self._run_history is None:
            return
        try:
            await self._run_history.insert_pending(
                run_id=run_id,
                graph_hash=graph_hash,
                trigger_source=trigger_source,
            )
        except Exception:  # pragma: no cover - defensive
            _logger.exception(
                "Scheduler._record_history_pending failed for run_id=%s",
                run_id,
            )

    async def _record_history_terminal(self, run_id: str, *, status: str) -> None:
        """Update ``runs_history`` on terminal state with finished_at + duration_ms."""
        if self._run_history is None:
            self._enqueue_started_at.pop(run_id, None)
            return
        finished = datetime.now(UTC)
        started = self._enqueue_started_at.pop(run_id, None)
        duration_ms: int | None = None
        if started is not None:
            duration_ms = int((finished - started).total_seconds() * 1000)
        try:
            await self._run_history.update_status(
                run_id,
                status,
                finished_at=finished,
                duration_ms=duration_ms,
            )
        except Exception:  # pragma: no cover - defensive
            _logger.exception(
                "Scheduler._record_history_terminal failed for run_id=%s",
                run_id,
            )

    async def _replay_pending(self) -> None:
        """Replay persisted pending rows on :meth:`start`.

        For each row in :meth:`PendingStore.list_pending`, push a fresh
        :class:`QueueItem` with a new :class:`asyncio.Future` (the
        original caller's future is unrecoverable across processes).
        The dispatcher then drives each replayed run to completion and
        the terminal handler removes the row.
        """
        if self._pending_store is None:
            return
        try:
            rows: Iterable[PendingRun] = await self._pending_store.list_pending()
        except Exception:  # pragma: no cover - defensive
            _logger.exception("Scheduler._replay_pending list_pending failed")
            return
        loop = asyncio.get_running_loop()
        for row in rows:
            self._get_limiter(row.graph_id)
            future: asyncio.Future[RunSummary] = loop.create_future()
            self._queue.put_nowait(QueueItem(pending=row, future=future))
