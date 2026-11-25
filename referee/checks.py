"""`referee check`: model-free manuscript checks. No API key needed."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .documents import DocumentLoader
from .verification.consistency import run_automated_checks


def run_checks(paths: list[str], literature: bool = False) -> dict[str, Any]:
    loader = DocumentLoader()
    text = "\n\n".join(loader.load(p).text for p in paths)
    result: dict[str, Any] = {"files": [Path(p).name for p in paths], "automated_checks": run_automated_checks(text)}
    if literature:
        from .verification.literature_check import run_literature_check
        result["literature"] = run_literature_check(text)
    return result


def render_checks_markdown(r: dict[str, Any]) -> str:
    a = r["automated_checks"]
    L = ["# Referee check report (no model, no API key)", "", "Files: " + ", ".join(r["files"]), "",
         f"## Numerical and reference consistency ({len(a['findings'])} finding(s), {a['gross_inconsistencies']} gross)"]
    if not a["findings"]:
        L.append("No inconsistencies found by the offline checks.")
    for f in a["findings"]:
        q = f" `{f['quote']}`" if f.get("quote") else ""
        L.append(f"- **{f['check']}** ({f['severity']}):{q} {f['note']}")
    L += ["", "_" + a["note"] + "_"]
    lit = r.get("literature")
    if lit:
        L += ["", f"## Literature checks (free public sources; {lit['dois_found']} DOI(s) found in the text)"]
        bad = [d for d in lit["doi_checks"] if d["status"] != "found"]
        ok = len(lit["doi_checks"]) - len(bad)
        L.append(f"- {ok} DOI(s) resolved to a matching record.")
        for d in bad:
            L.append(f"- **{d['status']}**: {d['doi']} {d.get('note') or d.get('detail') or ''}" + (f" Notices: {', '.join(d['notices'])}." if d.get("notices") else ""))
        n = lit["nearest_prior_art"]
        L += ["", "### Possible missing prior art"]
        if n.get("status") != "ok":
            L.append(f"Unavailable ({n.get('detail') or n.get('note')}).")
        else:
            L.append(n["note"])
            for h in n["uncited_candidates"]:
                L.append(f"- {h['title']} ({h.get('journal') or 'n/a'}, {h.get('year')}; cited by {h.get('cited_by_count')}) {('doi:' + h['doi']) if h.get('doi') else ''}")
    return "\n".join(L) + "\n"
