from referee.decision import editorial_recommendation, classify_fix

CLAIMS = [{"claim_id": "C1", "centrality": "central"}, {"claim_id": "C2", "centrality": "supporting"}]


def concern(cid, claim, resolution, consequence="Interpretation is weakened.", mech="Detail is missing."):
    return {"concern_id": cid, "title": cid, "claim_ids": [claim], "minimum_resolution": resolution,
            "scientific_consequence": consequence, "failure_mechanism": mech}


def test_nothing_verified_is_accept():
    assert editorial_recommendation(CLAIMS, [])["recommendation"] == "ACCEPT"


def test_supporting_claim_wording_fix_is_minor_not_major():
    r = editorial_recommendation(CLAIMS, [concern("a", "C2", "Clarify the sampling description.")])
    assert r["recommendation"] == "MINOR_REVISION"
    assert r["would_become_if_drivers_closed"] == "ACCEPT"


def test_central_claim_needing_reanalysis_is_major():
    r = editorial_recommendation(CLAIMS, [concern("a", "C1", "Re-analyse with a sensitivity analysis.")])
    assert r["recommendation"] == "MAJOR_REVISION"


def test_central_claim_invalidated_needing_new_data_is_reject_in_current_form():
    r = editorial_recommendation(CLAIMS, [concern("a", "C1", "Collect an independent validation cohort.",
                                                  consequence="The central conclusion is unsupported.")])
    assert r["recommendation"] == "REJECT_IN_CURRENT_FORM"


def test_many_small_concerns_escalate():
    cs = [concern(str(i), "C2", "Clarify wording.") for i in range(3)]
    assert editorial_recommendation(CLAIMS, cs)["recommendation"] == "MAJOR_REVISION"


def test_gross_numerical_slip_alone_is_minor():
    assert editorial_recommendation(CLAIMS, [], automated_flags=1)["recommendation"] == "MINOR_REVISION"


def test_fix_classifier():
    assert classify_fix("Reword the abstract") == "wording"
    assert classify_fix("Recompute with bootstrap") == "reanalysis"
    assert classify_fix("Recruit a new cohort") == "new_data"
