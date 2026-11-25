"""Graded editorial recommendation (accept / minor / major / reject).

Why this exists: v0.1.0 reduced the outcome to "any admitted major concern =>
major issues remain". Any paper that attracts one verified concern therefore
read as a major revision, whatever the concern was. This module grades the
outcome from three facts about each verified concern: does it touch a CENTRAL
claim, how consequential is it, and what does the minimum fix cost (wording,
reanalysis of existing data, or new data). The rules are deterministic and
stated in the output so an author or editor can disagree with a specific step.
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

LEVELS = {"ACCEPT": 0, "MINOR_REVISION": 1, "MAJOR_REVISION": 2, "REJECT_IN_CURRENT_FORM": 3}


def classify_fix(minimum_resolution: str) -> str:
    """wording | reanalysis | new_data, from the concern's stated minimum resolution."""
    t = (minimum_resolution or "").lower()
    if any(k in t for k in NEW_DATA):
        return "new_data"
    if any(k in t for k in REANALYSIS):
        return "reanalysis"
    return "wording"


LEVELS_EXPLICIT = {"invalidates": 4.0, "changes_interpretation": 3.0, "weakens": 2.0, "minor": 1.0}


def consequence_weight(c: dict[str, Any]) -> float:
    """Use the reviewer's explicit consequence_level when given; otherwise fall back to keywords."""
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


def editorial_recommendation(claims: list[dict[str, Any]], admitted: list[dict[str, Any]],
                             automated_flags: int = 0) -> dict[str, Any]:
    """Return {recommendation, basis, drivers, would_become_if_closed, rules}.

    `automated_flags` is the number of gross numerical inconsistencies found by
    the offline checks (see referee/verification/consistency.py).
    """
    centrality = {str(c.get("claim_id")): str(c.get("centrality") or "supporting") for c in claims if isinstance(c, dict)}
    rows = []
    for c in admitted:
        fix = classify_fix(str(c.get("minimum_resolution") or ""))
        rows.append({
            "concern_id": c.get("concern_id"), "title": c.get("title"),
            "central": _central(c, centrality), "weight": consequence_weight(c), "fix": fix,
        })

    def level_of(row: dict[str, Any]) -> str:
        if row["central"] and row["weight"] >= 4 and row["fix"] == "new_data":
            return "REJECT_IN_CURRENT_FORM"
        if row["central"] and (row["weight"] >= 4 or row["fix"] in ("reanalysis", "new_data") or row["weight"] >= 3):
            return "MAJOR_REVISION"
        return "MINOR_REVISION"

    levels = [level_of(r) for r in rows]
    rec = max(levels, key=lambda x: LEVELS[x]) if levels else "ACCEPT"
    if len(rows) >= 3 and LEVELS[rec] < LEVELS["MAJOR_REVISION"]:
        rec = "MAJOR_REVISION"
        count_rule = "three or more verified concerns together"
    else:
        count_rule = ""
    if automated_flags and rec == "ACCEPT":
        rec = "MINOR_REVISION"

    drivers = [r for r, lv in zip(rows, levels) if LEVELS[lv] == LEVELS[rec]] if rows else []
    if rec == "ACCEPT":
        basis = ("No concern passed the evidence-locked independent-verification gate. Remaining comments are suggestions. "
                 "This is not proof the paper is flawless: it means nothing consequential could be verified against the text.")
    elif rec == "MINOR_REVISION":
        basis = ("Verified concerns exist, but none puts a central claim at risk beyond what rewording, clearer reporting or a "
                 "check on existing data can settle." if rows else
                 "Only automated numerical inconsistencies were found; they should be corrected or explained.")
    elif rec == "MAJOR_REVISION":
        basis = ("At least one verified concern touches a central claim and needs a reanalysis, new evidence, or a material change "
                 "to what the paper claims" + ("; " + count_rule if count_rule else "") + ".")
    else:
        basis = ("A central claim is undermined and only new data can restore it. As written the paper does not support its main "
                 "conclusion; a different or narrower paper could be built on the existing work.")

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
        "drivers": [{k: r[k] for k in ("concern_id", "title", "central", "fix")} for r in drivers],
        "would_become_if_drivers_closed": after,
        "automated_numerical_flags": automated_flags,
        "rules": ("REJECT_IN_CURRENT_FORM: central claim invalidated and fix needs new data. "
                  "MAJOR_REVISION: central-claim concern needing reanalysis/new data or a material reframing, or 3+ verified concerns. "
                  "MINOR_REVISION: verified concerns fixable by wording, reporting or checks on existing data, or only numerical slips. "
                  "ACCEPT: nothing verified."),
    }
