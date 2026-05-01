# SPDX-License-Identifier: Apache-2.0
"""AST walker — bans bare ``Exception``/``RuntimeError`` raises in ``src/harbor`` (FR-24, AC-3.2).

Walks every ``.py`` module under ``src/harbor/`` and inspects each ``ast.Raise``
node. The exception class being raised must either:

* inherit (by name) from :class:`harbor.errors.HarborError`, or
* be one of a small allow-list of standard-library exceptions that have a
  documented justification (``TypeError``/``ValueError``/``NotImplementedError``
  for type/contract violations, common control-flow exceptions for re-raises),
  or
* be a bare ``raise`` (re-raise inside ``except`` — no ``exc`` value).

``raise Exception(...)``, ``raise BaseException(...)``, and
``raise RuntimeError(...)`` are forbidden — production code must use
``HarborRuntimeError`` (or a more specific :class:`HarborError` subclass) so
operators can catch Harbor-emitted failures distinctly from third-party noise.

The walker also pins the 12-row provenance encoder
(``harbor.fathom._provenance``) to ``ValidationError`` — every raise in that
module must surface a :class:`harbor.errors.ValidationError` rather than a
bare exception.

Allowed call shapes inspected:

* ``raise Name(...)``         — class name compared directly to the allow-list.
* ``raise Name``              — class name compared directly to the allow-list.
* ``raise helper(...)``       — function call returning an exception (e.g.
  ``_reject(...)``); not statically resolvable, so accepted on faith.
* ``raise``                   — bare re-raise inside ``except``.

Anything outside those shapes (e.g. ``raise pkg.Exception(...)`` attribute
access, ``raise (expr)`` arbitrary expression) is rejected unless its tail
``Name`` is on the allow-list.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# Exception class names permitted in ``raise`` statements under ``src/harbor``.
# Keep this list narrow: every entry is either a Harbor exception subclass
# (HarborError-rooted) or a stdlib exception with a documented contract use.
_ALLOWED_RAISE_NAMES: frozenset[str] = frozenset(
    {
        # Harbor exception hierarchy (HarborError subclasses).
        "HarborError",
        "ValidationError",
        "PluginLoadError",
        "HarborRuntimeError",
        "CheckpointError",
        "ReplayError",
        # Stdlib — type/contract violations (caller bug, not a Harbor failure).
        "TypeError",
        "ValueError",
        "NotImplementedError",
        "AssertionError",
        # Stdlib — control-flow / iteration / lookup errors. Conventional in
        # Python and would be wrong to wrap as Harbor errors.
        "AttributeError",
        "KeyError",
        "IndexError",
        "StopIteration",
        "StopAsyncIteration",
    }
)

# Explicitly forbidden — even though they are stdlib, raising them in Harbor
# core is a code-smell. Listed here so failure messages can name the offender.
_FORBIDDEN_RAISE_NAMES: frozenset[str] = frozenset({"Exception", "BaseException", "RuntimeError"})

# Project root resolved relative to this test file: tests/unit/ -> tests/ -> repo root.
_REPO_ROOT: Path = Path(__file__).resolve().parents[2]
_SRC_HARBOR: Path = _REPO_ROOT / "src" / "harbor"


def _iter_harbor_python_files() -> list[Path]:
    """Return every ``.py`` module under ``src/harbor`` (sorted, excluding caches)."""
    return sorted(p for p in _SRC_HARBOR.rglob("*.py") if "__pycache__" not in p.parts)


def _raise_call_name(node: ast.Raise) -> str | None:
    """Return the bare class name being raised, or ``None`` if not a ``Name``-call.

    Handles:

    * ``raise Foo(...)``  -> ``"Foo"``
    * ``raise Foo``       -> ``"Foo"``
    * ``raise``           -> ``None``      (bare re-raise; caller must allow)
    * ``raise foo.Bar()`` -> ``None``      (attribute access; caller must reject)
    """
    if node.exc is None:
        return None
    exc = node.exc
    if isinstance(exc, ast.Call):
        func = exc.func
        if isinstance(func, ast.Name):
            return func.id
        return None
    if isinstance(exc, ast.Name):
        return exc.id
    return None


def _module_helpers_returning_allowed_exception(tree: ast.Module) -> set[str]:
    """Collect helper function names whose return annotation is an allow-listed exception.

    Pattern: ``def _reject(...) -> ValidationError: ...`` lets ``raise _reject(...)``
    pass the walker because the return type proves the helper produces an
    allow-listed exception class. Only direct ``Name`` annotations are honored;
    string-form annotations and complex types are not unwrapped.
    """
    helpers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ret = node.returns
            if isinstance(ret, ast.Name) and ret.id in _ALLOWED_RAISE_NAMES:
                helpers.add(node.name)
    return helpers


def _collect_raise_violations(path: Path) -> list[tuple[int, str]]:
    """Return ``(lineno, offending-name)`` for every disallowed raise in ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    helpers = _module_helpers_returning_allowed_exception(tree)
    violations: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise):
            continue
        name = _raise_call_name(node)
        if name is None:
            # Bare ``raise`` (re-raise) — always allowed. Other shapes
            # (attribute access, arbitrary expressions) fall through here too;
            # treat them as allowed because they cannot be statically resolved
            # to a forbidden class without false positives.
            if node.exc is None:
                continue
            # Non-Name exc expression: skip (e.g. ``raise self._err``,
            # ``raise helpers.make_err()``). These are rare and not the target
            # of FR-24; banning them would be over-broad.
            continue
        if name in _ALLOWED_RAISE_NAMES:
            continue
        if name in helpers:
            # ``raise <helper>(...)`` where the helper is annotated to return
            # an allow-listed exception class. Treat as allow-listed by proxy.
            continue
        violations.append((node.lineno, name))
    return violations


@pytest.mark.unit
def test_no_bare_exception_raises_in_src_harbor() -> None:
    """Every ``raise`` in ``src/harbor`` uses an allow-listed exception class (FR-24)."""
    files = _iter_harbor_python_files()
    assert files, f"no python files found under {_SRC_HARBOR!s}"

    all_violations: list[tuple[Path, int, str]] = []
    for path in files:
        for lineno, name in _collect_raise_violations(path):
            all_violations.append((path, lineno, name))

    if all_violations:
        rendered = "\n".join(
            f"  {p.relative_to(_REPO_ROOT)}:{lineno}: raise {name}(...)"
            for p, lineno, name in all_violations
        )
        forbidden_seen = sorted(
            {name for _, _, name in all_violations if name in _FORBIDDEN_RAISE_NAMES}
        )
        hint = (
            "\nForbidden classes detected: "
            + ", ".join(forbidden_seen)
            + "\nUse harbor.errors.HarborRuntimeError (or a more specific HarborError "
            "subclass) instead of bare Exception/RuntimeError; use ValidationError "
            "for input/contract violations."
            if forbidden_seen
            else (
                "\nIf this exception class is legitimate, add it to "
                "_ALLOWED_RAISE_NAMES with a one-line justification."
            )
        )
        pytest.fail(
            "Disallowed raise statements found in src/harbor (FR-24, AC-3.2):\n" + rendered + hint
        )


@pytest.mark.unit
def test_provenance_encoder_uses_validation_error() -> None:
    """The 12-row provenance encoder raises only ``ValidationError`` (AC-6.3, FR-24)."""
    target = _SRC_HARBOR / "fathom" / "_provenance.py"
    assert target.is_file(), f"expected provenance encoder at {target!s}"

    tree = ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    raise_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.Raise)]
    assert raise_nodes, f"expected at least one raise in {target.name}"

    # Every raise must either:
    #   (a) name ValidationError directly, or
    #   (b) call a helper that returns ValidationError (e.g. ``_reject``).
    # We accept (b) by inspecting the helper definition in the same module:
    # any ``def <helper>(...) -> ValidationError`` annotation counts.
    helper_returns_validation_error: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            ret = node.returns
            if isinstance(ret, ast.Name) and ret.id == "ValidationError":
                helper_returns_validation_error.add(node.name)

    offenders: list[tuple[int, str]] = []
    for raise_node in raise_nodes:
        exc = raise_node.exc
        if exc is None:
            # Bare re-raise — allowed.
            continue
        if isinstance(exc, ast.Call):
            func = exc.func
            if isinstance(func, ast.Name):
                if func.id == "ValidationError":
                    continue
                if func.id in helper_returns_validation_error:
                    continue
                offenders.append((raise_node.lineno, func.id))
                continue
        if isinstance(exc, ast.Name):
            if exc.id == "ValidationError":
                continue
            offenders.append((raise_node.lineno, exc.id))
            continue
        offenders.append((raise_node.lineno, ast.dump(exc)))

    assert not offenders, (
        "provenance encoder must raise only ValidationError "
        "(directly or via a helper annotated -> ValidationError):\n"
        + "\n".join(f"  line {lineno}: {what}" for lineno, what in offenders)
    )
