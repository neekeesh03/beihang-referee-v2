"""Reasoning-focused regression suite. These tests do not ask 'does the feature run?' but 'does the gate behave
correctly on adversarial cases?' and pin the rates that matter: unsupported-concern admission, false closure,
critical-defect retention, and information loss between agents (gate -> written review)."""
import pytest

from referee import direction as d
from referee.evals.reasoning_metrics import closure_metrics, gate_metrics, retention_metrics
from tests.test_direction import CLAIMS, V1, V2, good, other


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("REFEREE_HOME", str(tmp_path))


def test_gate_adversarial_suite_has_zero_unsupported_admissions_and_keeps_every_critical_defect():
    s = d.Session(V1)
    cases = [
        {"name": "decisive grounded defect", "concern": good(), "expect": "admit", "critical": True},
        {"name": "second grounded defect", "concern": other(0), "expect": "admit", "critical": False},
        {"name": "real quote, irrelevant to the concern", "concern": good(anchors=["We thank the Hospital Foundation for lunch and parking support"]), "expect": "reject"},
        {"name": "invented quote", "concern": good(anchors=["Participants were recruited from three hospitals in Berlin."]), "expect": "reject"},
        {"name": "confidence is NaN", "concern": good(confidence=float("nan")), "expect": "reject"},
        {"name": "confidence above 1", "concern": good(confidence=9), "expect": "reject"},
        {"name": "confidence is a boolean", "concern": good(confidence=True), "expect": "reject"},
        {"name": "fails own steelman", "concern": good(survives_steelman=False), "expect": "reject"},
        {"name": "steelman text contradicts the flag", "concern": good(steelman_survival="This does not survive the authors' reading."), "expect": "reject"},
        {"name": "vague closure", "concern": good(closure_criterion="improve it"), "expect": "reject"},
        {"name": "missing mechanism", "concern": good(failure_mechanism=""), "expect": "reject"},
        {"name": "new data demanded for a supporting claim", "concern": good(claim_ids=["C2"], fix_type="new_data"), "expect": "reject"},
    ]
    m = gate_metrics(s, CLAIMS, cases)
    assert m["unsupported_admission_rate"] == 0.0, [c for c in m["cases"] if c["expect"] == "reject" and c["admitted"]]
    assert m["valid_rejection_rate"] == 0.0
    assert m["critical_defect_retention"] == 1.0


def test_closure_adversarial_suite_has_zero_false_closures_and_no_missed_valid_closures():
    s1 = d.Session(V1); s1.save(); d.submit_concerns(s1, CLAIMS, [good()])
    s2 = d.Session(V2)
    cases = [
        {"name": "valid: changed text addresses the criterion", "new_session": s2, "prior_id": s1.id, "expect_closed": True,
         "status_entry": {"status": "VERIFIED_CLOSED", "evidence_quote": "is associated with a 20% improvement in outcome Y"}},
        {"name": "quote not in the revision", "new_session": s2, "prior_id": s1.id, "expect_closed": False,
         "status_entry": {"status": "VERIFIED_CLOSED", "evidence_quote": "We added a randomized control arm to the design."}},
        {"name": "real changed text, unrelated to the concern", "new_session": s2, "prior_id": s1.id, "expect_closed": False,
         "status_entry": {"status": "VERIFIED_CLOSED", "evidence_quote": "We also report a new subgroup of 12 people who all improved."}},
        {"name": "text that was already there before the revision", "new_session": s2, "prior_id": s1.id, "expect_closed": False,
         "status_entry": {"status": "VERIFIED_CLOSED", "evidence_quote": "There was no randomized control group."}},
        {"name": "claims closed with no evidence at all", "new_session": s2, "prior_id": s1.id, "expect_closed": False,
         "status_entry": {"status": "VERIFIED_CLOSED"}},
    ]
    m = closure_metrics(cases)
    assert m["false_closure_rate"] == 0.0 and m["missed_valid_closure_rate"] == 0.0


def test_scientific_findings_survive_the_handoff_to_the_written_review():
    s = d.Session(V1); s.save()
    gate = d.submit_concerns(s, CLAIMS, [good(), other(0), other(1, claim_ids=["C2"])])
    full = ("## Major concerns\n1. No counterfactual: the single group cannot separate the effect from time trends.\n\n"
            "2. Outcome timing: measured only once after treatment so spontaneous recovery is not separated.\n\n"
            "## Minor comments\nSingle cohort size: one cohort limits generalisation.\n")
    assert retention_metrics(gate, full) == {"admitted_retention": 1.0, "p0_retention": 1.0}
    lossy = "## Major concerns\n1. Outcome timing: measured only once after treatment.\n"
    m = retention_metrics(gate, lossy)
    assert m["p0_retention"] < 1.0 and m["admitted_retention"] < 1.0   # a decisive concern vanished: caught
    notes = " ".join(f["note"] for f in d.lint_review(lossy, gate)["findings"] if f["check"] == "information_loss")
    assert "No counterfactual" in notes and "Outcome timing" not in notes


def test_many_minor_or_supporting_concerns_do_not_escalate_the_recommendation():
    s = d.Session(V1); s.save()
    minors = [other(i, claim_ids=["C2"], consequence_level="weakens", fix_type="wording") for i in range(4)]
    out = d.submit_concerns(s, CLAIMS, minors)
    assert len(out["admitted"]) >= 3
    assert out["editorial_decision"]["recommendation"] == "MINOR_REVISION"
    assert "Driving:" in out["editorial_decision"]["basis"]  # the explanation names the actual drivers


def test_decision_basis_matches_the_concerns_that_drive_it():
    s = d.Session(V1); s.save()
    out = d.submit_concerns(s, CLAIMS, [good(fix_type="reanalysis")])
    dec = out["editorial_decision"]
    assert dec["recommendation"] == "MAJOR_REVISION"
    assert dec["drivers"][0]["concern_id"] == "MC-001" and "MC-001" in dec["basis"] and "reanalysis" in dec["basis"]
