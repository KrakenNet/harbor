# SPDX-License-Identifier: Apache-2.0
"""Harbor exception hierarchy.

All Harbor errors inherit from :class:`HarborError`, which carries a
human-readable ``message`` plus arbitrary keyword ``context`` for
structured logging. Subclasses are pass-through: they exist purely so
callers can pattern-match on category.
"""

from __future__ import annotations

from typing import Any


class HarborError(Exception):
    """Base class for all Harbor exceptions.

    Stores ``message`` (the user-facing string) and ``context`` (a dict
    populated from keyword arguments) for structured logging downstream.
    """

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(message)
        self.message: str = message
        self.context: dict[str, Any] = context


class ValidationError(HarborError):
    """Raised when input fails Harbor validation rules."""


class PluginLoadError(HarborError):
    """Raised when a Harbor plugin cannot be discovered or imported."""


class HarborRuntimeError(HarborError):
    """Raised for runtime failures inside Harbor.

    Renamed to avoid shadowing builtin RuntimeError.
    """


class CheckpointError(HarborError):
    """Raised when checkpoint write/read fails."""


class ReplayError(HarborError):
    """Raised when replaying a recorded run fails."""
