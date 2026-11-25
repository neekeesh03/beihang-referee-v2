"""Keyless literature checks (no API key, no model).

Uses free public endpoints that need no account: Crossref (DOI records,
retraction notices) and Europe PMC (biomedical + preprint search, no key).
Everything is best-effort: if the network is blocked the check reports
"unavailable" instead of guessing.

Checks
- Does each cited DOI exist, and does the record match the reference text?
  (catches mistyped or fabricated references)
- Has a cited paper been retracted or have a correction/expression of concern?
- Nearest prior art for the manuscript's own title: papers a reader would expect
  to see cited that are not.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Any

UA = "BeihangReferee/2.0 (research tool; https://github.com/neekeesh03/beihang-referee-v2)"
_DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
_WORD = re.compile(r"[a-z0-9]{3,}")
_STOP = frozenset("the and for with from that this are was were into using based study analysis effect effects between their".split())
_DESIGN = frozenset("pilot randomised randomized controlled trial trials cohort preliminary exploratory novel approach evaluation investigation assessment impact role after during among versus within toward towards".split())


def _get(url: str, timeout: float = 20.0, attempts: int = 2) -> dict[str, Any] | None:
    import time
    last: dict[str, Any] = {"_error": "unknown"}
    for i in range(attempts):
        # curl first: it tolerates proxies that truncate chunked responses for Python's urllib
        via_curl = _curl_json(url, timeout)
        if via_curl is not None:
            return via_curl
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", "Accept-Encoding": "identity"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (404, 400):
                return {"_http": e.code}
            last = {"_http": e.code, "_error": f"HTTP {e.code}"}
        except Exception as e:  # network blocked, timeout, truncated read, bad JSON
            last = {"_error": str(e)[:120]}
        time.sleep(1.5 * (i + 1))
    return last


def _curl_json(url: str, timeout: float) -> dict[str, Any] | None:
    import shutil, subprocess
    exe = shutil.which("curl")
    if not exe:
        return None
    try:
        p = subprocess.run([exe, "-s", "-L", "--max-time", str(int(timeout)), "-A", UA, "-H", "Accept: application/json",
                            "-w", "\n%{http_code}", url], capture_output=True, text=True, timeout=timeout + 5)
        body, _, code = p.stdout.rpartition("\n")
        if code in ("404", "400"):
            return {"_http": int(code)}
        if code == "200" and body:
            return json.loads(body)
    except Exception:
        return None
    return None


def _toks(s: str) -> set[str]:
    return {w for w in _WORD.findall(s.lower()) if w not in _STOP}


def verify_doi(doi: str, reference_line: str = "") -> dict[str, Any]:
    doi = doi.rstrip(".,;)")
    data = _get("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/"))
    if not data or "_error" in data:
        return {"doi": doi, "status": "unavailable", "detail": (data or {}).get("_error", "")}
    if data.get("_http") == 404:
        return {"doi": doi, "status": "not_found",
                "note": "Crossref has no record of this DOI. It may be mistyped, from another registry (e.g. DataCite), or invented."}
    msg = data.get("message") or {}
    title = (msg.get("title") or [""])[0]
    res = {"doi": doi, "status": "found", "title": title, "year": ((msg.get("issued") or {}).get("date-parts") or [[None]])[0][0]}
    for upd in msg.get("updated-by") or []:
        t = str(upd.get("type") or "").lower()
        if t in ("retraction", "withdrawal", "removal", "expression_of_concern", "correction", "erratum"):
            res.setdefault("notices", []).append(t)
    if any(n in ("retraction", "withdrawal", "removal") for n in res.get("notices", [])):
        res["status"] = "retracted"
    if reference_line and title:
        a, b = _toks(title), _toks(reference_line)
        overlap = len(a & b) / max(1, len(a))
        res["title_overlap"] = round(overlap, 2)
        if overlap < 0.25 and res["status"] == "found":
            res["status"] = "title_mismatch"
            res["note"] = "The DOI resolves to a different title than the reference text. Check the reference."
    return res


def references_with_dois(text: str) -> list[tuple[str, str]]:
    last: dict[str, tuple[str, str]] = {}
    for line in text.splitlines():
        for d in _DOI.findall(line):
            d = d.rstrip(".,;)")
            last[d.lower()] = (d, line.strip())  # later lines (the reference list) win
    return list(last.values())


def guess_title(text: str) -> str:
    for line in text.splitlines():
        s = line.strip().lstrip("#").strip()
        if 15 <= len(s) <= 220 and not s.lower().startswith(("abstract", "keywords", "doi")):
            return s
    return ""


def nearest_prior_art(title: str, manuscript_text: str, limit: int = 8) -> dict[str, Any]:
    if not title:
        return {"status": "skipped", "note": "No title found."}
    tt = _toks(title) - _DESIGN
    order = [w for w in _WORD.findall(title.lower()) if w in tt]
    terms = list(dict.fromkeys(order))[:5]  # distinctive title words, in title order
    data = None
    for n in (len(terms), 3, 2):  # AND the most specific title words; relax if nothing comes back
        if n < 2 or n > len(terms):
            continue
        q = " AND ".join(terms[:n])
        url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=40&resultType=lite&query="
               + urllib.parse.quote(q))
        data = _get(url)
        if data and "resultList" in data and (data["resultList"] or {}).get("result"):
            break
    if not data or "_error" in data or "_http" in data:
        return {"status": "unavailable", "detail": str((data or {}).get("_error") or (data or {}).get("_http"))}
    low = manuscript_text.lower()
    hits = []
    for r in (data.get("resultList") or {}).get("result", []):
        t = r.get("title") or ""
        if len(_toks(t) & tt) < 2:  # relevance filter: must share >= 2 distinctive words with the manuscript title
            continue
        doi = (r.get("doi") or "").lower()
        cited = bool(doi and doi in low) or (len(t) > 25 and t.lower().rstrip(".") in low)
        hits.append({"title": t, "year": r.get("pubYear"), "journal": r.get("journalTitle"), "doi": r.get("doi"),
                     "cited_by_count": r.get("citedByCount") or 0, "already_cited": cited})
    hits.sort(key=lambda h: -int(h["cited_by_count"]))
    uncited = [h for h in hits if not h["already_cited"]][:limit]
    return {"status": "ok", "query": q, "source": "Europe PMC (no key)", "uncited_candidates": uncited,
            "note": "Search hits sharing distinctive title words with the manuscript that the text does not appear to cite. "
                    "They are candidates to read, not proof of missing citations or of lack of novelty."
                    + ("" if uncited else " Nothing relevant found (this is a coverage limit of the source, not proof of novelty).")}


def run_literature_check(text: str, max_dois: int = 40) -> dict[str, Any]:
    refs = references_with_dois(text)[:max_dois]
    return {
        "doi_checks": [verify_doi(d, line) for d, line in refs],
        "nearest_prior_art": nearest_prior_art(guess_title(text), text),
        "dois_found": len(refs),
    }
