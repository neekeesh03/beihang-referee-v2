"""Descriptive writing-quality metrics. Offline, deterministic, no model.

These are objective measurements of prose (sentence length, passive voice,
hedging, acronyms defined before use, signposting). They are NOT a verdict on
quality: good writing in physics (Einstein 1905) and in psychology (Gollwitzer
1999) differ, and a few exemplars cannot define a norm. The report therefore
shows the manuscript's numbers next to the profile of a small set of
high-quality exemplar papers (docs/evaluation/EXEMPLAR_WRITING_PROFILE.md) and
flags only things a careful editor would flag in any field: acronyms never
defined, very long sentences, and very heavy hedging.
"""
from __future__ import annotations

import re
import statistics
from typing import Any

_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(\[])")
_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
_HEDGES = ("may", "might", "could", "possibly", "perhaps", "appears", "appear", "seems", "seem", "suggests", "suggest",
           "likely", "potentially", "arguably", "tends", "tend", "somewhat", "relatively")
_PASSIVE = re.compile(r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?(?:\w+ed|shown|made|given|taken|seen|found|known|done|held|used|built|chosen)\b", re.I)
_ACRONYM = re.compile(r"\b[A-Z][A-Z0-9]{1,6}s?\b")
_COMMON = frozenset("""DNA RNA USA UK EU US AI ID OK PDF HTML URL API CPU GPU PC TV IQ GDP DOI ISBN ISSN FAQ ET AL
IEEE ACM PLOS NSF NIH WHO NASA MIT ICLR NIPS NEURIPS ICML ACL EMNLP arXiv LLM LLMS SOTA
I II III IV V VI VII VIII IX X XI XII""".split())
_SIGNPOST = re.compile(r"\b(we (?:show|propose|introduce|present|argue|find|report|demonstrate|test)|this (?:paper|article|study|survey|section)|"
                       r"in (?:this|the following) section|first,|second,|finally,|in summary|to summari[sz]e|in conclusion)\b", re.I)


def _clean(text: str) -> str:
    t = re.sub(r"-\n(?=[a-z])", "", text)                 # de-hyphenate line breaks
    t = re.sub(r"(?m)^\s*(?:--- Page \d+ ---|Authorized licensed use.*|\d{1,5})\s*$", " ", t)
    t = re.sub(r"\[\d+(?:[,–-]\s*\d+)*\]", " ", t)        # numeric citations
    return re.sub(r"[ \t]*\n[ \t]*", " ", t)


def _body(text: str) -> str:
    m = None
    for m in re.finditer(r"(?im)^\s*#*\s*(references|bibliography|literature cited)\s*$", text):
        pass
    return text[:m.start()] if m and m.start() > len(text) * 0.4 else text


def _drop_caps_lines(text: str) -> str:
    """Remove running headers, table captions and ALL-CAPS headings so they are not read as acronyms."""
    keep = []
    for line in text.splitlines():
        letters = [c for c in line if c.isalpha()]
        if len(letters) >= 6 and sum(c.isupper() for c in letters) / len(letters) > 0.6 and len(line.split()) >= 2:
            continue
        if re.search(r"(?i)authorized licensed use|downloaded on|restrictions apply|©|all rights reserved", line):
            continue
        keep.append(line)
    return "\n".join(keep)


def undefined_acronyms(text: str) -> list[str]:
    """Acronyms used 2+ times that are never expanded as 'Long form (ABC)' or 'ABC (long form)'.

    Skips: variable names with digits (A1, E2), ALL-CAPS headings (a lower-case word of the same
    spelling appears as ordinary text), and widely known abbreviations.
    """
    text = _drop_caps_lines(text)
    counts: dict[str, int] = {}
    for m in _ACRONYM.finditer(text):
        a = m.group(0)
        a = a[:-1] if a.endswith("s") and len(a) > 3 else a
        if a in _COMMON or any(ch.isdigit() for ch in a) or len(a) < 3:
            continue
        counts[a] = counts.get(a, 0) + 1
    out = []
    for a, n in counts.items():
        if n < 2:
            continue
        if len(re.findall(r"\b" + re.escape(a.lower()) + r"\b", text)) >= 2:  # lower-case form used as an ordinary word
            continue  # a heading in capitals, not an acronym
        defined = re.search(r"\b[A-Za-z][\w-]*(?:\s+[A-Za-z][\w-]*){0,6}\s*\(\s*" + re.escape(a) + r"s?\s*\)", text) or \
                  re.search(r"\b" + re.escape(a) + r"s?\s*\(\s*[A-Za-z][\w-]*(?:\s+[A-Za-z][\w-]*){1,7}\s*\)", text)
        if not defined:
            out.append(a)
    return sorted(out)


def profile(text: str) -> dict[str, Any]:
    body = _clean(_body(text))
    sentences = [s.strip() for s in _SENT.split(body) if len(_WORD.findall(s)) >= 4]
    lengths = [len(_WORD.findall(s)) for s in sentences]
    words = _WORD.findall(body)
    n = max(1, len(words))
    low = [w.lower() for w in words]
    hedge = sum(low.count(h) for h in _HEDGES)
    return {
        "words": len(words), "sentences": len(sentences),
        "sentence_words_median": statistics.median(lengths) if lengths else 0,
        "sentence_words_p90": sorted(lengths)[int(0.9 * (len(lengths) - 1))] if lengths else 0,
        "share_sentences_over_40_words": round(sum(1 for x in lengths if x > 40) / max(1, len(lengths)), 3),
        "passive_per_100_sentences": round(100 * len(_PASSIVE.findall(body)) / max(1, len(sentences)), 1),
        "hedges_per_1000_words": round(1000 * hedge / n, 1),
        "first_person_we_i_per_1000_words": round(1000 * (low.count("we") + low.count("i") + low.count("our")) / n, 1),
        "signposts_per_1000_words": round(1000 * len(_SIGNPOST.findall(body)) / n, 1),
        "undefined_acronyms": undefined_acronyms(_body(text)),
    }


def long_sentences(text: str, limit: int = 60, k: int = 5) -> list[dict[str, Any]]:
    body = _clean(_body(text))
    rows = [(len(_WORD.findall(s)), s.strip()) for s in _SENT.split(body)]
    rows = [r for r in rows if r[0] > limit]
    rows.sort(reverse=True)
    return [{"words": n, "sentence": s[:240] + ("..." if len(s) > 240 else "")} for n, s in rows[:k]]


def check_writing(text: str) -> dict[str, Any]:
    p = profile(text)
    flags = []
    if p["undefined_acronyms"]:
        flags.append({"check": "acronyms_not_defined", "items": p["undefined_acronyms"][:20],
                      "note": "Used more than once but never expanded in the text. Define each at first use."})
    ls = long_sentences(text)
    if ls:
        flags.append({"check": "very_long_sentences", "items": ls,
                      "note": "Sentences over 60 words are hard to follow. Consider splitting."})
    if p["hedges_per_1000_words"] > 25:
        flags.append({"check": "heavy_hedging", "value": p["hedges_per_1000_words"],
                      "note": "Hedging is very dense. Keep hedges where the evidence is genuinely uncertain and state firm results firmly."})
    return {"method": "descriptive prose metrics; offline", "profile": p, "flags": flags,
            "note": "Metrics describe the text; they are not a quality score. Compare with docs/evaluation/EXEMPLAR_WRITING_PROFILE.md."}
