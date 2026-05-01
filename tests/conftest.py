# SPDX-License-Identifier: Apache-2.0
"""Shared pytest fixtures for the Harbor test suite.

Provides ``engine`` and ``adapter`` fixtures wired against Fathom v0.3.x. The
``adapter`` fixture also seeds the engine with the ``harbor_action`` deftemplate
(via :class:`harbor.fathom.FathomAdapter.register_harbor_action_template`) and
mirrors a matching :class:`fathom.models.TemplateDefinition` into the engine's
``_template_registry`` so :py:meth:`fathom.Engine.query` can read back asserted
``harbor_action`` facts -- raw ``load_clips_function`` builds the CLIPS template
but does not populate the registry by itself.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fathom import Engine
from fathom.models import ModuleDefinition, SlotDefinition, SlotType, TemplateDefinition

from harbor.fathom import FathomAdapter

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"


def _harbor_action_template_definition() -> TemplateDefinition:
    """Mirror of ``HARBOR_ACTION_DEFTEMPLATE`` for the engine's registry.

    Required so :py:meth:`fathom.Engine.query` can read ``harbor_action`` facts
    after rules fire; ``load_clips_function`` only registers in CLIPS itself,
    not in the Python-side ``_template_registry``.
    """
    return TemplateDefinition(
        name="harbor_action",
        slots=[
            SlotDefinition(
                name="kind",
                type=SlotType.SYMBOL,
                allowed_values=["goto", "parallel", "halt", "retry", "assert", "retract"],
            ),
            SlotDefinition(name="target", type=SlotType.STRING, default=""),
            SlotDefinition(name="reason", type=SlotType.STRING, default=""),
            SlotDefinition(name="rule_id", type=SlotType.STRING, default=""),
            SlotDefinition(name="step", type=SlotType.INTEGER, default=0),
            SlotDefinition(name="targets", type=SlotType.STRING),
            SlotDefinition(name="join", type=SlotType.STRING, default=""),
            SlotDefinition(
                name="strategy",
                type=SlotType.SYMBOL,
                allowed_values=["all", "any", "race", "quorum"],
                default="all",
            ),
            SlotDefinition(name="backoff_ms", type=SlotType.INTEGER, default=0),
            SlotDefinition(name="fact", type=SlotType.STRING, default=""),
            SlotDefinition(name="slots", type=SlotType.STRING, default=""),
            SlotDefinition(name="pattern", type=SlotType.STRING, default=""),
        ],
    )


def _evidence_template_definition() -> TemplateDefinition:
    """User template carrying provenance slots plus a payload (field, value).

    Slot types are chosen to match what
    :func:`harbor.fathom._provenance._sanitize_provenance_slot` returns for the
    standard provenance bundle: ``_step`` is an int; everything else is a string.
    """
    return TemplateDefinition(
        name="evidence",
        slots=[
            SlotDefinition(name="_origin", type=SlotType.STRING),
            SlotDefinition(name="_source", type=SlotType.STRING),
            SlotDefinition(name="_run_id", type=SlotType.STRING),
            SlotDefinition(name="_step", type=SlotType.INTEGER),
            SlotDefinition(name="_confidence", type=SlotType.STRING),
            SlotDefinition(name="_timestamp", type=SlotType.STRING),
            SlotDefinition(name="field", type=SlotType.STRING),
            SlotDefinition(name="value", type=SlotType.STRING),
        ],
    )


def _build_evidence_clips(defn: TemplateDefinition) -> str:
    """Build a CLIPS deftemplate for the ``evidence`` template.

    Uses the same compile path Fathom would use for a YAML template, but
    inline (avoids an extra fixture file for a single template).
    """
    from fathom.compiler import Compiler

    return Compiler().compile_template(defn)


@pytest.fixture
def engine() -> Engine:
    """Fresh Fathom engine for every test (deny by default, fail-closed)."""
    return Engine(default_decision="deny")


def _register_poc_module(engine: Engine) -> None:
    """Register a ``poc`` module so the POC ruleset can compile against it.

    ``Engine.load_modules`` does this when reading a YAML modules file; here we
    short-circuit to a single inline call so the only fixture file on disk is
    the rules YAML the task specifies. Mirrors ``load_modules``: ensures
    ``MAIN`` is built (with ``?ALL`` export) before any non-MAIN module, then
    builds the ``poc`` module and records it in ``_module_registry``.
    """
    if not engine._module_registry:  # pyright: ignore[reportPrivateUsage]
        engine._safe_build(  # pyright: ignore[reportPrivateUsage]
            "(defmodule MAIN (export ?ALL))",
            context="module:MAIN",
        )
    poc_defn = ModuleDefinition(name="poc", description="Harbor POC smoke ruleset")
    engine._safe_build(  # pyright: ignore[reportPrivateUsage]
        "(defmodule poc (import MAIN ?ALL))",
        context="module:poc",
    )
    engine._module_registry["poc"] = poc_defn  # pyright: ignore[reportPrivateUsage]
    engine.set_focus(["poc"])


@pytest.fixture
def adapter(engine: Engine) -> FathomAdapter:
    """``FathomAdapter`` wired to a fresh engine with templates and module seeded.

    Seeds four things needed for the POC smoke:

    1. ``harbor_action`` deftemplate in CLIPS (via the adapter API).
    2. ``harbor_action`` :class:`TemplateDefinition` in the engine's registry
       so ``engine.query("harbor_action", None)`` returns rows.
    3. ``evidence`` template (CLIPS deftemplate + registry entry) so user
       fixtures can call ``engine.assert_fact("evidence", ...)``.
    4. ``poc`` module (CLIPS defmodule + registry entry) so the rules YAML
       loaded by individual tests can compile against it.
    """
    adapter_ = FathomAdapter(engine)
    adapter_.register_harbor_action_template()
    engine._template_registry[  # pyright: ignore[reportPrivateUsage]
        "harbor_action"
    ] = _harbor_action_template_definition()

    evidence_defn = _evidence_template_definition()
    engine.load_clips_function(_build_evidence_clips(evidence_defn))
    engine._template_registry["evidence"] = evidence_defn  # pyright: ignore[reportPrivateUsage]

    _register_poc_module(engine)

    return adapter_
