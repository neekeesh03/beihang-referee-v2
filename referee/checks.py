"""`referee check`: model-free manuscript checks. No API key needed."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .documents import DocumentLoader
from .verification.consistency import run_automated_checks


def run_checks(paths: list[str], literature: bool = False, figures: bool = False) -> dict[str, Any]:
    loader = DocumentLoader()
    text = "\n\n".join(loader.load(p).text for p in paths)
    result: dict[str, Any] = {"files": [Path(p).name for p in paths], "automated_checks": run_automated_checks(text)}
    if literature:
        from .verification.literature_check import run_literature_check
        result["literature"] = run_literature_check(text)
    if figures:
        from .verification.figures import check_figures
        result["figures"] = [{"file": Path(p).name, **check_figures(p)} for p in paths if str(p).lower().endswith(".pdf")]
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
    for fig in r.get("figures") or []:
        L += ["", f"## Figure duplicate check: {fig['file']}"]
        if fig.get("status") != "ok":
            L.append(fig.get("note", "unavailable"))
            continue
        hi = [f for f in fig["findings"] if f["priority"] == "high"]
        lo = [f for f in fig["findings"] if f["priority"] != "high"]
        L.append(f"{fig['images_examined']} image(s) examined; {len(hi)} high-priority and {len(lo)} low-priority possible duplicate pair(s); {len(fig.get('repeated_elements') or [])} repeated element group(s).")
        for f in hi + lo:
            L.append(f"- [{f['priority']}] {f['a']} and {f['b']}: {f['match']} (hash distance {f['hash_distance_bits_of_256']}/256). {f['note']}")
        for g in fig.get("repeated_elements") or []:
            L.append(f"- [repeated element] the same image appears {len(g)} times ({', '.join(g)}): probably a logo, icon or template.")
        L.append("_" + fig["note"] + "_")
    return "\n".join(L) + "\n"
