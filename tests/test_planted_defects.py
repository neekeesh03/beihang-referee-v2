import re
from pathlib import Path

from referee.direction import inspect_code
from referee.verification.consistency import run_automated_checks

FX = Path(__file__).resolve().parent.parent / "evals" / "planted_defects"


def _code(text):
    return re.search(r"```python\n(.*?)```", text, re.S).group(1)


def test_subtle_fixture_code_defects_are_pointed_at_without_a_model():
    text = (FX / "manuscript_subtle.md").read_text(encoding="utf-8")
    pts = inspect_code(_code(text), "analysis.py")["pointers"]
    by_kind = {p["kind"]: p for p in pts}
    assert "lags[p - 1]" in by_kind["index_offset_in_loop"]["code"]          # S1 wrong participant's lag
    assert "stim_bins + 1" in by_kind["offset_on_event_index"]["code"]        # S2 post-stimulus bin
    assert "KFold" in by_kind["cv_not_grouped"]["code"]                       # S3 not leave-one-participant-out
    assert "StandardScaler" in by_kind["preprocess_before_split"]["code"]     # S4 scaler before the split


def test_subtle_fixture_numeric_defect_is_flagged():
    f = run_automated_checks((FX / "manuscript_subtle.md").read_text(encoding="utf-8"))["findings"]
    assert any(x["check"] == "test_statistic_vs_p" and "r(18)" in x["quote"] for x in f)  # S5


def test_easy_fixture_numeric_defect_is_flagged():
    f = run_automated_checks((FX / "manuscript_easy.md").read_text(encoding="utf-8"))["findings"]
    assert any(x["severity"] == "gross" and "t(19) = 1.20" in x["quote"] for x in f)
