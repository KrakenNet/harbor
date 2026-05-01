# SPDX-License-Identifier: Apache-2.0
# ruff: noqa: E501  -- design table rows in module docstring intentionally wide
"""Action vocabulary translation tests (design §3.1.4, Learning F).

Pins the 5-row translation table from design §3.1.4 that maps the five
native Fathom action verbs (``allow``, ``deny``, ``escalate``, ``scope``,
``route``) to the corresponding :data:`~harbor.runtime.action.RoutingDecision`
variant produced by :func:`~harbor.runtime.action.translate_actions` after
:func:`~harbor.fathom.extract_actions` has lifted ``harbor_action`` fact slot
dicts into typed IR :data:`~harbor.fathom.Action` instances.

Covered rows (design §3.1.4 table):

| Fathom native            | Engine action                    | Routing semantics                              |
|--------------------------|----------------------------------|------------------------------------------------|
| ``harbor_action.allow``  | continue current edge            | :class:`ContinueAction`                        |
| ``harbor_action.deny``   | halt                             | :class:`HaltAction(reason="denied-by-rule")`   |
| ``harbor_action.escalate`` | route to escalation target     | :class:`GotoAction(target=escalation_target)`  |
| ``harbor_action.scope``  | filter state, continue           | :class:`ContinueAction` (scope is adapter-side)|
| ``harbor_action.route``  | route to target                  | :class:`GotoAction(target=target)`             |
"""

from __future__ import annotations

from typing import Any

import pytest

from harbor.fathom import extract_actions
from harbor.runtime.action import (
    ContinueAction,
    GotoAction,
    HaltAction,
    RoutingDecision,
    translate_actions,
)


def _translate(facts: list[dict[str, Any]]) -> RoutingDecision:
    """Adapter+translator end-to-end: facts → IR Actions → RoutingDecision."""
    return translate_actions(extract_actions(facts))


@pytest.mark.unit
def test_allow_translates_to_continue() -> None:
    """``harbor_action.allow`` → :class:`ContinueAction` (walk static edge)."""
    decision = _translate([{"kind": "allow"}])
    assert isinstance(decision, ContinueAction)
    assert decision.kind == "continue"


@pytest.mark.unit
def test_deny_translates_to_halt_with_denied_by_rule_reason() -> None:
    """``harbor_action.deny`` → :class:`HaltAction(reason="denied-by-rule")`."""
    decision = _translate([{"kind": "deny"}])
    assert isinstance(decision, HaltAction)
    assert decision.reason == "denied-by-rule"


@pytest.mark.unit
def test_escalate_translates_to_goto_escalation_target() -> None:
    """``harbor_action.escalate`` → :class:`GotoAction(target=escalation_target)`."""
    decision = _translate([{"kind": "escalate", "escalation_target": "human_review"}])
    assert isinstance(decision, GotoAction)
    assert decision.target == "human_review"


@pytest.mark.unit
def test_scope_translates_to_continue() -> None:
    """``harbor_action.scope`` → :class:`ContinueAction` (state-filter is adapter-layer; no routing change)."""
    decision = _translate([{"kind": "scope", "scope": "tenant_a"}])
    assert isinstance(decision, ContinueAction)
    assert decision.kind == "continue"


@pytest.mark.unit
def test_route_translates_to_goto_target() -> None:
    """``harbor_action.route`` → :class:`GotoAction(target=target)`."""
    decision = _translate([{"kind": "route", "target": "fallback_node"}])
    assert isinstance(decision, GotoAction)
    assert decision.target == "fallback_node"


@pytest.mark.unit
def test_translation_table_exhaustive_five_rows() -> None:
    """Parametric pin: all five design §3.1.4 rows produce the expected variant.

    The table is reproduced inline so the test fails loudly if any future
    refactor changes the mapping without updating both call sites.
    """
    cases: list[tuple[dict[str, Any], type[RoutingDecision]]] = [
        ({"kind": "allow"}, ContinueAction),
        ({"kind": "deny"}, HaltAction),
        (
            {"kind": "escalate", "escalation_target": "t"},
            GotoAction,
        ),
        ({"kind": "scope", "scope": "s"}, ContinueAction),
        ({"kind": "route", "target": "t"}, GotoAction),
    ]
    for fact, expected_type in cases:
        decision = _translate([fact])
        assert isinstance(decision, expected_type), (
            f"{fact['kind']!r} expected {expected_type.__name__}, got {type(decision).__name__}"
        )
