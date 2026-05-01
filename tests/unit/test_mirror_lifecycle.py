# SPDX-License-Identifier: Apache-2.0
"""Mirror lifecycle scheduler -- bucket semantics + boundary retraction (FR-2, FR-13).

Pins the engine-side enforcement of ``Mirror.lifecycle`` semantics
(:class:`harbor.runtime.mirror_lifecycle.MirrorScheduler`):

* ``"step"`` mirrors are retracted at every node boundary
  (``retract_step()``); they do not bleed across nodes.
* ``"run"`` mirrors persist for the lifetime of the GraphRun and are not
  cleared by ``retract_step`` nor by ``persist_pinned``.
* ``"pinned"`` mirrors are scheduled into a separate bucket; the v1
  ``persist_pinned()`` is a documented stub (the FactStore wiring lands in
  Phase 3 of the knowledge spec) -- the in-memory bucket survives both
  step retraction and the persist call so introspection still works.
* The ``run`` bucket is held for the lifetime of the scheduler instance
  (engine drops the scheduler with the run; per-run identity is enforced
  upstream in :mod:`harbor.graph.run`).
"""

from __future__ import annotations

import fathom
import pytest

from harbor.runtime.mirror_lifecycle import MirrorScheduler


def _spec(template: str = "tpl", value: str = "v") -> fathom.AssertSpec:
    """Build a minimal :class:`fathom.AssertSpec` for bucket round-trips."""
    return fathom.AssertSpec(template=template, slots={"value": value})


# ---------------------------------------------------------------------------
# schedule + bucket isolation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_scheduler_starts_with_empty_buckets() -> None:
    """A fresh scheduler has empty ``run``/``step``/``pinned`` buckets."""
    sched = MirrorScheduler()
    assert sched._run == []  # pyright: ignore[reportPrivateUsage]
    assert sched._step == []  # pyright: ignore[reportPrivateUsage]
    assert sched._pinned == []  # pyright: ignore[reportPrivateUsage]


@pytest.mark.unit
def test_schedule_routes_specs_to_the_named_bucket() -> None:
    """``schedule(specs, lifecycle=X)`` appends to the ``X`` bucket only."""
    sched = MirrorScheduler()
    s_run = _spec("run_t")
    s_step = _spec("step_t")
    s_pinned = _spec("pinned_t")
    sched.schedule([s_run], lifecycle="run")
    sched.schedule([s_step], lifecycle="step")
    sched.schedule([s_pinned], lifecycle="pinned")
    assert sched._run == [s_run]  # pyright: ignore[reportPrivateUsage]
    assert sched._step == [s_step]  # pyright: ignore[reportPrivateUsage]
    assert sched._pinned == [s_pinned]  # pyright: ignore[reportPrivateUsage]


@pytest.mark.unit
def test_schedule_appends_in_call_order_no_dedup_in_v1() -> None:
    """v1 buckets are append-only with no de-duplication."""
    sched = MirrorScheduler()
    s1 = _spec("t", "v1")
    s2 = _spec("t", "v2")
    sched.schedule([s1, s2], lifecycle="run")
    sched.schedule([s1], lifecycle="run")  # duplicate template, distinct slot value
    assert sched._run == [s1, s2, s1]  # pyright: ignore[reportPrivateUsage]


# ---------------------------------------------------------------------------
# retract_step boundary semantics (FR-2)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_retract_step_clears_only_step_bucket() -> None:
    """``retract_step()`` clears ``step`` while leaving ``run`` and ``pinned``
    untouched (per-glossary lifecycle definition)."""
    sched = MirrorScheduler()
    s_run = _spec("run_t")
    s_step = _spec("step_t")
    s_pinned = _spec("pinned_t")
    sched.schedule([s_run], lifecycle="run")
    sched.schedule([s_step], lifecycle="step")
    sched.schedule([s_pinned], lifecycle="pinned")

    sched.retract_step()

    assert sched._step == []  # pyright: ignore[reportPrivateUsage]
    assert sched._run == [s_run]  # pyright: ignore[reportPrivateUsage]
    assert sched._pinned == [s_pinned]  # pyright: ignore[reportPrivateUsage]


@pytest.mark.unit
def test_step_mirrors_do_not_bleed_across_node_boundaries() -> None:
    """Simulate two node boundaries: step specs scheduled for node A must be
    gone by the time node B's step specs land."""
    sched = MirrorScheduler()
    a_step = _spec("node_a_step")
    sched.schedule([a_step], lifecycle="step")
    sched.retract_step()  # node boundary fires (design §3.1.2 step 8)

    b_step = _spec("node_b_step")
    sched.schedule([b_step], lifecycle="step")
    assert sched._step == [b_step]  # pyright: ignore[reportPrivateUsage]
    assert a_step not in sched._step  # pyright: ignore[reportPrivateUsage]


@pytest.mark.unit
def test_repeated_retract_step_is_idempotent() -> None:
    """Calling ``retract_step`` on an already-empty step bucket is a no-op."""
    sched = MirrorScheduler()
    sched.retract_step()
    sched.retract_step()
    assert sched._step == []  # pyright: ignore[reportPrivateUsage]


# ---------------------------------------------------------------------------
# run + pinned persistence
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_run_bucket_persists_across_many_step_boundaries() -> None:
    """``run`` mirrors last for the whole scheduler lifetime; many node
    boundaries do not clear them."""
    sched = MirrorScheduler()
    s_run = _spec("session_token")
    sched.schedule([s_run], lifecycle="run")
    for _ in range(10):
        sched.schedule([_spec("step_only")], lifecycle="step")
        sched.retract_step()
    assert sched._run == [s_run]  # pyright: ignore[reportPrivateUsage]


@pytest.mark.unit
def test_persist_pinned_is_v1_stub_and_does_not_clear_bucket() -> None:
    """v1 ``persist_pinned()`` is documented as a no-op stub: the in-memory
    pinned bucket remains populated for introspection (FactStore wiring lands
    in Phase 3 of the knowledge spec)."""
    sched = MirrorScheduler()
    s_pinned = _spec("user_pref")
    sched.schedule([s_pinned], lifecycle="pinned")
    assert sched.persist_pinned() is None
    # Stub does not clear; pinned spec is still available for inspection.
    assert sched._pinned == [s_pinned]  # pyright: ignore[reportPrivateUsage]


@pytest.mark.unit
def test_pinned_bucket_survives_step_retraction() -> None:
    """``pinned`` specs persist across node boundaries (only ``step`` is cleared)."""
    sched = MirrorScheduler()
    s_pinned = _spec("preference")
    sched.schedule([s_pinned], lifecycle="pinned")
    for _ in range(5):
        sched.retract_step()
    assert sched._pinned == [s_pinned]  # pyright: ignore[reportPrivateUsage]


@pytest.mark.unit
def test_buckets_are_independent_lists() -> None:
    """Mutating the input ``specs`` list after ``schedule`` does not retro-edit
    the bucket (the scheduler ``extend``s; it does not retain the caller's list)."""
    sched = MirrorScheduler()
    inputs = [_spec("a")]
    sched.schedule(inputs, lifecycle="run")
    inputs.append(_spec("b"))
    assert len(sched._run) == 1  # pyright: ignore[reportPrivateUsage]
