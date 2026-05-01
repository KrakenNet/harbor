# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the Shipwright run-state schema."""

from __future__ import annotations

import pytest

from harbor.skills.shipwright.state import (
    Question,
    SpecSlot,
    State,
    VerifierResult,
)


@pytest.mark.unit
def test_state_defaults_to_new_mode() -> None:
    s = State()
    assert s.mode == "new"
    assert s.kind is None
    assert s.slots == {}
    assert s.fix_attempts == 0


@pytest.mark.unit
def test_spec_slot_records_origin() -> None:
    slot = SpecSlot(name="purpose", value="triage", origin="user")
    assert slot.confidence == 1.0
    assert slot.origin == "user"


@pytest.mark.unit
def test_question_carries_schema_and_kind() -> None:
    q = Question(
        slot="purpose",
        prompt="What is this graph for?",
        kind="required",
        schema={"type": "string"},
        origin="rule",
    )
    assert q.kind == "required"
    assert q.origin == "rule"


@pytest.mark.unit
def test_verifier_result_records_findings() -> None:
    r = VerifierResult(kind="static", passed=False, findings=[{"msg": "x"}], duration_ms=42)
    assert r.passed is False
    assert r.findings == [{"msg": "x"}]


@pytest.mark.unit
def test_state_round_trips_through_pydantic() -> None:
    s = State(mode="fix", kind="graph", brief="b", target_path="./graphs/x")
    dumped = s.model_dump()
    reloaded = State.model_validate(dumped)
    assert reloaded == s
