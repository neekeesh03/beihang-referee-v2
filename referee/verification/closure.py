import re

# A closure criterion is "testable" when someone could look at the revised paper and say yes or no.
# Stems (not whole words) so "reconcile", "reconciliation" and "reconciled" all count.
_OBSERVABLE_STEMS = (
    "demonstrat", "report", "remov", "provid", "show", "recalculat", "recomput", "validat", "replicat", "reframe",
    "includ", "match", "reconcil", "compar", "quantif", "state", "identif", "document", "list", "describ", "map",
    "give", "add", "clarif", "separat", "specif", "defin", "justif", "disclos", "tabulat", "present", "cite",
    "discuss", "narrow", "reword", "revis", "rewrit", "replac", "correct", "rerun", "re-run", "repeat", "evaluat",
    "measur", "test", "analys", "analyz", "adjust", "control", "quot", "name", "preregist", "pre-regist", "share",
    "deposit", "publish", "releas", "upload", "link", "label", "mark", "distinguish", "frame", "call the", "no longer",
    "reconstruct", "reproduc", "locat", "verif", "check", "trace", "recover", "derive", "calculat", "comput", "access", "annotat", "append", "tag", "pin", "freez", "archiv", "attach", "supply", "make available", "explain",
)
_VAGUE = re.compile(r"^\s*(address|fix|improve|resolve|handle|consider)\b[^.]{0,30}\.?\s*$", re.I)


def assess_closure_test(criterion: str) -> dict:
    c = (criterion or "").strip()
    low = c.lower()
    observable = any(w in low for w in _OBSERVABLE_STEMS) and not _VAGUE.match(c)
    ok = len(c) >= 20 and observable
    return {"criterion": c, "nonempty": bool(c), "actionable": ok, "status": "testable" if ok else "weak"}
