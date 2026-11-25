import pytest

from referee import direction as d

V1 = """# Demo
## Methods
A single observational cohort of 80 participants received intervention X. There was no randomized control group. Outcome Y was measured after treatment and compared with the cohort's pre-treatment value.
## Results
Mean Y increased from 50 to 60 units after treatment (n=80).
## Conclusion
Intervention X causes a 20% improvement in outcome Y.
"""
V2 = V1.replace("Intervention X causes a 20% improvement in outcome Y.",
                "Intervention X is associated with a 20% improvement in outcome Y; we cannot rule out time trends.") + "\nWe also report a new subgroup of 12 people who all improved.\n"

CLAIMS = [{"claim_id": "C1", "centrality": "central", "text": "X causes a 20% improvement"},
          {"claim_id": "C2", "centrality": "supporting", "text": "Y rose from 50 to 60"}]


def good(**kw):
    c = {"title": "No counterfactual", "claim_ids": ["C1"], "anchors": ["There was no randomized control group."],
         "failure_mechanism": "A single-group pre-post comparison cannot separate the effect from time trends.",
         "scientific_consequence": "The central causal conclusion cannot be supported.",
         "minimum_resolution": "Reframe the conclusion as an association, or add a comparison group analysis.",
         "closure_criterion": "The abstract and conclusion no longer state a causal effect, or the paper reports a valid comparison.",
         "consequence_level": "invalidates", "confidence": 0.85, "steelman": "Authors may argue the effect is large.", "steelman_survival": "Size does not remove regression to the mean."}
    c.update(kw)
    return c


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("REFEREE_HOME", str(tmp_path))


def test_playbook_has_workflow_and_rules():
    p = d.playbook()
    assert len(p["workflow"]) == 8 and {"voice", "stopping", "decision", "elevation"} <= set(p["rules"])


def test_quote_verification_exact_near_and_hallucinated():
    s = d.Session(V1)
    assert d.verify_quote(s, "There was no randomized control group.")["match"] == "exact"
    assert d.verify_quote(s, "there  was NO randomized\ncontrol group")["status"] == "verified"  # whitespace/case tolerant
    assert d.verify_quote(s, "The authors preregistered the protocol on OSF")["status"] == "not_found"


def test_gate_admits_grounded_concern_and_blocks_invented_one():
    s = d.Session(V1); s.save()
    out = d.submit_concerns(s, CLAIMS, [good(), good(title="Invented", anchors=["Participants were recruited from three hospitals in Berlin."])])
    assert [c["concern_id"] for c in out["admitted"]] == ["MC-001"]
    assert out["downgraded"][0]["new_status"] == "question"
    assert out["editorial_decision"]["recommendation"] in ("MAJOR_REVISION", "REJECT_IN_CURRENT_FORM")


def test_low_confidence_and_weak_closure_are_downgraded():
    s = d.Session(V1); s.save()
    out = d.submit_concerns(s, CLAIMS, [good(confidence=0.3), good(title="b", closure_criterion="fix it")])
    assert not out["admitted"] and len(out["downgraded"]) == 2
    assert out["editorial_decision"]["recommendation"] == "ACCEPT"


def test_new_data_demand_on_supporting_claim_is_downgraded():
    s = d.Session(V1); s.save()
    c = good(claim_ids=["C2"], minimum_resolution="Recruit a new cohort and repeat the study.")
    out = d.submit_concerns(s, CLAIMS, [c])
    assert not out["admitted"] and "non-central" in out["downgraded"][0]["downgraded_because"][-1]


def test_budget_of_eight_majors():
    s = d.Session(V1); s.save()
    cs = [good(title=f"t{i}", anchors=[q]) for i, q in enumerate([
        "There was no randomized control group.", "A single observational cohort of 80 participants",
        "Mean Y increased from 50 to 60 units", "Outcome Y was measured after treatment",
        "compared with the cohort's pre-treatment value", "Intervention X causes a 20% improvement"])]
    out = d.submit_concerns(s, CLAIMS, cs)
    assert len(out["admitted"]) == 6 and not out["downgraded"]  # budget is 8


def test_revision_round_requires_evidence_to_close_and_blocks_goalposts():
    s1 = d.Session(V1); s1.save()
    d.submit_concerns(s1, CLAIMS, [good()])
    s2 = d.Session(V2); s2.save()
    # claimed closed with a quote that is not in the revision -> stays open
    r = d.revision_round(s2, s1.id, {"MC-001": {"status": "VERIFIED_CLOSED", "evidence_quote": "We added a randomized control arm."}})
    assert r["ledger_status"][0]["status"] == "OPEN"
    # closed with a real quote from the revision
    r = d.revision_round(s2, s1.id, {"MC-001": {"status": "VERIFIED_CLOSED", "evidence_quote": "is associated with a 20% improvement in outcome Y"}},
                         new_concerns=[good(title="wish", origin="would_be_nice", anchors=["Mean Y increased from 50 to 60 units"])])
    assert r["ledger_status"][0]["status"] == "VERIFIED_CLOSED"
    assert r["new_concerns_rejected"] and "moving goalposts" in r["new_concerns_rejected"][0]["reasons"][0]
    assert r["editorial_decision"]["recommendation"] == "ACCEPT"


def test_new_concern_must_be_introduced_by_revision():
    s1 = d.Session(V1); s1.save(); d.submit_concerns(s1, CLAIMS, [good()])
    s2 = d.Session(V2); s2.save()
    st = {"MC-001": {"status": "VERIFIED_CLOSED", "evidence_quote": "is associated with a 20% improvement in outcome Y"}}
    new_ok = good(title="subgroup", origin="introduced_by_revision", anchors=["a new subgroup of 12 people who all improved"],
                  claim_ids=["C2"])
    old_text = good(title="old", origin="introduced_by_revision", anchors=["There was no randomized control group."])
    r = d.revision_round(s2, s1.id, st, [new_ok, old_text])
    assert len(r["new_concerns_accepted"]) == 1 and r["new_concerns_accepted"][0]["label"].startswith("NEW")
    assert any("already existed" in x for x in r["new_concerns_rejected"][0]["reasons"])


def test_field_development_concern_needs_external_source_and_is_labelled():
    s1 = d.Session(V1); s1.save(); d.submit_concerns(s1, CLAIMS, [good()])
    s2 = d.Session(V2); s2.save()
    st = {"MC-001": {"status": "VERIFIED_CLOSED", "evidence_quote": "is associated with a 20% improvement in outcome Y"}}
    base = good(title="outdated baseline", origin="field_development", claim_ids=["C2"], anchors=["Mean Y increased from 50 to 60 units"])
    r = d.revision_round(s2, s1.id, st, [base])
    assert r["new_concerns_rejected"] and "external_source" in r["new_concerns_rejected"][0]["reasons"][0]
    r = d.revision_round(s2, s1.id, st, [{**base, "external_source": "https://doi.org/10.1000/xyz"}])
    assert r["new_concerns_accepted"] and "field_development" in r["new_concerns_accepted"][0]["label"]


def test_playbook_includes_journal_report_style():
    assert "Two separate verdicts" in d.playbook()["rules"]["report_style"]
