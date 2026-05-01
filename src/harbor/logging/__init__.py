# SPDX-License-Identifier: Apache-2.0
"""Harbor logging — structlog with ContextVar correlation.

This package shadows the stdlib ``logging`` package within Harbor's namespace.
Internal modules avoid ``import logging`` and use structlog directly.
"""

from ._config import get_logger
from ._context import run_context

__all__ = ["get_logger", "run_context"]
