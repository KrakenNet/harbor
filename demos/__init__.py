# SPDX-License-Identifier: Apache-2.0
"""Harbor demo namespace package.

Demo packages live under this namespace so ``state_class:`` references in
demo IR YAMLs (e.g. ``demos.cve_remediation.graph.state:CveRemState``)
resolve via standard Python import. The demos themselves are not shipped
in the harbor wheel — they're test/integration artifacts under the repo
root.
"""
