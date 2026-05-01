# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the lifespan-singleton :class:`nautilus.Broker` (FR-47, AC-6.1, design §8.3).

The lifespan factory builds the :class:`nautilus.Broker` from
``<harbor-config>/nautilus.yaml`` once at startup, stashes it on the
:data:`harbor.serve.contextvars._broker_var` ContextVar, and clears it
on teardown. The :func:`harbor.serve.contextvars.current_broker`
accessor lifts an unset contextvar into a typed
:class:`HarborRuntimeError` so consumers (BrokerNode, broker_request
tool) fail loudly outside an active lifespan.

The RED-test invariants:

1. ``current_broker()`` returns the wired :class:`Broker` instance from
   inside an active lifespan (simulated by entering the
   :func:`harbor.serve.lifecycle.broker_lifespan` async context manager).
2. ``current_broker()`` outside the lifespan raises
   :class:`HarborRuntimeError`.
3. Missing ``<harbor-config>/nautilus.yaml`` logs a warning (stderr or
   the harbor logger sink) but does not crash the lifespan -- Nautilus
   is optional, the app must still boot.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

from harbor.errors import HarborRuntimeError
from harbor.serve.contextvars import _broker_var, current_broker
from harbor.serve.lifecycle import broker_lifespan

if TYPE_CHECKING:
    from pathlib import Path


_QUICKSTART_YAML = """
sources:
  - id: vuln_db
    type: postgres
    description: "Vulnerability database"
    classification: unclassified
    data_types: [cve, vulnerability, patch]
    allowed_purposes: [threat-analysis, incident-response]
    connection: "postgresql://example/db"
    table: vulnerabilities

agents:
  analyst:
    id: analyst
    clearance: unclassified
    compartments: []
    default_purpose: threat-analysis

rules:
  user_rules_dirs: []

analysis:
  mode: pattern
  keyword_map:
    vulnerability: [vulnerability, vuln, cve, weakness]

audit:
  path: ./audit.jsonl

attestation:
  enabled: false

api:
  keys:
    - test-key
"""


@pytest.mark.asyncio
async def test_current_broker_inside_lifespan_returns_broker(
    tmp_path: Path,
) -> None:
    """Entering :func:`broker_lifespan` must wire the contextvar to a Broker."""
    config_dir = tmp_path / "harbor"
    config_dir.mkdir()
    (config_dir / "nautilus.yaml").write_text(_QUICKSTART_YAML, encoding="utf-8")

    async with broker_lifespan(config_dir=config_dir):
        broker = current_broker()
        assert broker is not None
        # The broker is the live nautilus.Broker; expose the public
        # attribute set so we know we got the real object.
        assert hasattr(broker, "arequest")
        assert hasattr(broker, "agent_registry")

    # After the context exits the var must be cleared again -- the
    # accessor lifts the unset state into HarborRuntimeError.
    with pytest.raises(HarborRuntimeError):
        current_broker()


@pytest.mark.asyncio
async def test_current_broker_outside_lifespan_raises() -> None:
    """``current_broker()`` outside an active lifespan raises HarborRuntimeError."""
    # The contextvar default is None at module load time and stays
    # None until a lifespan sets it.
    assert _broker_var.get() is None
    with pytest.raises(HarborRuntimeError):
        current_broker()


@pytest.mark.asyncio
async def test_missing_nautilus_yaml_warns_but_does_not_crash(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Missing ``nautilus.yaml`` must log a warning but not raise."""
    # config_dir exists but has no nautilus.yaml: Nautilus is optional;
    # the app still boots.
    config_dir = tmp_path / "harbor-empty"
    config_dir.mkdir()

    with caplog.at_level(logging.WARNING, logger="harbor.serve.lifecycle"):
        async with broker_lifespan(config_dir=config_dir):
            # Inside the lifespan: the broker var stays unset because
            # construction was skipped. current_broker() raises.
            with pytest.raises(HarborRuntimeError):
                current_broker()

    # Warning surfaced (full text optional; presence of the path is
    # the diagnostic check).
    warning_messages = [r.getMessage() for r in caplog.records]
    assert any("nautilus.yaml" in m for m in warning_messages), (
        f"expected nautilus.yaml warning; got {warning_messages!r}"
    )
