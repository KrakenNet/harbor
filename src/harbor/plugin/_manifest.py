# SPDX-License-Identifier: Apache-2.0
"""Manifest discovery and validation for Harbor plugins.

A Harbor plugin distribution exposes a single ``harbor_plugin`` entry
point in the ``harbor`` group whose value is a zero-arg callable
returning a :class:`harbor.ir.PluginManifest`. The loader imports only
this manifest factory before deciding whether to register the dist's
tool/skill/store/pack entry points.

This split is the same pattern Datasette uses (datasette/plugins.py:
``check_version``) and lets Harbor reject incompatible plugins or
resolve namespace conflicts without paying the import cost of every
tool module.
"""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import Any

from harbor.errors import PluginLoadError
from harbor.ir import PluginManifest

__all__ = [
    "HARBOR_API_VERSION_MAJOR",
    "_detect_namespace_conflict",
    "_enforce_api_version",
    "_load_and_validate_manifest",
]

HARBOR_API_VERSION_MAJOR: int = 1
"""Major version of the Harbor plugin API. Manifests must match."""


def _load_and_validate_manifest(dist_name: str) -> PluginManifest:
    """Load the ``harbor_plugin`` manifest factory for ``dist_name``.

    Raises :class:`PluginLoadError` if the dist declares plugin entry
    points but no ``harbor_plugin`` factory, if the factory does not
    return a :class:`PluginManifest`, or if the manifest's
    ``api_version`` is incompatible with this Harbor major.
    """
    eps = entry_points(group="harbor", name="harbor_plugin")
    matches = [ep for ep in eps if ep.dist is not None and ep.dist.name == dist_name]
    if not matches:
        raise PluginLoadError(
            f"{dist_name}: declares plugin entries but no harbor_plugin "
            "manifest factory in the 'harbor' entry-point group",
            dist=dist_name,
        )
    factory: Any = matches[0].load()
    manifest = factory()
    if not isinstance(manifest, PluginManifest):
        raise PluginLoadError(
            f"{dist_name}: harbor_plugin factory must return a PluginManifest "
            f"(got {type(manifest).__name__!r})",
            dist=dist_name,
        )
    _enforce_api_version(manifest, dist_name)
    return manifest


def _enforce_api_version(manifest: PluginManifest, dist_name: str) -> None:
    """Reject manifests whose ``api_version`` major does not match Harbor."""
    declared = manifest.api_version
    try:
        major = int(declared.split(".", 1)[0])
    except (ValueError, IndexError) as exc:
        raise PluginLoadError(
            f"{dist_name}: malformed api_version {declared!r}",
            dist=dist_name,
            api_version=declared,
        ) from exc
    if major != HARBOR_API_VERSION_MAJOR:
        raise PluginLoadError(
            f"{dist_name}: api_version {declared!r} incompatible with "
            f"Harbor major {HARBOR_API_VERSION_MAJOR}. Refusing to load.",
            dist=dist_name,
            api_version=declared,
            harbor_major=HARBOR_API_VERSION_MAJOR,
        )


def _detect_namespace_conflict(
    manifest: PluginManifest,
    dist_name: str,
    claimed: dict[str, str],
) -> None:
    """Update ``claimed`` with ``manifest.namespaces``, raising on conflict.

    ``claimed`` maps namespace -> owning dist. On collision both dist
    names are surfaced in the :class:`PluginLoadError` so operators can
    pick the offender to uninstall.
    """
    for ns in manifest.namespaces:
        prior = claimed.get(ns)
        if prior is not None and prior != dist_name:
            raise PluginLoadError(
                f"namespace conflict: {ns!r} claimed by both {prior!r} and {dist_name!r}",
                namespace=ns,
                dists=(prior, dist_name),
            )
        claimed[ns] = dist_name
