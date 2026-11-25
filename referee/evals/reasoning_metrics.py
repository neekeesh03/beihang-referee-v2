"""Reasoning-focused regression metrics for the director gate (no model).

Unit tests show that features run. These measure whether the gate and ledger
behave correctly on ADVERSARIAL cases: irrelevant evidence, invalid confidence,
a concern that fails its own steelman, false closure, a dropped concern. The
metrics are rates over labelled cases, so a change that makes the gate more
permissive shows up as a number, not as a silent regression.
"""
from __future__ import annotations

from typing import Any

from .. import direction as D


def gate_metrics(session: D.Session, claims: list[dict[str, Any]], cases: list[dict[str, Any]]) -> dict[str, Any]:
    """cases: [{name, concern, expect: 'admit'|'reject', critical: bool}]. Each concern is submitted alone in a fresh session."""
    admitted_wrong = rejected_wrong = n_bad = n_good = crit_total = crit_kept = 0
    rows = []
    for c in cases:
        claims_by_id = {str(x["claim_id"]): x for x in claims}
        ok, reasons, _ = D._gate_one(session, c["concern"], claims_by_id)
        rows.append({"name": c["name"], "expect": c["expect"], "admitted": ok, "reasons": reasons})
        if c["expect"] == "reject":
            n_bad += 1
            admitted_wrong += int(ok)
        else:
            n_good += 1
            rejected_wrong += int(not ok)
            if c.get("critical"):
                crit_total += 1
                crit_kept += int(ok)
    return {
        "unsupported_admission_rate": admitted_wrong / max(1, n_bad),
        "valid_rejection_rate": rejected_wrong / max(1, n_good),
        "critical_defect_retention": crit_kept / max(1, crit_total) if crit_total else None,
        "cases": rows,
    }


def closure_metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """cases: [{name, new_session, prior_id, status_entry, expect_closed: bool}] for revision_round on concern MC-001."""
    false_close = missed_close = n_open = n_closed = 0
    for c in cases:
        r = D.revision_round(c["new_session"], c["prior_id"], {"MC-001": c["status_entry"]})
        closed = r["ledger_status"][0]["status"] == "VERIFIED_CLOSED"
        if c["expect_closed"]:
            n_closed += 1
            missed_close += int(not closed)
        else:
            n_open += 1
            false_close += int(closed)
    return {"false_closure_rate": false_close / max(1, n_open), "missed_valid_closure_rate": missed_close / max(1, n_closed)}


def retention_metrics(gate_result: dict[str, Any], review_text: str) -> dict[str, Any]:
    """Share of admitted concerns (and of P0 ones) that survive into a written review."""
    lint = D.lint_review(review_text, gate_result, max_words=10 ** 6)
    lost = {f["note"] for f in lint["findings"] if f["check"] == "information_loss"}
    admitted = gate_result.get("admitted") or []
    p0 = [a for a in admitted if a.get("priority") == "P0"]
    lost_ids = {a["concern_id"] for a in admitted if any(a["concern_id"] in n for n in lost)}
    return {"admitted_retention": 1 - len(lost_ids) / max(1, len(admitted)),
            "p0_retention": 1 - len([a for a in p0 if a["concern_id"] in lost_ids]) / max(1, len(p0)) if p0 else None}
