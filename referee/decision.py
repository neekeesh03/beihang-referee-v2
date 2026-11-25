"""Graded editorial recommendation (accept / minor / major / reject).

Inputs per verified concern: does it touch a CENTRAL claim, how consequential is
it (reviewer-stated consequence_level), and what does the cheapest sufficient
fix cost (reviewer-stated fix_type: wording | reanalysis | new_data).

Design rules (revised after independent validation of v2):
- The reviewer's structured judgments (consequence_level, fix_type) are used when
  given. Keyword reading of free text is only a FALLBACK, and it understands
  negation ("no new data are needed" is not a new-data request).
- The NUMBER of concerns never escalates a recommendation on its own. Only
  consequential concerns (central, or consequence >= changes_interpretation)
  count toward the "several decisive concerns" rule.
- The stated basis names the actual drivers, so the explanation cannot
  contradict the concerns that produced it.
"""
from __future__ import annotations

import re
from typing import Any

NEW_DATA = ("collect", "new experiment", "additional experiment", "replicat", "recruit", "new cohort",
            "independent dataset", "independent cohort", "prospective", "validation cohort", "new data",
            "additional data", "randomi", "external validation", "run new", "perform new", "matched control",
            "held-out", "held out", "new queries", "additional queries", "new benchmark", "control experiment", "equal-access")
REANALYSIS = ("reanaly", "re-analy", "recompute", "recalculat", "sensitivity analys", "robustness",
              "adjust for", "control for", "stratif", "bootstrap", "additional analys", "new analys",
              "multiple-comparison", "multiple comparison", "refit", "re-fit", "report effect size", "compare the saved",
              "quantify", "quantif", "agreement", "paired", "confidence interval", "interval", "inter-rater", "kappa", "ablat")
_NEGATORS = re.compile(r"(?:\bno\b|\bnot\b|n't\b|\bwithout\b|\bnever\b|\bneither\b|\bnor\b|\binstead of\b|\brather than\b|\bavoid\w*\b|\bunnecessary\b|\bnone\b)[^.;:]{0,45}$", re.I)

LEVELS = {"ACCEPT": 0, "MINOR_REVISION": 1, "MAJOR_REVISION": 2, "REJECT_IN_CURRENT_FORM": 3}
LEVELS_EXPLICIT = {"invalidates": 4.0, "changes_interpretation": 3.0, "weakens": 2.0, "minor": 1.0}
FIX_TYPES = ("wording", "reanalysis", "new_data")


def _has_affirmed(text: str, keys: tuple[str, ...]) -> bool:
    """True if any keyword occurs and is not negated by a preceding 'no/not/without/instead of...'."""
    low = text.lower()
    for k in keys:
        start = 0
        while True:
            i = low.find(k, start)
            if i == -1:
                break
            if not _NEGATORS.search(low[max(0, i - 60):i]):
                return True
            start = i + len(k)
    return False


def classify_fix(minimum_resolution: str, fix_type: str | None = None) -> str:
    """wording | reanalysis | new_data. The reviewer's explicit fix_type wins; keywords are a negation-aware fallback."""
    if fix_type and str(fix_type).lower() in FIX_TYPES:
        return str(fix_type).lower()
    t = minimum_resolution or ""
    if _has_affirmed(t, NEW_DATA):
        return "new_data"
    if _has_affirmed(t, REANALYSIS):
        return "reanalysis"
    return "wording"


def consequence_weight(c: dict[str, Any]) -> float:
    lvl = str(c.get("consequence_level") or "").lower()
    if lvl in LEVELS_EXPLICIT:
        return LEVELS_EXPLICIT[lvl]
    text = (str(c.get("scientific_consequence") or "") + " " + str(c.get("failure_mechanism") or "")).lower()
    if any(x in text for x in ("invalidat", "cannot support", "not identifiable", "cannot identify", "uninterpretable",
                               "principal conclusion", "central conclusion is unsupported", "main conclusion is unsupported")):
        return 4.0
    if any(x in text for x in ("major reinterpret", "reframe", "materially changes", "central interpretation", "primary result")):
        return 3.0
    if any(x in text for x in ("substantial", "important limitation", "material bias", "serious limitation", "weakens")):
        return 2.0
    return 1.0


def _central(c: dict[str, Any], centrality: dict[str, str]) -> bool:
    return any(centrality.get(str(cid)) == "central" for cid in (c.get("claim_ids") or []))


def priority_of(central: bool, weight: float) -> str:
    """P0 decisive, P1 important, P2 improvement."""
    if central and weight >= 3:
        return "P0"
    if central or weight >= 3:
        return "P1"
    return "P2"


def editorial_recommendation(claims: list[dict[str, Any]], admitted: list[dict[str, Any]],
                             automated_flags: int = 0, verification_level: str | None = None) -> dict[str, Any]:
    centrality = {str(c.get("claim_id")): str(c.get("centrality") or "supporting") for c in claims if isinstance(c, dict)}
    rows = []
    for c in admitted:
        w = consequence_weight(c)
        central = _central(c, centrality)
        rows.append({
            "concern_id": c.get("concern_id"), "title": c.get("title"), "central": central, "weight": w,
            "fix": classify_fix(str(c.get("minimum_resolution") or ""), c.get("fix_type")),
            "priority": priority_of(central, w),
        })

    def level_of(r: dict[str, Any]) -> str:
        if r["central"] and r["weight"] >= 4 and r["fix"] == "new_data":
            return "REJECT_IN_CURRENT_FORM"
        if r["central"] and (r["weight"] >= 4 or r["fix"] in ("reanalysis", "new_data") or r["weight"] >= 3):
            return "MAJOR_REVISION"
        return "MINOR_REVISION"

    levels = [level_of(r) for r in rows]
    rec = max(levels, key=lambda x: LEVELS[x]) if levels else "ACCEPT"
    consequential = [r for r in rows if r["priority"] in ("P0", "P1")]
    escalated = False
    if len(consequential) >= 3 and LEVELS[rec] < LEVELS["MAJOR_REVISION"]:
        rec, escalated = "MAJOR_REVISION", True  # several decisive concerns together; minor/supporting ones never escalate
    if automated_flags and rec == "ACCEPT":
        rec = "MINOR_REVISION"

    drivers = [r for r, lv in zip(rows, levels) if LEVELS[lv] == LEVELS[rec]] if not escalated else consequential
    drv = "; ".join(f"{d['concern_id']} ({'central claim' if d['central'] else 'supporting claim'}, "
                    f"{'new data' if d['fix'] == 'new_data' else d['fix']}, priority {d['priority']})" for d in drivers[:5])
    if rec == "ACCEPT":
        basis = ("No concern passed the verification gate. Remaining comments are suggestions. This is not proof the paper is flawless: "
                 "nothing consequential could be verified against the text.")
    elif rec == "MINOR_REVISION":
        basis = (f"Verified concerns exist but none puts a central claim at risk beyond what rewording, reporting or a check on existing data can settle. Driving: {drv}."
                 if rows else "Only automated numerical inconsistencies were found; correct or explain them.")
    elif rec == "MAJOR_REVISION":
        basis = ("Three or more consequential concerns together" if escalated else "A verified concern on a central claim needs a reanalysis, new evidence or a material reframing") + f". Driving: {drv}."
    else:
        basis = f"A central claim is undermined and only new data can restore it. Driving: {drv}."
    if verification_level == "self_only":
        basis += " Verification level: self-only (no independent verifier); treat as provisional."

    if rec in ("MAJOR_REVISION", "REJECT_IN_CURRENT_FORM"):
        remaining = [r for r in rows if r not in drivers]
        after = "MINOR_REVISION" if remaining or automated_flags else "ACCEPT"
    elif rec == "MINOR_REVISION":
        after = "ACCEPT"
    else:
        after = None
    return {
        "recommendation": rec,
        "basis": basis,
        "drivers": [{k: r[k] for k in ("concern_id", "title", "central", "fix", "priority")} for r in drivers],
        "priorities": {r["concern_id"]: r["priority"] for r in rows},
        "would_become_if_drivers_closed": after,
        "automated_numerical_flags": automated_flags,
        "verification_level": verification_level,
        "rules": ("REJECT_IN_CURRENT_FORM: central claim invalidated and the fix needs new data. "
                  "MAJOR_REVISION: a central-claim concern needing reanalysis, new data or a material reframing, or three or more CONSEQUENTIAL concerns (central or changes-interpretation and above). "
                  "MINOR_REVISION: concerns fixable by wording, reporting or checks on existing data, or only numerical slips. "
                  "ACCEPT: nothing verified. The count of minor or supporting concerns never escalates the outcome."),
    }


def consolidate_and_cap(claims: list[dict[str, Any]], admitted: list[dict[str, Any]], hard_max: int,
                        per_central_claim: int = 3) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Pipeline-side counterpart of the director's budget: merge near-duplicates (same claim, similar mechanism),
    rank by priority, then cap at min(hard_max, per_central_claim * number of central claims). Returns (kept, dropped);
    dropped items carry a reason so nothing disappears silently."""
    centrality = {str(c.get("claim_id")): str(c.get("centrality") or "supporting") for c in claims if isinstance(c, dict)}
    n_central = sum(1 for v in centrality.values() if v == "central")

    def stems(c: dict[str, Any]) -> set[str]:
        return {w[:6] for w in re.findall(r"[a-z]{4,}", (str(c.get("failure_mechanism") or "") + " " + str(c.get("title") or "")).lower())}

    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for c in sorted(admitted, key=lambda x: ({"P0": 0, "P1": 1, "P2": 2}[priority_of(_central(x, centrality), consequence_weight(x))])):
        dup = None
        for k in kept:
            if set(k.get("claim_ids") or []) & set(c.get("claim_ids") or []):
                a, b = stems(c), stems(k)
                if a and b and len(a & b) / len(a | b) >= 0.55:
                    dup = k
                    break
        if dup is not None:
            dropped.append({**c, "status": "merged_into_other", "admission_errors": [f"near-duplicate of \"{dup.get('title')}\"; consolidated"]})
        else:
            kept.append(c)
    cap = min(hard_max, per_central_claim * max(1, n_central))
    for c in kept[cap:]:
        dropped.append({**c, "status": "over_budget", "admission_errors": [f"over the budget of {cap} major concerns for {n_central or 1} central claim(s); reported as a should-fix"]})
    return kept[:cap], dropped
