# CVE feed fixtures (Phase-5 task 5.2)

Sample NVD + CISA KEV records used by `tests/integration/serve/test_cve_triage_e2e.py`
(Phase-5 validation gate — task 5.3) and the `cve_triage.yaml` IR fixture
(Phase-5 task 5.1).

## Sources

- **NVD JSON 2.0 schema**: <https://nvd.nist.gov/developers/vulnerabilities>
  (`/rest/json/cves/2.0` endpoint). Schema documentation:
  <https://csrc.nist.gov/schema/nvd/api/2.0/cve_api_json_2.0.schema>.
- **CISA Known Exploited Vulnerabilities Catalog**:
  <https://www.cisa.gov/known-exploited-vulnerabilities-catalog>. CSV form:
  <https://www.cisa.gov/sites/default/files/csv/known_exploited_vulnerabilities.csv>.

## Retrieval date + intent

- Authored: **2026-04-30** (Phase-5 validation-gate fixture for the
  `harbor-serve-and-bosun` spec).
- Intent: **shape validation only**. Each entry is a real, published CVE
  (canonical CVE IDs from 2023-2024 across NVD-public records). Fields
  populated reflect the public NVD JSON 2.0 + CISA KEV CSV schemas; the
  exact field values are abbreviated where the public NVD record itself
  is abbreviated (e.g., descriptive `vulnerabilityName` strings reflect
  the public KEV CSV at retrieval time).
- **No non-public exploitation details**: every field maps to data
  CISA + NVD publish openly. "Patch availability", "ransomware campaign
  use", and references all match what the public catalogs disclose. The
  fixture is a structural facsimile, not novel intelligence.

## Records included (12 CVEs)

CVE IDs cover:

- **Supply-chain**: CVE-2024-3094 (xz Utils backdoor)
- **Microsoft Windows / Outlook / LDAP**: CVE-2024-21413, CVE-2024-49113,
  CVE-2024-26229
- **Linux kernel netfilter**: CVE-2024-1086
- **Web / CI**: CVE-2024-23897 (Jenkins CLI)
- **Network appliance / firewall / VPN**: CVE-2024-21762 (Fortinet FortiOS),
  CVE-2024-21887 (Ivanti Connect Secure), CVE-2023-46805 (Ivanti CS
  auth-bypass), CVE-2024-3400 (Palo Alto PAN-OS), CVE-2024-1709
  (ConnectWise ScreenConnect)
- **OpenSSH**: CVE-2024-6387 (regreSSHion)

The vendor / weakness-class / CVSS-severity spread is deliberate: the
ML-severity scoring node + CLIPS routing node should produce different
classifications across the corpus (CRITICAL: 5, HIGH: 7), which the
counterfactual broker-mutation scenario re-ranks (FR-56,
design §13.3 (a)).

## How to refresh

NVD: pull a real slice with `curl 'https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2024-3094'`
and pretty-print into the `vulnerabilities[]` array (one entry per CVE).
KEV: download the canonical CSV and grep / awk the rows you need.

When the fixture corpus drifts (e.g., NVD adds new fields in v2.1), bump
the `version` field in `nvd_sample.json` and document the migration here.
