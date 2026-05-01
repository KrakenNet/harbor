# SPDX-License-Identifier: Apache-2.0
"""Public API for the Harbor plugin system.

Re-exports the pluggy markers and the :mod:`hookspecs` module so
plugins can simply ``from harbor.plugin import hookimpl`` or
``from harbor.plugin import hookspecs``.
"""

from harbor.plugin import hookspecs
from harbor.plugin._markers import hookimpl, hookspec
from harbor.plugin.loader import build_plugin_manager

__all__ = [
    "build_plugin_manager",
    "hookimpl",
    "hookspec",
    "hookspecs",
]
