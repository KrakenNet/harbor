# SPDX-License-Identifier: Apache-2.0
"""Mirror lifecycle scheduler -- engine-side enforcer of ``Mirror.lifecycle`` (FR-2).

Foundation's :class:`harbor.ir.Mirror` annotation tags state fields with
``lifecycle: Literal["run", "step", "pinned"]`` (FR-13, FR-14). Foundation only
declares the marker and resolves field-name templates via
:func:`harbor.ir.mirrored_fields`; **the engine is responsible for enforcing
lifecycle semantics at runtime boundaries** (requirements glossary
``lifecycle (Mirror)``).

This module provides :class:`MirrorScheduler`, the engine's lifecycle bucket:

* ``schedule(specs, lifecycle=...)`` -- record :class:`fathom.AssertSpec`
  instances in the named lifecycle bucket. Called from the execution loop
  (design §3.1.2 step 3) after :meth:`harbor.fathom.FathomAdapter.mirror_state`
  produces specs from the post-merge state.
* ``retract_step()`` -- clear the ``step`` bucket. Called at the node boundary
  (design §3.1.2 step 8) so step-scoped mirrors do not bleed across nodes.
* ``persist_pinned()`` -- flush the ``pinned`` bucket to the FactStore. Phase 3
  fills the FactStore call (knowledge spec) -- v1 ships a stub that records
  intent but does not persist.

The ``run`` bucket is held for the lifetime of the GraphRun and is cleared
neither at node boundary nor at run end (the engine is expected to drop the
scheduler instance with the run). v1 is in-memory only -- no checkpoint
restore is wired here; checkpoint integration is a Phase 3 concern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import fathom

    from harbor.ir._mirror import Lifecycle

__all__ = ["MirrorScheduler"]


class MirrorScheduler:
    """In-memory lifecycle bucket for mirrored :class:`fathom.AssertSpec` instances.

    One instance per :class:`harbor.GraphRun`. Buckets are append-only within a
    lifecycle (no de-duplication in v1 -- duplicate templates are the engine's
    responsibility to handle at assert time, since Fathom's deftemplate semantics
    treat each ``assert_fact`` as a fresh fact). The scheduler is the
    engine-side authority on **when** to retract or persist; it does not itself
    call into :class:`~harbor.fathom.FathomAdapter` (the loop owns that
    interaction so back-pressure and ``asyncio.to_thread`` semantics stay
    visible at the call site).
    """

    __slots__ = ("_pinned", "_run", "_step")

    def __init__(self) -> None:
        self._run: list[fathom.AssertSpec] = []
        self._step: list[fathom.AssertSpec] = []
        self._pinned: list[fathom.AssertSpec] = []

    def schedule(self, specs: list[fathom.AssertSpec], lifecycle: Lifecycle) -> None:
        """Record ``specs`` in the bucket named by ``lifecycle``.

        ``lifecycle`` is the boundary scope at which these specs apply. The
        :class:`harbor.ir.ResolvedMirror.lifecycle` field on each Mirror
        annotation determines which bucket the loop should pass for each
        field (resolution happens upstream in
        :func:`harbor.ir.mirrored_fields`); this method is the bucket sink.
        """
        if lifecycle == "run":
            self._run.extend(specs)
        elif lifecycle == "step":
            self._step.extend(specs)
        else:  # "pinned"
            self._pinned.extend(specs)

    def retract_step(self) -> None:
        """Clear the ``step`` bucket -- called at every node boundary.

        Per requirements glossary ``lifecycle (Mirror)``: step-scoped mirrors
        must be retracted at the node boundary so they do not bleed across
        nodes. The execution loop (design §3.1.2 step 8) calls this after the
        transition event is emitted and the checkpoint write completes.
        """
        self._step.clear()

    def persist_pinned(self) -> None:
        """Flush the ``pinned`` bucket to the FactStore (Phase 3).

        v1 stub: pinned specs are recorded by :meth:`schedule` but not yet
        persisted. The FactStore protocol lives in the harbor-knowledge spec
        and is wired up in Phase 3 of harbor-engine; until then this method
        is a no-op (specs remain in the in-memory bucket, available for
        introspection but not durable across runs).

        TODO(harbor-knowledge): replace this stub with a FactStore.write_batch
        call and clear ``self._pinned`` on success.
        """
        # Phase 3 stub -- FactStore integration deferred (knowledge spec).
        return
