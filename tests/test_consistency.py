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


def test_df_after_statistic_format_is_parsed():
    assert check_test_statistics("t = 2.10, df = 45, p = .04") == []
    f = check_test_statistics("t = 1.10, df = 45, p = .01")
    assert f and f[0]["severity"] == "gross"


def test_real_world_chi_square_df_typo_is_caught():
    # chi2(1)=4.84 gives p=.028; the same statistic with df=2 gives p=.089 (a pattern seen in a published open-access paper)
    assert check_test_statistics("chi2 (1) = 4.84, p = 0.028") == []
    f = check_test_statistics("chi2 (2) = 4.84, p = 0.028")
    assert f and f[0]["severity"] == "gross" and abs(f[0]["recomputed_p"] - 0.089) < 0.003


def test_zero_p_value_is_flagged_but_small_p_is_not():
    from referee.verification.consistency import check_zero_p
    assert check_zero_p("(beta = 0.35, p<0.000)")
    assert not check_zero_p("p < 0.001 and p = 0.0001")


def test_doi_repeated_in_one_entry_is_not_a_duplicate():
    doc = "x\nReferences\n1. A doi:10.1/a.1 and https://doi.org/10.1/a.1\n2. B 10.2/b.2\n"
    assert not [f for f in check_references(doc, 2026) if f["check"] == "reference_duplicate_doi"]
