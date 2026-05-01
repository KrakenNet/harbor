# SPDX-License-Identifier: Apache-2.0
"""ContextVars and ``run_context`` manager for correlation IDs.

Note: this module lives under ``harbor.logging`` which shadows the stdlib
``logging`` package within Harbor's namespace. Code in this package must avoid
``import logging`` — use ``structlog`` directly via :mod:`harbor.logging`.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

_run_id: ContextVar[str | None] = ContextVar("harbor_run_id", default=None)
_step: ContextVar[int | None] = ContextVar("harbor_step", default=None)
_node_id: ContextVar[str | None] = ContextVar("harbor_node_id", default=None)


def get_run_id() -> str | None:
    """Return the current run_id ContextVar value (or ``None``)."""
    return _run_id.get()


def get_step() -> int | None:
    """Return the current step ContextVar value (or ``None``)."""
    return _step.get()


def get_node_id() -> str | None:
    """Return the current node_id ContextVar value (or ``None``)."""
    return _node_id.get()


@contextmanager
def run_context(run_id: str, step: int, node_id: str | None = None) -> Generator[None, None, None]:
    """Bind correlation IDs for the duration of the ``with`` block.

    Sets ``run_id``, ``step``, and (optionally) ``node_id`` ContextVars. The
    structlog processor in :mod:`harbor.logging._config` injects these into
    every log event emitted within the block. Tokens are reset on exit so
    nesting is safe.
    """
    t_run = _run_id.set(run_id)
    t_step = _step.set(step)
    t_node = _node_id.set(node_id)
    try:
        yield
    finally:
        _node_id.reset(t_node)
        _step.reset(t_step)
        _run_id.reset(t_run)
