#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
#
# CVE pipeline production deployment runbook (FR-52, AC-11.4, design §18 step 16).
#
# This script is DOCUMENTATION + dry-run helpers. It does NOT start a real
# production deployment. The 7-day soak is executed out-of-band by an operator
# following the steps below; the validation-gate close-out artifact is the
# script + runbook, not a live deployment.
#
# Usage:
#   ./scripts/cve_production_deployment.sh           # prints the runbook
#   ./scripts/cve_production_deployment.sh --check   # dry-run the pre-flight checks
#
# Ports 8765/8000 (and any other harbor-serve port) are NOT bound by this
# script under any flag. To actually deploy, run the commands from the runbook
# manually or from your orchestrator (systemd unit / docker-compose / k8s).

set -euo pipefail

# -----------------------------------------------------------------------------
# Configuration (override via env)
# -----------------------------------------------------------------------------
HARBOR_PROFILE="${HARBOR_PROFILE:-oss-default}"
HARBOR_PORT="${HARBOR_PORT:-8000}"
HARBOR_CONFIG_DIR="${HARBOR_CONFIG_DIR:-/var/lib/harbor/config}"
NVD_FEED_URL="${NVD_FEED_URL:-https://services.nvd.nist.gov/rest/json/cves/2.0}"
KEV_FEED_URL="${KEV_FEED_URL:-https://www.cisa.gov/sites/default/files/csv/known_exploited_vulnerabilities.csv}"
CRON_INTERVAL_HOURS="${CRON_INTERVAL_HOURS:-1}"
SOAK_DURATION_DAYS="${SOAK_DURATION_DAYS:-7}"
LINEAGE_AUDIT_INTERVAL_HOURS="${LINEAGE_AUDIT_INTERVAL_HOURS:-1}"


# -----------------------------------------------------------------------------
# Runbook printer
# -----------------------------------------------------------------------------
print_runbook() {
    cat <<'RUNBOOK_EOF'
================================================================================
CVE PIPELINE PRODUCTION DEPLOYMENT — 7-DAY SOAK RUNBOOK
================================================================================

Per design §18 step 16 + FR-52 + AC-11.4: production deployment, scheduled via
``harbor serve`` with a cron trigger, running for >=7 documented days against
real NVD JSON 2.0 + CISA KEV feeds. The soak validates production-grade FR-60
(failure protocol; <2x retry budget) and AC-11.5 (validation report).

PREREQUISITES (ONE-TIME)
------------------------

1. Provision the deployment host:
   - POSIX-local filesystem (NFS refused per AC-15.8 / NFR-25).
   - SQLite WAL filesystem support (most ext4/xfs/zfs OK; tmpfs OK for tests).
   - Network egress to ${NVD_FEED_URL} and ${KEV_FEED_URL}.
   - Python 3.13 + uv installed; ``harbor`` CLI on PATH.

2. Create the harbor user + config dir:
       sudo useradd -r -m -d /var/lib/harbor harbor
       sudo install -d -m 0755 -o harbor -g harbor /var/lib/harbor/{config,data,artifacts,audit}

3. Author the harbor.toml (under ${HARBOR_CONFIG_DIR}/harbor.toml):
       [run_history]
       retention_days = 30

       [audit]
       sink = "jsonl"
       path = "/var/lib/harbor/audit/audit.jsonl"

       [artifacts]
       backend = "fs"
       root    = "/var/lib/harbor/artifacts"

       [checkpointer]
       backend = "sqlite"
       path    = "/var/lib/harbor/data/checkpoints.sqlite"

4. Author the cron-trigger config (under ${HARBOR_CONFIG_DIR}/triggers/cve.yaml):
       # Cron trigger: pulls NVD + KEV every ${CRON_INTERVAL_HOURS}h, drives the
       # CVE triage pipeline (graph_id=cve-triage-remediation).
       triggers:
         - id: cve_cron
           kind: cron
           graph: cve-triage-remediation
           schedule: "0 */${CRON_INTERVAL_HOURS} * * *"      # hourly
           inputs:
             nvd_url: "${NVD_FEED_URL}"
             kev_url: "${KEV_FEED_URL}"
           timezone: "UTC"

5. Sign the Bosun packs (one-time, run on the build host):
       uv run python scripts/sign_bosun_packs.py
   Then copy ``src/harbor/bosun/*/manifest.{yaml,jwt}`` to the deployment host.


DEPLOY (T0)
-----------

Start ``harbor serve`` under a service supervisor (systemd shown):

    # /etc/systemd/system/harbor.service
    [Unit]
    Description=Harbor Engine (CVE pipeline production deployment)
    After=network.target

    [Service]
    Type=exec
    User=harbor
    Group=harbor
    WorkingDirectory=/var/lib/harbor
    Environment="HARBOR_CONFIG_DIR=${HARBOR_CONFIG_DIR}"
    ExecStart=/usr/local/bin/harbor serve --profile ${HARBOR_PROFILE} \
        --port ${HARBOR_PORT} \
        --config-dir ${HARBOR_CONFIG_DIR}
    Restart=on-failure
    RestartSec=5

    [Install]
    WantedBy=multi-user.target

Enable + start:
    sudo systemctl daemon-reload
    sudo systemctl enable --now harbor.service

Verify liveness:
    curl -sf http://127.0.0.1:${HARBOR_PORT}/openapi.json > /dev/null && echo SERVE_UP


SOAK MONITORING (T0..T+${SOAK_DURATION_DAYS}d)
----------------------------------------------

Per AC-11.4: lineage audit every ${LINEAGE_AUDIT_INTERVAL_HOURS}h; halt + file
bug on any FAIL.

1. Per-run inspection (manual ad-hoc):
       harbor inspect <run_id> --db /var/lib/harbor/data/checkpoints.sqlite

2. Hourly lineage audit (cron):
       # /etc/cron.d/harbor-lineage-audit
       0 * * * * harbor /usr/local/bin/uv run python /opt/harbor/scripts/lineage_audit.py \
           --audit-path /var/lib/harbor/audit/audit.jsonl \
           >> /var/lib/harbor/audit/lineage-audit.log 2>&1

3. Run-history dashboard (manual or grafana):
       harbor inspect --list --since=24h --db /var/lib/harbor/data/checkpoints.sqlite

4. Audit log tail (real-time):
       tail -f /var/lib/harbor/audit/audit.jsonl | jq .


STOP CONDITIONS
---------------

- Any lineage-audit FAIL    -> halt + file bug (do not paper over).
- Any pipeline run with     -> halt + capture run_id, audit-log path, file bug.
  status="failed"
- Any panicking serve crash -> halt + capture coredump + journalctl logs.

PASS CONDITION
--------------

- ${SOAK_DURATION_DAYS} days elapsed with:
    * >=1 successful CVE-pipeline run per cron tick (at hourly cadence,
      that is >=${SOAK_DURATION_DAYS} * 24 = $((SOAK_DURATION_DAYS * 24))
      successful runs).
    * 0 lineage-audit FAILs across the entire window.
    * 0 panicking crashes (Restart=on-failure may legitimately fire on
      transient feed outages; log them).
    * Validation report (``docs/validation/cve-pipeline-report.md``) updated
      with the soak window's run-count, audit count, and any anomalies.


DEPROVISION (T+>=${SOAK_DURATION_DAYS}d)
----------------------------------------

    sudo systemctl disable --now harbor.service
    # Preserve audit + checkpoints for the validation report:
    sudo tar czf /var/backups/harbor-soak-$(date +%Y%m%d).tar.gz \
        /var/lib/harbor/{audit,data,artifacts}
    # Then either keep the deployment as-is or rotate to a fresh state.

================================================================================
RUNBOOK_EOF
}


# -----------------------------------------------------------------------------
# Pre-flight check (--check)
# -----------------------------------------------------------------------------
check_preflight() {
    local rc=0
    echo "[preflight] checking harbor CLI..."
    if ! command -v harbor >/dev/null 2>&1; then
        echo "[FAIL] harbor not on PATH (run via 'uv run harbor ...' instead)"
        rc=1
    else
        echo "[OK]   harbor CLI present"
    fi

    echo "[preflight] checking lineage_audit.py..."
    if [ -f "scripts/lineage_audit.py" ]; then
        echo "[OK]   scripts/lineage_audit.py present"
    else
        echo "[FAIL] scripts/lineage_audit.py missing"
        rc=1
    fi

    echo "[preflight] checking Bosun pack signatures..."
    local missing=0
    for pack in budgets audit safety_pii retries; do
        if [ ! -f "src/harbor/bosun/${pack}/manifest.jwt" ]; then
            echo "[WARN] Bosun pack '${pack}' has no manifest.jwt — run scripts/sign_bosun_packs.py"
            missing=1
        fi
    done
    if [ "${missing}" -eq 0 ]; then
        echo "[OK]   all 4 Bosun pack manifests signed"
    fi

    echo "[preflight] checking feed URLs reachable..."
    if curl -sf --max-time 5 "${NVD_FEED_URL}?resultsPerPage=1" -o /dev/null; then
        echo "[OK]   NVD feed reachable"
    else
        echo "[WARN] NVD feed unreachable (curl rc=$?) — soak deployment will retry on cron tick"
    fi

    echo "[preflight] checks complete (rc=${rc})"
    return "${rc}"
}


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
case "${1:-}" in
    --check)
        check_preflight
        ;;
    --help|-h)
        cat <<HELP_EOF
Usage: $(basename "$0") [--check | --help]

Without flags: prints the production deployment runbook (read-only).
--check: runs pre-flight checks (harbor CLI present, packs signed, feeds reachable).
--help:  this message.

This script never starts a real harbor serve process. The 7-day soak is
executed out-of-band by an operator following the runbook.
HELP_EOF
        ;;
    *)
        print_runbook
        ;;
esac
