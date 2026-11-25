from referee.verification.closure import assess_closure_test

def test_closure_actionable():
    assert assess_closure_test('Report the corrected denominator and demonstrate that all tables match.')['actionable']


def test_realistic_closure_criteria_from_blind_review_are_accepted():
    for c in ["The revision reconciles attempted and retained tools for each case with reasons for removal.",
              "Readers can reconstruct numerators and denominators from the text and a supplementary table.",
              "The SORT1 result is described as reprioritization and all three candidate genes are shown side by side.",
              "Fix it."]:
        r = assess_closure_test(c)
        assert r["actionable"] == (c != "Fix it.")
