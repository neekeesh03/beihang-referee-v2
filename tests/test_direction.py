import json

import pytest

from referee import direction as d

V1 = """# Demo
## Methods
A single observational cohort of 80 participants received intervention X. There was no randomized control group. Outcome Y was measured after treatment and compared with the cohort's pre-treatment value.
## Results
Mean Y increased from 50 to 60 units after treatment (n=80).
## Conclusion
Intervention X causes a 20% improvement in outcome Y.
## Acknowledgments
We thank the Hospital Foundation for lunch and parking support during recruitment.
"""
V2 = V1.replace("Intervention X causes a 20% improvement in outcome Y.",
                "Intervention X is associated with a 20% improvement in outcome Y; we cannot rule out time trends.") + "\nWe also report a new subgroup of 12 people who all improved.\n"

CLAIMS = [{"claim_id": "C1", "centrality": "central", "text": "X causes a 20% improvement"},
          {"claim_id": "C2", "centrality": "supporting", "text": "Y rose from 50 to 60"}]


def good(**kw):
    c = {"title": "No counterfactual", "claim_ids": ["C1"], "anchors": ["There was no randomized control group."],
         "failure_mechanism": "A single-group pre-post comparison cannot separate the effect from time trends.",
         "scientific_consequence": "The central causal conclusion cannot be supported.",
         "consequence_level": "invalidates", "fix_type": "wording",
         "minimum_resolution": "Reframe the conclusion as an association, or add a comparison group analysis.",
         "closure_criterion": "The abstract and conclusion no longer state a causal effect, or the paper reports a valid comparison.",
         "confidence": 0.85, "steelman": "Authors may argue the effect is large.", "survives_steelman": True,
         "steelman_survival": "Size does not remove regression to the mean."}
    c.update(kw)
    return c


def other(i, **kw):
    """A distinct, grounded concern (different mechanism, anchor and claim)."""
    banks = [
        ("Outcome timing", ["Outcome Y was measured after treatment"], "The outcome was measured only once after treatment so spontaneous recovery is not separated."),
        ("Single cohort size", ["A single observational cohort of 80 participants"], "One cohort of eighty participants limits generalisation to other settings."),
        ("Magnitude reporting", ["Mean Y increased from 50 to 60 units"], "Only the mean change is given without any variability or interval for the change."),
        ("Pre-treatment baseline", ["compared with the cohort's pre-treatment value"], "A pre-treatment value is the only comparator so regression to the mean is not addressed."),
    ]
    t, a, m = banks[i]
    kw.setdefault("consequence_level", "changes_interpretation")
    return good(title=t, anchors=a, failure_mechanism=m, **kw)


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("REFEREE_HOME", str(tmp_path))


def test_default_playbook_releases_only_discovery_rules():
    p = d.playbook()
    assert len(p["workflow"]) == 8
    assert set(p["rules"]) == {"phases", "evidence", "defect_hunt", "coverage"}  # no voice, decision, stopping: they cannot compete with discovery
    assert "voice" in d.playbook("write")["rules"] and "decision" in d.playbook("adjudicate")["rules"]
    assert "Two separate verdicts" in d.playbook("write")["rules"]["report_style"]
    assert "alignment" in d.playbook("defect_hunt")["rule"].lower()


def test_quote_verification_exact_near_and_hallucinated():
    s = d.Session(V1)
    assert d.verify_quote(s, "There was no randomized control group.")["match"] == "exact"
    assert d.verify_quote(s, "there  was NO randomized\ncontrol group")["status"] == "verified"
    assert d.verify_quote(s, "The authors preregistered the protocol on OSF")["status"] == "not_found"


def test_gate_admits_grounded_concern_and_blocks_invented_one():
    s = d.Session(V1); s.save()
    out = d.submit_concerns(s, CLAIMS, [good(), good(title="Invented", anchors=["Participants were recruited from three hospitals in Berlin."])])
    assert [c["concern_id"] for c in out["admitted"]] == ["MC-001"]
    assert out["downgraded"][0]["new_status"] == "question"
    assert out["editorial_decision"]["recommendation"] in ("MAJOR_REVISION", "REJECT_IN_CURRENT_FORM")
    assert out["verification_level"] == "self_only" and "provisional" in out["editorial_decision"]["basis"]


def test_a_real_quote_that_does_not_support_the_concern_is_not_admitted():
    s = d.Session(V1); s.save()
    irrelevant = good(title="No counterfactual", anchors=["We thank the Hospital Foundation for lunch and parking support"])
    out = d.submit_concerns(s, CLAIMS, [irrelevant])
    assert not out["admitted"]
    assert "does not appear to support" in " ".join(out["downgraded"][0]["downgraded_because"])


@pytest.mark.parametrize("bad", [float("nan"), 7, -1, True, "high", None, float("inf")])
def test_invalid_confidence_values_never_pass(bad):
    s = d.Session(V1); s.save()
    out = d.submit_concerns(s, CLAIMS, [good(confidence=bad)])
    assert not out["admitted"]


def test_low_confidence_and_weak_closure_are_downgraded():
    s = d.Session(V1); s.save()
    out = d.submit_concerns(s, CLAIMS, [good(confidence=0.3), good(title="b", closure_criterion="fix it")])
    assert not out["admitted"] and len(out["downgraded"]) == 2
    assert out["editorial_decision"]["recommendation"] == "ACCEPT"


def test_concern_that_fails_its_own_steelman_is_not_admitted():
    s = d.Session(V1); s.save()
    a = d.submit_concerns(s, CLAIMS, [good(survives_steelman=False)])
    assert not a["admitted"] and "steelman" in " ".join(a["downgraded"][0]["downgraded_because"])
    s2 = d.Session(V1 + " "); s2.save()
    b = d.submit_concerns(s2, CLAIMS, [good(steelman_survival="The concern does not survive: the authors' reading is correct.")])
    assert not b["admitted"] and "contradicting" in " ".join(b["downgraded"][0]["downgraded_because"])


def test_new_data_demand_on_supporting_claim_is_downgraded_but_negated_demand_is_not_new_data():
    s = d.Session(V1); s.save()
    c = good(claim_ids=["C2"], fix_type="new_data", minimum_resolution="Recruit a new cohort and repeat the study.")
    assert not d.submit_concerns(s, CLAIMS, [c])["admitted"]
    s2 = d.Session(V1 + "\n"); s2.save()
    # fix_type unspecified wording; resolution text says no new data are needed: must not be read as new data
    ok = good(claim_ids=["C2"], fix_type="wording", minimum_resolution="No new data are needed; state the variability of the change.")
    assert d.submit_concerns(s2, CLAIMS, [ok])["admitted"]


def test_budget_scales_with_central_claims_and_overflow_is_a_ranked_should_fix():
    s = d.Session(V1); s.save()
    cs = [other(i) for i in range(4)]
    out = d.submit_concerns(s, CLAIMS, [good()] + cs)  # one central claim -> cap 3
    assert len(out["admitted"]) == 3
    over = [x for x in out["downgraded"] if x["new_status"] == "should_fix"]
    assert len(over) == 2 and "budget" in over[0]["downgraded_because"][0]


def test_near_duplicate_concerns_are_merged_not_double_counted():
    s = d.Session(V1); s.save()
    dup = good(title="Absent comparison group", anchors=["A single observational cohort of 80 participants"],
               failure_mechanism="A single-group pre-post comparison cannot separate the effect from time trends.")
    out = d.submit_concerns(s, CLAIMS, [good(), dup])
    assert len(out["admitted"]) == 1 and out["downgraded"][0]["new_status"] == "merge"


def test_minor_rated_concern_is_a_minor_comment_and_does_not_use_the_major_budget():
    s = d.Session(V1); s.save()
    m = [good(title=f"m{i}", consequence_level="minor", anchors=[q], failure_mechanism=f"distinct wording {i} about typography") for i, q in enumerate(
        ["There was no randomized control group.", "A single observational cohort of 80 participants"])]
    out = d.submit_concerns(s, CLAIMS, m + [other(2)])
    assert [c["title"] for c in out["admitted"]] == ["Magnitude reporting"]
    assert [c["new_status"] for c in out["downgraded"]] == ["minor", "minor"]


def test_priority_orders_decisive_concerns_first():
    s = d.Session(V1); s.save()
    minor_first = other(0, claim_ids=["C2"], consequence_level="weakens")
    out = d.submit_concerns(s, CLAIMS, [minor_first, good()])
    assert out["admitted"][0]["priority"] == "P0" and out["admitted"][0]["title"] == "No counterfactual"
    assert out["admitted"][0]["concern_id"] == "MC-001"


def test_two_phase_independent_verification():
    s = d.Session(V1); s.save()
    pend = d.submit_concerns(s, CLAIMS, [good()], require_verification=True)
    assert pend["status"] == "pending_verification" and "editorial_decision" not in pend
    pk = pend["verification_packets"][0]
    assert "steelman" not in json.dumps(pk["concern"]).lower() and "Try to DESTROY" in pk["verifier_instructions"]
    verdict = {"verdict": "VERIFIED", "anchors_support_mechanism": True, "consequence_proportionate": True, "resolution_sufficient": True,
               "closure_testable": True, "steelman_survives": True, "contradiction_found": False, "reason": "ok"}
    out = d.submit_concerns(s, CLAIMS, [good()], independent_verdicts={pk["packet_id"]: verdict})
    assert out["verification_level"] == "independent" and [c["concern_id"] for c in out["admitted"]] == ["MC-001"]


def test_independent_verifier_can_reject_or_downgrade():
    s = d.Session(V1); s.save()
    pk = d.submit_concerns(s, CLAIMS, [good()], require_verification=True)["verification_packets"][0]["packet_id"]
    v = {"verdict": "VERIFIED", "anchors_support_mechanism": False, "consequence_proportionate": True, "resolution_sufficient": True,
         "closure_testable": True, "steelman_survives": True, "contradiction_found": False}
    out = d.submit_concerns(s, CLAIMS, [good()], independent_verdicts={pk: v})
    assert not out["admitted"] and "did not affirm" in out["downgraded"][0]["downgraded_because"][0]
    s2 = d.Session(V1 + "\n"); s2.save()
    out2 = d.submit_concerns(s2, CLAIMS, [good()], independent_verdicts={pk: {"verdict": "DOWNGRADE", "reason": "less consequential"}})
    assert out2["downgraded"][0]["new_status"] == "minor"
    s3 = d.Session(V1 + "\n\n"); s3.save()
    assert not d.submit_concerns(s3, CLAIMS, [good()], independent_verdicts={})["admitted"]  # no verdict supplied -> not admitted


def test_ledger_is_frozen_and_cannot_be_overwritten():
    s = d.Session(V1); s.save()
    first = d.submit_concerns(s, CLAIMS, [good()])
    again = d.submit_concerns(s, CLAIMS, [good()])           # identical: fine
    assert again["ledger_sha256"] == first["ledger_sha256"]
    with pytest.raises(ValueError, match="frozen"):
        d.submit_concerns(s, CLAIMS, [good(), other(0)])    # different content for the same round


def test_tampered_ledger_is_detected(tmp_path):
    s1 = d.Session(V1); s1.save(); d.submit_concerns(s1, CLAIMS, [good()])
    p = d._ledger_path(s1.id, 1)
    data = json.loads(p.read_text())
    data["ledger"]["concerns"][0]["title"] = "edited"
    p.write_text(json.dumps(data))
    s2 = d.Session(V2); s2.save()
    with pytest.raises(ValueError, match="modified after it was frozen"):
        d.revision_round(s2, s1.id, {})


def test_revision_closure_needs_changed_text_that_addresses_the_concern():
    s1 = d.Session(V1); s1.save(); d.submit_concerns(s1, CLAIMS, [good()])
    s2 = d.Session(V2); s2.save()
    def closure(q, **kw):
        return d.revision_round(s2, s1.id, {"MC-001": {"status": "VERIFIED_CLOSED", "evidence_quote": q, **kw}})["ledger_status"][0]
    assert closure("We added a randomized control arm.")["status"] == "OPEN"                       # not in the revision
    unrelated = closure("We also report a new subgroup of 12 people who all improved.")            # real, changed, but unrelated
    assert unrelated["status"] == "OPEN" and "does not appear to address" in unrelated["problems"][0]
    stale = closure("There was no randomized control group.")                                      # real but unchanged text
    assert stale["status"] == "OPEN"
    ok = closure("is associated with a 20% improvement in outcome Y")
    assert ok["status"] == "VERIFIED_CLOSED"


def test_revision_rounds_chain_ledgers_and_block_goalposts():
    s1 = d.Session(V1); s1.save(); first = d.submit_concerns(s1, CLAIMS, [good()])
    s2 = d.Session(V2); s2.save()
    r = d.revision_round(s2, s1.id, {"MC-001": {"status": "VERIFIED_CLOSED", "evidence_quote": "is associated with a 20% improvement in outcome Y"}},
                         new_concerns=[good(title="wish", origin="would_be_nice", anchors=["Mean Y increased from 50 to 60 units"])])
    assert r["new_concerns_rejected"] and "moving goalposts" in r["new_concerns_rejected"][0]["reasons"][0]
    assert r["editorial_decision"]["recommendation"] == "ACCEPT"
    assert r["parent_ledger_sha256"] == first["ledger_sha256"] and d._ledger_path(s2.id, 2).exists()


def test_new_concern_must_be_introduced_by_revision_and_field_development_needs_a_source():
    s1 = d.Session(V1); s1.save(); d.submit_concerns(s1, CLAIMS, [good()])
    s2 = d.Session(V2); s2.save()
    st = {"MC-001": {"status": "VERIFIED_CLOSED", "evidence_quote": "is associated with a 20% improvement in outcome Y"}}
    new_ok = good(title="subgroup", origin="introduced_by_revision", anchors=["a new subgroup of 12 people who all improved"],
                  claim_ids=["C2"], failure_mechanism="A subgroup of twelve people all improved so selection of the subgroup after the fact is possible.")
    old_text = good(title="old", origin="introduced_by_revision", anchors=["There was no randomized control group."])
    r = d.revision_round(s2, s1.id, st, [new_ok, old_text])
    assert len(r["new_concerns_accepted"]) == 1 and r["new_concerns_accepted"][0]["label"].startswith("NEW")
    assert any("already existed" in x for x in r["new_concerns_rejected"][0]["reasons"])
    fd = {**new_ok, "origin": "field_development"}
    s3 = d.Session(V2 + "\n"); s3.save()  # same revision, new session id -> new round-2 ledger
    r2 = d.revision_round(s3, s1.id, st, [fd])
    assert r2["new_concerns_rejected"] and "external_source" in r2["new_concerns_rejected"][0]["reasons"][0]


def test_lint_flags_information_loss_extra_majors_length_and_recommendation():
    s = d.Session(V1); s.save()
    gate = d.submit_concerns(s, CLAIMS, [good(), other(0)])
    good_review = ("## Summary\nThe paper reports one cohort.\n\n## Major concerns\n1. No counterfactual: the single group cannot separate the effect from time trends.\n\n"
                   "2. Outcome timing: the outcome was measured only once so spontaneous recovery is not separated.\n\n## Recommendation\nMajor revision.\n")
    assert d.lint_review(good_review, gate)["ok"]
    lost = d.lint_review("## Major concerns\n1. No counterfactual in the design.\n\n## Recommendation\nMajor revision.", gate)
    assert any(f["check"] == "information_loss" and "Outcome timing" in f["note"] for f in lost["findings"])
    extra = d.lint_review(good_review.replace("## Recommendation", "3. A third made-up major point.\n\n## Recommendation"), gate)
    assert any(f["check"] == "extra_major_comments" for f in extra["findings"])
    assert any(f["check"] == "recommendation" for f in d.lint_review(good_review.replace("Major revision.", "Looks fine."), gate)["findings"])
    assert any(f["check"] == "length" for f in d.lint_review(good_review, gate, max_words=10)["findings"])


def test_inspect_code_points_at_shared_lag_and_leakage():
    code = '''
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

def align_all(data, lag):
    out = []
    for subject in data:
        out.append(np.roll(subject, lag))
    return out

def estimate():
    lag = 12
    for participant in range(20):
        x = signals[participant][lag:]
    return lag

def fit_model(X, y):
    Xs = StandardScaler().fit_transform(X)
    Xtr, Xte, ytr, yte = train_test_split(Xs, y)
    return Xtr
'''
    r = d.inspect_code(code, "analysis.py")
    kinds = {p["kind"] for p in r["pointers"]}
    assert {"lag_or_shift", "shared_lag_across_subjects", "preprocess_before_split", "unseeded_split"} <= kinds
    assert all(p["line"] > 0 and p["check"] for p in r["pointers"])


def test_trace_claim_returns_result_and_method_passages():
    s = d.Session(V1)
    t = d.trace_claim(s, "Intervention X causes a 20% improvement")
    assert t["result_passages"] and t["method_passages"] and len(t["ask"]) >= 3


def test_inspect_code_finds_index_offset_off_by_one_window_ungrouped_cv_and_scaler_leak():
    code = '''
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold

def align_all(neural_all, lags):
    out = []
    for p in range(neural_all.shape[0]):
        out.append(np.roll(neural_all[p], lags[p - 1]))
    return out

def trial_features(alpha, stim_bins):
    return alpha[:, stim_bins + 1]

def decode(features, labels, n_participants):
    X = StandardScaler().fit_transform(features)
    cv = KFold(n_splits=n_participants, shuffle=True)
    for tr, te in cv.split(X):
        pass
'''
    kinds = {p["kind"] for p in d.inspect_code(code, "a.py")["pointers"]}
    assert {"index_offset_in_loop", "offset_on_event_index", "cv_not_grouped", "preprocess_before_split", "lag_or_shift"} <= kinds
    clean = "def f(x, subjects):\n    from sklearn.model_selection import GroupKFold\n    return GroupKFold(5)\n"
    assert not {p["kind"] for p in d.inspect_code(clean)["pointers"]} & {"cv_not_grouped", "index_offset_in_loop"}
