from referee.verification.consistency import (p_t, p_f, p_chi2, p_z, check_test_statistics, check_grim,
                                              check_percentages, check_references, run_automated_checks)


def test_distributions_match_textbook_critical_values():
    assert abs(p_t(2.228, 10) - 0.05) < 5e-4
    assert abs(p_f(3.316, 2, 30) - 0.05) < 5e-4
    assert abs(p_chi2(5.991, 2) - 0.05) < 5e-4
    assert abs(p_z(1.96) - 0.05) < 5e-4


def test_correct_reporting_is_not_flagged():
    assert check_test_statistics("t(28) = 2.10, p = .045; F(1, 40) = 4.50, p = .04; chi2(2) = 5.99, p = .05; r(48) = .30, p = .035") == []


def test_wrong_significance_is_gross():
    f = check_test_statistics("Groups differed, t(28) = 1.20, p < .05.")
    assert f and f[0]["severity"] == "gross"


def test_nonsignificant_reported_but_actually_significant_is_gross():
    f = check_test_statistics("t(20) = 2.30, p = .30")
    assert f and f[0]["severity"] == "gross"


def test_grim_and_percentages():
    assert check_grim("(M = 3.45, SD = 1.2, n = 15)")
    assert not check_grim("(M = 3.47, SD = 1.2, n = 15)")
    assert check_percentages("13/40 (35%)")
    assert not check_percentages("12/40 (30%)")


def test_references():
    doc = "Text [1,2] and [4-5].\nReferences\n1. A (2020) 10.1000/a.1\n2. B (2031) 10.1000/a.1\n3. C (2019)\n"
    kinds = {f["check"] for f in check_references(doc, 2026)}
    assert {"reference_cited_not_listed", "reference_listed_not_cited", "reference_duplicate_doi", "reference_future_year"} <= kinds


def test_report_shape():
    r = run_automated_checks("t(28) = 1.20, p < .05")
    assert r["gross_inconsistencies"] == 1 and "no model" in r["method"]
