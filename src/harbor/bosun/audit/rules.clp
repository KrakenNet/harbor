; SPDX-License-Identifier: Apache-2.0
; Bosun ``audit`` reference pack — Phase-4 implementation (task 4.2).
;
; Emits ``bosun.audit`` facts on every audit-relevant Harbor fact.
; The fact-watcher seam (``harbor.bosun.audit.promote_audit_facts``)
; converts each ``bosun.audit`` assertion into a ``BosunAuditEvent``
; (Pydantic v2 variant declared in ``harbor.runtime.events``) which
; flows through the existing single-sink ``JSONLAuditSink`` (design §7.2,
; FR-38, Resolved Decision #5 — single-sink invariant preserved).
;
; ``bosun.audit`` slot vocabulary:
;   - ``run_id`` — engine run identifier (string)
;   - ``step``   — engine step number (integer)
;   - ``kind``   — one of ``transition`` | ``tool_call`` | ``node_run`` |
;                  ``respond`` | ``cancel`` | ``pause`` | ``artifact_write``
;   - ``detail`` — short human-readable context (string)
;
; The seven rules below mirror the seven kinds. Each rule reads a
; canonical Harbor fact and asserts a ``bosun.audit`` fact bound to
; the same run_id/step.
;
; See harbor-serve-and-bosun design §7.1 + §7.2.

(deftemplate bosun.audit
  (slot run_id)
  (slot step)
  (slot kind)
  (slot detail))

(defrule audit-on-transition
  (harbor.transition (_run_id ?r) (_step ?s) (kind ?k))
  =>
  (assert (bosun.audit (run_id ?r) (step ?s) (kind "transition") (detail ?k))))

(defrule audit-on-tool-call
  (harbor.tool_call (_run_id ?r) (_step ?s) (name ?n))
  =>
  (assert (bosun.audit (run_id ?r) (step ?s) (kind "tool_call") (detail ?n))))

(defrule audit-on-node-run
  (harbor.node_run (_run_id ?r) (_step ?s) (node_id ?n))
  =>
  (assert (bosun.audit (run_id ?r) (step ?s) (kind "node_run") (detail ?n))))

(defrule audit-on-respond
  (harbor.respond (_run_id ?r) (_step ?s) (caller ?c))
  =>
  (assert (bosun.audit (run_id ?r) (step ?s) (kind "respond") (detail ?c))))

(defrule audit-on-cancel
  (harbor.cancel (_run_id ?r) (_step ?s) (reason ?why))
  =>
  (assert (bosun.audit (run_id ?r) (step ?s) (kind "cancel") (detail ?why))))

(defrule audit-on-pause
  (harbor.pause (_run_id ?r) (_step ?s) (reason ?why))
  =>
  (assert (bosun.audit (run_id ?r) (step ?s) (kind "pause") (detail ?why))))

(defrule audit-on-artifact-write
  (harbor.artifact_write (_run_id ?r) (_step ?s) (artifact_id ?a))
  =>
  (assert (bosun.audit (run_id ?r) (step ?s) (kind "artifact_write") (detail ?a))))
