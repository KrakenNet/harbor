# How to Author a Bosun Pack

## Goal

Ship a Bosun rule pack — CLIPS rules in `rules.clp`, manifest, signing
sidecar — as an installable distribution under the `harbor.packs` entry
point.

## Prerequisites

- Harbor + Fathom installed (`pip install stargraph>=0.2`).
- Familiarity with [Fathom rules](../tutorials/fathom-rules.md) and
  [Bosun in serve](../serve/bosun.md).
- An Ed25519 keypair for signing (Harbor v1 is alg-strict — EdDSA only).

## Steps

### 1. Lay out the pack

The shape is what Harbor's bundled packs use ([`harbor.bosun.budgets`,
`audit`, `safety_pii`, `retries`][bosun-tree]):

```text
my_pack/
├── __init__.py
├── manifest.yaml             # id, version, requires, provides
├── rules.clp                 # CLIPS rules + deftemplates
├── manifest.jwt              # EdDSA-JWT signature over manifest.yaml + rules.clp
└── <key_id>.pub.pem          # Ed25519 public-key sidecar
```

### 2. Write the manifest

```yaml
# my_pack/manifest.yaml
id: "harbor.bosun.my_pack"
version: "1.0"
requires:
  harbor_facts_version: "1.0"
  api_version: "1"
provides:
  - "harbor_facts:my.fact_template"
  - "harbor_facts:my.violation"
```

`requires` is the FR-39 version-compat block: Harbor refuses to load the
pack if the running engine doesn't satisfy the harbor-facts schema
version or plugin api_version (`PackCompatError` at load time, never
silent runtime drift).

**Verify:** `python -c "import yaml;
print(yaml.safe_load(open('my_pack/manifest.yaml')))"` round-trips.

### 3. Author the CLIPS rules

```clips
; my_pack/rules.clp
; SPDX-License-Identifier: Apache-2.0

(deftemplate my.fact_template
  (slot kind)
  (slot value)
  (slot run_id))

(deftemplate my.violation
  (slot kind)
  (slot severity)
  (slot run_id)
  (slot reason))

(defrule too-large
  (my.fact_template (kind "size") (value ?v&:(> ?v 1000)) (run_id ?r))
  =>
  (assert (my.violation
            (kind "size-exceeded")
            (severity "halt")
            (run_id ?r)
            (reason "value over threshold"))))
```

Templates declared in your pack are local to it; Harbor's bundled packs
follow the same one-pack-one-template-set convention.
Mirror the [`harbor.bosun.budgets`][budgets] pack for shape.

**Verify:** use the Fathom plugin
([`/fathom validate <pack-dir>`](../tutorials/fathom-rules.md)) to lint
the CLIPS source before signing.

### 4. Sign the pack

Harbor's signing pathway is in [`harbor.bosun.signing`][signing]:
EdDSA-JWT compact form (PyJWT[crypto]), BLAKE3 over the pack tree by
default (SHA-256 fallback under `HARBOR_FIPS_MODE=1`).

```python
# tools/sign_pack.py
from pathlib import Path

from harbor.bosun.signing import sign_pack  # see harbor/bosun/signing.py

pack_dir = Path("my_pack")
private_key_pem = Path("dev-bosun.key.pem").read_bytes()
key_id = "abcd1234abcd1234"

sign_pack(pack_dir, private_key_pem=private_key_pem, key_id=key_id)
```

The signer writes `manifest.jwt` (EdDSA-JWT over the canonical
manifest+rules tree) and the public-key sidecar
`<pack_dir>/<key_id>.pub.pem` that the verifier reads on first sight
(TOFU pin).

!!! warning "Algorithm strict"
    Harbor refuses any JWT alg other than `EdDSA` and rejects embedded
    `x5c` headers at decode (locked design §17 Decision #4). HMAC keys
    and `none` are not accepted under any profile.

### 5. Distribute as a `harbor.packs` plugin

```python
# my_pack/_pack.py
from harbor.ir import PackMount, PackRequires
from harbor.plugin._markers import hookimpl


@hookimpl
def register_packs() -> list[PackMount]:
    return [
        PackMount(
            id="harbor.bosun.my_pack",
            version="1.0",
            requires=PackRequires(
                harbor_facts_version="1.0",
                api_version="1",
            ),
        ),
    ]
```

## Wire it up

```toml
# pyproject.toml
[project]
name = "harbor-pack-my-pack"
version = "1.0"
dependencies = ["stargraph>=0.2"]

[project.entry-points."harbor"]
harbor_plugin = "my_pack._plugin:harbor_plugin"

[project.entry-points."harbor.packs"]
my_pack = "my_pack._pack"

[tool.hatch.build.targets.wheel.force-include]
"my_pack/manifest.yaml"     = "my_pack/manifest.yaml"
"my_pack/rules.clp"         = "my_pack/rules.clp"
"my_pack/manifest.jwt"      = "my_pack/manifest.jwt"
"my_pack/abcd1234.pub.pem"  = "my_pack/abcd1234.pub.pem"
```

The `force-include` block ships the data files alongside the Python
package so the bosun loader can resolve them from `__file__`.

Mount the pack from a graph:

```yaml
# harbor.yaml
governance:
  - id: harbor.bosun.my_pack
    version: "1.0"
    requires:
      harbor_facts_version: "1.0"
      api_version: "1"
```

## Verify

```bash
pip install -e ./my_pack
HARBOR_TRACE_PLUGINS=1 python -c "
from harbor.plugin.loader import build_plugin_manager
pm = build_plugin_manager()
for mounts in pm.hook.register_packs():
    for m in mounts:
        print(m.id, m.version)
"
```

Then run a graph that mounts the pack — the rule firings appear in
`harbor inspect <run_id>` under the per-step rule trace.

## Troubleshooting

!!! warning "Common failure modes"
    - **`PackSignatureError: alg mismatch`** — only EdDSA is permitted.
      Re-sign with an Ed25519 keypair.
    - **`PackSignatureError: TOFU drift`** — the on-disk
      `<config_dir>/trusted_keys/<key_id>.json` fingerprint does not
      match the current sidecar. Either revoke the trust record or
      re-issue from the original key.
    - **`PackCompatError`** — `requires.harbor_facts_version` doesn't
      match the running engine. Bump the pack or pin Harbor.
    - **Pack files missing in the wheel** — add them under
      `[tool.hatch.build.targets.wheel.force-include]`; pure-Python
      auto-discovery skips data files.

## See also

- [Add a rule pack](add-rule-pack.md) — wiring it into a graph.
- [Bosun in serve](../serve/bosun.md) — discovery + verification flow.
- [Fathom rules tutorial](../tutorials/fathom-rules.md).
- [Reference: signing](../reference/signing.md).
- [`harbor.bosun.signing`][signing] source.
- [Bundled packs][bosun-tree].

[bosun-tree]: https://github.com/KrakenNet/harbor/tree/main/src/harbor/bosun
[budgets]: https://github.com/KrakenNet/harbor/tree/main/src/harbor/bosun/budgets
[signing]: https://github.com/KrakenNet/harbor/blob/main/src/harbor/bosun/signing.py
