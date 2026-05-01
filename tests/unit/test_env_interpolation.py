# SPDX-License-Identifier: Apache-2.0
"""``${VAR}`` env interpolation post-YAML, pre-validation (FR-19, NFR-9).

Bootstrap order:

1. YAML -> dict (caller's responsibility).
2. :func:`harbor.plugin._config.interpolate_env` resolves every
   ``${VAR}`` placeholder against ``os.environ``.
3. :func:`harbor.plugin._config.validate_config` runs the resulting
   payload through the StoreSpec.config_schema.

Step 2 must come before step 3 so the validator never sees a literal
``${HARBOR_DB_PATH}`` string -- it always sees the resolved value.
Missing variables are loud (NFR-9): unresolved placeholders raise
:class:`harbor.errors.ValidationError`.
"""

from __future__ import annotations

import pytest

from harbor.errors import ValidationError
from harbor.plugin._config import interpolate_env

pytestmark = [pytest.mark.knowledge, pytest.mark.unit]


def test_interpolate_env_resolves_top_level_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """A bare ``${HARBOR_DB_PATH}`` value resolves from ``os.environ``."""
    monkeypatch.setenv("HARBOR_DB_PATH", "/var/lib/harbor/db")
    out = interpolate_env("${HARBOR_DB_PATH}")
    assert out == "/var/lib/harbor/db"


def test_interpolate_env_substitutes_inside_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """Placeholders inside larger strings are substituted in-place."""
    monkeypatch.setenv("HARBOR_DB_PATH", "/var/lib/harbor")
    out = interpolate_env("${HARBOR_DB_PATH}/vectors.lance")
    assert out == "/var/lib/harbor/vectors.lance"


def test_interpolate_env_recurses_into_dicts_and_lists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nested dict/list payloads are walked recursively."""
    monkeypatch.setenv("HARBOR_DB_PATH", "/data")
    monkeypatch.setenv("HARBOR_TABLE", "vectors")
    payload = {
        "path": "${HARBOR_DB_PATH}/db",
        "tables": ["${HARBOR_TABLE}", "facts"],
        "nested": {"target": "${HARBOR_DB_PATH}"},
    }
    out = interpolate_env(payload)
    assert out == {
        "path": "/data/db",
        "tables": ["vectors", "facts"],
        "nested": {"target": "/data"},
    }


def test_interpolate_env_preserves_non_string_leaves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-string leaves (int, bool, None) pass through unchanged."""
    monkeypatch.setenv("HARBOR_DB_PATH", "/data")
    payload: dict[str, object] = {
        "path": "${HARBOR_DB_PATH}",
        "port": 5432,
        "tls": True,
        "extra": None,
    }
    out = interpolate_env(payload)
    assert out == {"path": "/data", "port": 5432, "tls": True, "extra": None}


def test_interpolate_env_missing_var_raises_loud(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unresolved ``${VAR}`` raises :class:`ValidationError` with var name."""
    monkeypatch.delenv("HARBOR_DB_PATH", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        interpolate_env("${HARBOR_DB_PATH}/db")
    err = exc_info.value
    assert err.context["var"] == "HARBOR_DB_PATH"
    assert "HARBOR_DB_PATH" in err.message


def test_interpolate_env_preserves_keys_only_substitutes_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dict keys are not interpolated -- only values."""
    monkeypatch.setenv("HARBOR_DB_PATH", "/data")
    # The literal string '${HARBOR_DB_PATH}' as a *key* must survive
    # untouched so schemas with field names never collide with env vars.
    payload = {"${HARBOR_DB_PATH}": "${HARBOR_DB_PATH}"}
    out = interpolate_env(payload)
    assert out == {"${HARBOR_DB_PATH}": "/data"}


def test_interpolate_env_no_placeholders_is_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Strings without ``${VAR}`` placeholders are returned untouched."""
    monkeypatch.delenv("HARBOR_DB_PATH", raising=False)
    out = interpolate_env({"plain": "value", "n": 1})
    assert out == {"plain": "value", "n": 1}
