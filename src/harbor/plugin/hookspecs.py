# SPDX-License-Identifier: Apache-2.0
"""Hook specifications for the Harbor plugin system.

Declarations only: every function body is ``pass``. Pluggy uses these
signatures as the contract that plugin implementations must match.

``authorize_action`` uses ``firstresult=True`` so the first non-``None``
result wins, supporting Bosun's first-deny authorisation semantics. The
``register_*`` collect-all hooks intentionally omit ``firstresult`` so
every plugin's contributions are aggregated.

.. note::
   ``PluginManager``, ``ToolCall``, ``ToolResult``, ``StoreSpec`` and
   ``PackSpec`` do not yet exist in the POC and are aliased to
   :data:`Any` below. Phase 2 will introduce concrete types and tighten
   these signatures.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from harbor.plugin._markers import hookspec

if TYPE_CHECKING:
    from harbor.ir._models import SkillSpec, ToolSpec

# TODO(phase-2): replace these ``Any`` aliases with the real domain
# types once they land (PluginManager from the loader, ToolCall /
# ToolResult from the runtime, StoreSpec / PackSpec from the registry).
type PluginManager = Any
type ToolCall = Any
type ToolResult = Any
type StoreSpec = Any
type PackSpec = Any


@hookspec
def harbor_startup(pm: PluginManager) -> None:
    """Lifecycle: invoked once after the plugin manager finishes loading."""


@hookspec
def harbor_shutdown(pm: PluginManager) -> None:
    """Lifecycle: invoked once during graceful shutdown."""


@hookspec
def register_tools() -> list[ToolSpec]:
    """Collect-all: each plugin returns the tools it provides."""
    return []


@hookspec
def before_tool_call(call: ToolCall) -> None:
    """Observation hook fired immediately before a tool invocation."""


@hookspec
def after_tool_call(call: ToolCall, result: ToolResult) -> None:
    """Observation hook fired immediately after a tool invocation."""


@hookspec
def register_skills() -> list[SkillSpec]:
    """Collect-all: each plugin returns the skills it provides."""
    return []


@hookspec
def register_stores() -> list[StoreSpec]:
    """Collect-all: each plugin returns the stores it provides."""
    return []


@hookspec
def register_packs() -> list[PackSpec]:
    """Collect-all: each plugin returns the packs it provides."""
    return []


@hookspec(firstresult=True)
def authorize_action(action: dict[str, Any]) -> bool | None:
    """Authorisation hook: first non-``None`` result wins.

    Returning ``False`` denies, ``True`` allows, ``None`` abstains so
    the next plugin gets a turn. Implements Bosun first-deny semantics.
    """


# Expose ``firstresult`` as a direct attribute on each hookspec function
# (pluggy stashes its config inside ``<project>_spec`` dicts, but Harbor
# exposes a stable boolean attribute so callers and tests can inspect a
# hookspec's collect semantics without reaching into pluggy internals).
authorize_action.firstresult = True  # type: ignore[attr-defined]
for _hook in (
    harbor_startup,
    harbor_shutdown,
    register_tools,
    before_tool_call,
    after_tool_call,
    register_skills,
    register_stores,
    register_packs,
):
    _hook.firstresult = False  # type: ignore[attr-defined]
del _hook
