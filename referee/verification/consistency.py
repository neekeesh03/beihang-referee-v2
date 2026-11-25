"""Offline, deterministic consistency checks. No model, no network, no API key.

1. Reported test statistics vs reported p-values (t, F, chi-square, r, z),
   recomputed with the standard distributions (pure Python, stdlib only).
2. GRIM: can a reported mean arise from n integer observations?
3. Counts vs percentages ("12/40 (30%)").
4. Reference hygiene: numeric citations vs the reference list, duplicate DOIs,
   future years.

Every finding says what was recomputed so a human can check it in seconds.
Rounding is respected: a p-value is only called inconsistent if it cannot be
produced by ANY test statistic that rounds to the reported one.
"""
from __future__ import annotations

import datetime as _dt
import math
import re
from typing import Any

# ---------- distribution functions (stdlib only) ----------

def _betacf(a: float, b: float, x: float) -> float:
    MAXIT, EPS, FPMIN = 300, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > FPMIN else FPMIN)
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d; d = d if abs(d) > FPMIN else FPMIN
        c = 1.0 + aa / c; c = c if abs(c) > FPMIN else FPMIN
        d = 1.0 / d; h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d; d = d if abs(d) > FPMIN else FPMIN
        c = 1.0 + aa / c; c = c if abs(c) > FPMIN else FPMIN
        d = 1.0 / d; delta = d * c; h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_bt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x)
    bt = math.exp(ln_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def gammaq(a: float, x: float) -> float:
    """Regularized upper incomplete gamma Q(a, x)."""
    if x <= 0:
        return 1.0
    if x < a + 1.0:  # series for P
        ap, s, d = a, 1.0 / a, 1.0 / a
        for _ in range(1000):
            ap += 1.0; d *= x / ap; s += d
            if abs(d) < abs(s) * 1e-15:
                break
        return 1.0 - s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    b, c, d = x + 1.0 - a, 1e300, 1.0 / (x + 1.0 - a)
    h = d
    for i in range(1, 1000):
        an = -i * (i - a); b += 2.0
        d = an * d + b; d = d if abs(d) > 1e-300 else 1e-300
        c = b + an / c; c = c if abs(c) > 1e-300 else 1e-300
        d = 1.0 / d; delta = d * c; h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def p_t(t: float, df: float) -> float:
    return betainc(df / 2.0, 0.5, df / (df + t * t))


def p_f(f: float, d1: float, d2: float) -> float:
    return betainc(d2 / 2.0, d1 / 2.0, d2 / (d2 + d1 * f)) if f > 0 else 1.0


def p_chi2(x: float, df: float) -> float:
    return gammaq(df / 2.0, x / 2.0)


def p_z(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2.0))


def p_r(r: float, df: float) -> float:
    if abs(r) >= 1:
        return 0.0
    return p_t(r * math.sqrt(df / (1.0 - r * r)), df)

# ---------- statistic / p-value consistency ----------

_P = r"p\s*([<=>≤≥])\s*(\d*\.\d+|\d+(?:\.\d+)?(?:e-?\d+)?)"
_NUM = r"(-?\d*\.\d+|-?\d+)"
PATTERNS = {
    "t": re.compile(r"\bt\s*\(\s*(\d+(?:\.\d+)?)\s*\)\s*=\s*" + _NUM + r"\s*[,;]?\s*" + _P, re.I),
    "F": re.compile(r"\bF\s*\(\s*(\d+)\s*,\s*(\d+(?:\.\d+)?)\s*\)\s*=\s*" + _NUM + r"\s*[,;]?\s*" + _P),
    "chi2": re.compile(r"(?:χ\s*2|χ²|\bchi-?\s*square[d]?|\bchi2|\bX2)\s*\(\s*(\d+)(?:\s*,\s*N\s*=\s*\d+)?\s*\)\s*=\s*" + _NUM + r"\s*[,;]?\s*" + _P, re.I),
    "r": re.compile(r"\br\s*\(\s*(\d+)\s*\)\s*=\s*" + _NUM + r"\s*[,;]?\s*" + _P),
    "z": re.compile(r"\bz\s*=\s*" + _NUM + r"\s*[,;]?\s*" + _P),
}


def _decimals(s: str) -> int:
    return len(s.split(".")[1]) if "." in s else 0


def _p_range(kind: str, args: tuple[float, ...], stat_str: str) -> tuple[float, float]:
    """Smallest/largest p over every statistic value that rounds to the reported one."""
    stat = float(stat_str)
    half = 0.5 * 10 ** (-_decimals(stat_str))
    vals = []
    for s in (abs(stat) - half if abs(stat) - half > 0 else 0.0, abs(stat), abs(stat) + half):
        if kind == "t": vals.append(p_t(s, args[0]))
        elif kind == "F": vals.append(p_f(s, args[0], args[1]))
        elif kind == "chi2": vals.append(p_chi2(s, args[0]))
        elif kind == "r": vals.append(p_r(s, args[0]))
        else: vals.append(p_z(s))
    return min(vals), max(vals)


def _p_consistent(op: str, rep: float, rep_str: str, lo: float, hi: float) -> bool:
    op = {"≤": "<", "≥": ">"}.get(op, op)
    if op == "=":
        half = 0.5 * 10 ** (-_decimals(rep_str))
        return lo <= rep + half + 1e-12 and hi >= rep - half - 1e-12
    if op == "<":
        return lo < rep + 1e-12
    return hi > rep - 1e-12


def check_test_statistics(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for kind, rx in PATTERNS.items():
        for m in rx.finditer(text):
            g = m.groups()
            op, p_str = g[-2], g[-1]
            try:
                rep = float(p_str)
                if kind == "F":
                    args, stat_str = (float(g[0]), float(g[1])), g[2]
                elif kind == "z":
                    args, stat_str = (), g[0]
                else:
                    args, stat_str = (float(g[0]),), g[1]
                lo, hi = _p_range(kind, args, stat_str)
            except (ValueError, ZeroDivisionError, OverflowError):
                continue
            ok = _p_consistent(op, rep, p_str, lo, hi)
            if ok:
                continue
            comp = (lo + hi) / 2.0
            nop = {"≤": "<", "≥": ">"}.get(op, op)
            claims_sig = (nop == "<" and rep <= 0.05) or (nop == "=" and rep < 0.05)
            claims_nonsig = (nop == ">" and rep >= 0.05) or (nop == "=" and rep >= 0.05)
            gross = (claims_sig and lo >= 0.05) or (claims_nonsig and hi < 0.05)
            out.append({
                "check": "test_statistic_vs_p", "test": kind, "quote": m.group(0).strip(),
                "reported_p": f"{op}{p_str}", "recomputed_p": float(f"{comp:.3g}"),
                "recomputed_range": [float(f"{lo:.3g}"), float(f"{hi:.3g}")],
                "severity": "gross" if gross else "minor",
                "note": ("Reported significance changes when p is recomputed from the statistic and degrees of freedom."
                         if gross else "Reported p differs from the recomputed value beyond rounding."),
            })
    return out

# ---------- GRIM ----------

def grim_possible(mean_str: str, n: int, items: int = 1) -> bool:
    d = _decimals(mean_str)
    mean = float(mean_str)
    total = n * items
    if total <= 0 or total >= 10 ** d * 10:
        return True  # GRIM has no power
    k = round(mean * total)
    for kk in (k - 1, k, k + 1):
        if kk >= 0 and abs(round(kk / total, d) - mean) < 10 ** -(d + 3):
            return True
    return False


_GRIM = [re.compile(r"\bM\s*=\s*(\d+\.\d+)[^()\n]{0,60}?\bn\s*=\s*(\d+)", re.I),
         re.compile(r"\bn\s*=\s*(\d+)[^()\n]{0,60}?\bM\s*=\s*(\d+\.\d+)", re.I)]


def check_grim(text: str) -> list[dict[str, Any]]:
    out = []
    for i, rx in enumerate(_GRIM):
        for m in rx.finditer(text):
            mean_s, n_s = (m.group(1), m.group(2)) if i == 0 else (m.group(2), m.group(1))
            n = int(n_s)
            if 2 <= n <= 100 and not grim_possible(mean_s, n):
                out.append({"check": "grim", "quote": m.group(0).strip(), "severity": "minor",
                            "note": f"A mean of {mean_s} cannot be produced by {n} whole-number scores. Only meaningful if the "
                                    "measure is integer-valued (counts, single Likert items). If so, n or the mean is misreported."})
    return out

# ---------- counts vs percentages ----------

_FRAC = re.compile(r"\b(\d+)\s*/\s*(\d+)\s*\(\s*(\d+(?:\.\d+)?)\s*%\s*\)")


def check_percentages(text: str) -> list[dict[str, Any]]:
    out = []
    for m in _FRAC.finditer(text):
        a, b, pct_s = int(m.group(1)), int(m.group(2)), m.group(3)
        if b == 0:
            continue
        calc = 100.0 * a / b
        half = 0.5 * 10 ** (-_decimals(pct_s))
        if abs(calc - float(pct_s)) > half + 1e-9:
            out.append({"check": "count_vs_percent", "quote": m.group(0), "severity": "minor",
                        "note": f"{a}/{b} is {calc:.1f}%, not {pct_s}%."})
    return out

# ---------- reference hygiene ----------

_DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
_CITE = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]")
_REF_HEAD = re.compile(r"^\s*#*\s*(references|bibliography|literature cited)\s*$", re.I | re.M)
_REF_ITEM = re.compile(r"^\s*\[?(\d{1,3})[\].)]\s+\S", re.M)


def _expand(spec: str) -> set[int]:
    nums: set[int] = set()
    for part in re.split(r"\s*,\s*", spec):
        rng = re.split(r"\s*[–-]\s*", part)
        if len(rng) == 2 and rng[0].isdigit() and rng[1].isdigit() and 0 < int(rng[1]) - int(rng[0]) < 60:
            nums.update(range(int(rng[0]), int(rng[1]) + 1))
        elif part.strip().isdigit():
            nums.add(int(part))
    return nums


def check_references(text: str, now_year: int | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    now_year = now_year or _dt.date.today().year
    head = None
    for head in _REF_HEAD.finditer(text):
        pass
    body, refs = (text[:head.start()], text[head.end():]) if head else (text, "")
    listed = {int(m.group(1)) for m in _REF_ITEM.finditer(refs)}
    cited: set[int] = set()
    for m in _CITE.finditer(body):
        cited |= _expand(m.group(1))
    if listed and cited:
        missing = sorted(n for n in cited if n not in listed)
        uncited = sorted(n for n in listed if n not in cited)
        if missing:
            out.append({"check": "reference_cited_not_listed", "severity": "minor",
                        "note": f"In-text citation number(s) {missing[:15]} have no entry in the reference list."})
        if uncited:
            out.append({"check": "reference_listed_not_cited", "severity": "minor",
                        "note": f"Reference list entries {uncited[:15]} are never cited in the text."})
    dois = [d.rstrip(".,;)") for d in _DOI.findall(refs or text)]
    dup = sorted({d.lower() for d in dois if [x.lower() for x in dois].count(d.lower()) > 1})
    if dup:
        out.append({"check": "reference_duplicate_doi", "severity": "minor", "note": f"Duplicate DOI(s) in references: {dup[:8]}."})
    future = sorted({int(y) for y in re.findall(r"\((\d{4})[a-z]?\)", refs) if int(y) > now_year + 1})
    if future:
        out.append({"check": "reference_future_year", "severity": "minor", "note": f"Reference year(s) later than {now_year}: {future}."})
    return out


def run_automated_checks(text: str, now_year: int | None = None) -> dict[str, Any]:
    findings = (check_test_statistics(text) + check_grim(text) + check_percentages(text) + check_references(text, now_year))
    return {
        "method": "offline recomputation; no model, no network",
        "findings": findings,
        "gross_inconsistencies": sum(1 for f in findings if f.get("severity") == "gross"),
        "note": "Findings are objective recomputations, not judgements of scientific quality. Absence of findings does not mean the numbers are correct.",
    }
