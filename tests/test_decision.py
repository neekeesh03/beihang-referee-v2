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


def test_many_small_concerns_do_not_escalate_but_several_consequential_ones_do():
    small = [concern(str(i), "C2", "Clarify wording.") for i in range(5)]
    assert editorial_recommendation(CLAIMS, small)["recommendation"] == "MINOR_REVISION"
    big = [{**concern(str(i), "C2", "Clarify wording."), "consequence_level": "changes_interpretation"} for i in range(3)]
    assert editorial_recommendation(CLAIMS, big)["recommendation"] == "MAJOR_REVISION"


def test_negated_requests_are_not_read_as_new_data():
    assert classify_fix("No new data are needed; reword the abstract.") == "wording"
    assert classify_fix("Reword it. There is no need to recruit more participants or run new experiments.") == "wording"
    assert classify_fix("Recruit an independent cohort.") == "new_data"
    assert classify_fix("whatever", fix_type="reanalysis") == "reanalysis"   # explicit judgement wins over keywords


def test_gross_numerical_slip_alone_is_minor():
    assert editorial_recommendation(CLAIMS, [], automated_flags=1)["recommendation"] == "MINOR_REVISION"


def test_fix_classifier():
    assert classify_fix("Reword the abstract") == "wording"
    assert classify_fix("Recompute with bootstrap") == "reanalysis"
    assert classify_fix("Recruit a new cohort") == "new_data"


def test_comparing_saved_outputs_counts_as_reanalysis_and_matched_control_as_new_data():
    assert classify_fix("Compare the saved outputs per dataset and report agreement.") == "reanalysis"
    assert classify_fix("Run a matched control with the same model without the tool.") == "new_data"


def test_pipeline_cap_scales_with_central_claims_and_reports_what_it_drops():
    from referee.decision import consolidate_and_cap
    claims = [{"claim_id": "C1", "centrality": "central"}, {"claim_id": "C2", "centrality": "supporting"}]
    mk = lambda i, t, m, lvl="changes_interpretation": {"concern_id": f"M{i}", "title": t, "claim_ids": ["C1"], "failure_mechanism": m, "consequence_level": lvl}
    items = [mk(1, "alpha issue", "alpha mechanism about sampling frame bias"), mk(2, "beta issue", "beta mechanism about outcome timing leak"),
             mk(3, "gamma issue", "gamma mechanism about exclusion rules applied late"), mk(4, "delta issue", "delta mechanism about statistical power shortfall"),
             mk(5, "alpha again", "alpha mechanism about sampling frame bias")]
    kept, dropped = consolidate_and_cap(claims, items, hard_max=12)
    assert len(kept) == 3                                   # one central claim -> 3
    reasons = {x["status"] for x in dropped}
    assert reasons == {"merged_into_other", "over_budget"} and all(x["admission_errors"] for x in dropped)
