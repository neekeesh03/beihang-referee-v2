"""Response-to-reviewers support, built on Noble (2017), "Ten simple rules for
writing a response to reviewers", PLOS Computational Biology 13(10): e1005730.

Two deterministic tools, no model and no API key:
- response_skeleton(): turns a set of reviewer comments into an interleaved
  response template (rules 1, 4, 5, 6, 7, 9).
- audit_response(): checks a finished response letter against what a script can
  check of those rules and reports exactly which comments look unanswered.

Rules 2 (tone) and 10 (write it twice) are partly or wholly human judgement; the
audit only flags obviously dismissive phrases and says so.
"""
from __future__ import annotations

import re
from typing import Any

_ITEM = re.compile(r"(?m)^\s*(?:\(?(?:reviewer|referee)\s*#?\d+\)?[:.]?\s*)?(?:comment|point|concern|major|minor|issue)?\s*#?(\d{1,2})[\).:]\s+(\S.*)$", re.I)
_RESPONSE_LABEL = re.compile(r"(?im)^\s*(?:\*\*)?(?:author(?:s')?\s+)?(?:response|reply|answer)\b[^\n]{0,20}[:.\-—]", re.I)
_DIRECT = re.compile(r"^\s*(?:\*\*)?(?:response|reply|answer)?[:.\-—\s*]*(yes|no|we agree|we thank|thank you|agreed|we have|we added|we revised|we clarified|we now|we did|we ran|we performed|we included|we removed|we corrected|we changed|we rewrote|we expanded|we disagree|we respectfully disagree|we partly|partly|in part|this is correct|you are correct|the reviewer is correct)\b", re.I)
_VAGUE_POINTER = re.compile(r"(?i)\b(this point is (?:already )?addressed in the manuscript|as (?:already )?(?:stated|described|discussed|mentioned|shown) in the (?:manuscript|paper|text)|please (?:see|refer to) (?:the )?(?:manuscript|section|supplement)|already (?:discussed|covered|addressed) in)\b")
_CHANGE_WORDS = re.compile(r"(?i)\b(added|revised|changed|modified|rewrote|new (?:text|section|paragraph|figure|table|analysis)|now (?:reads|states|says|includes)|removed|replaced|updated|expanded|inserted)\b")
_HOSTILE = re.compile(r"(?i)\b(the reviewer (?:clearly |obviously |simply )?(?:did not|didn't|failed to|does not understand|misunderstood|missed|has not read)|obviously|ridiculous|absurd|nonsense|trivial and|irrelevant|as we (?:already )?(?:said|told|explained) (?:before|already)|should have read|baseless|unfair)\b")
_OUT_OF_SCOPE = re.compile(r"(?i)\b(beyond the scope|outside the scope|out of scope|not within the scope|future work|we leave this for)\b")
_QUOTED_CHANGE = re.compile(r"(?m)^\s*(?:>|\"|“|revised text|new text|modified text|\[revised)", re.I)
_LINE_REF = re.compile(r"(?i)\b(?:lines?|pages?|p\.|section|§)\s*\d+")
_VERSION_REF = re.compile(r"(?i)\b(original|previous|first|revised|new|updated) (?:version|manuscript|submission)\b")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def split_comments(reviews_text: str) -> list[dict[str, Any]]:
    """Split reviewer text into numbered comments. Falls back to blank-line paragraphs."""
    ms = list(_ITEM.finditer(reviews_text))
    comments = []
    if len(ms) >= 2:
        for i, m in enumerate(ms):
            end = ms[i + 1].start() if i + 1 < len(ms) else len(reviews_text)
            raw = reviews_text[m.start():end].strip()
            raw = re.sub(r"(?im)^\s*(?:reviewer|referee)\s*#?\d+\s*\n+", "", raw)  # drop a leading 'Reviewer 1' heading
            comments.append({"id": len(comments) + 1, "text": raw})
    else:
        for p in re.split(r"\n\s*\n", reviews_text):
            if len(p.split()) >= 8:
                comments.append({"id": len(comments) + 1, "text": p.strip()})
    return comments


def response_skeleton(reviews_text: str, title: str = "the manuscript") -> str:
    comments = split_comments(reviews_text)
    out = [f"# Response to reviewers: {title}", "",
           "## Overview of changes", "",
           "_Write this last. Summarise the new data and analyses made in response to the most essential criticisms. "
           "Say which criticisms several reviewers raised. Mention figures or tables that are for the reviewers only._", "",
           "**Conventions.** Reviewer comments are in plain text; our responses begin with **Response:**; text changed in the manuscript is quoted "
           "in blockquotes. Line numbers refer to the REVISED manuscript unless marked (original).", "", "---", ""]
    for c in comments:
        out += [f"### Comment {c['id']}", "", c["text"], "",
                "**Response:** _Start with a direct answer: Yes / No / Partly / We agree / We disagree because... If the reviewer is right, say so. "
                "If the point shows the text was unclear, accept the blame and revise._", "",
                "**What changed:** _Say explicitly whether this is NEW in the revised version or already in the original (never 'this is addressed in the manuscript'). "
                "Quote the new or changed text below, with line numbers (revised)._", "",
                "> _Quoted revised text here_", "", "---", ""]
    out += ["## Optional separate letter to the editor", "",
            "_Conflicts of interest, reviewer requests that conflict with each other or with journal policy, and any concern you do not want in the response to reviewers._", ""]
    return "\n".join(out)


def audit_response(response_text: str, reviews_text: str | None = None) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    low = response_text.lower()
    n = len(response_text.split())

    def add(rule: int, status: str, note: str, **extra):
        findings.append({"rule": rule, "status": status, "note": note, **extra})

    head = low[: max(600, int(len(low) * 0.15))]
    if re.search(r"overview|summary of (?:the )?changes|summary of (?:major )?revisions|main changes|we thank", head):
        add(1, "pass", "An overview or summary appears at the start.")
    else:
        add(1, "warn", "No overview of changes at the start. Lead with a short summary of new data and analyses.")

    comments = split_comments(reviews_text) if reviews_text else []
    quoted_frac = None
    if comments:
        norm_resp = _norm(response_text)
        hit = 0
        for c in comments:
            sentences = [s for s in re.split(r"(?<=[.!?])\s+", c["text"]) if len(s.split()) >= 8]
            if sentences and any(_norm(s)[:80] in norm_resp for s in sentences):
                hit += 1
        quoted_frac = hit / len(comments)
        add(1, "pass" if quoted_frac >= 0.8 else "warn",
            f"{hit} of {len(comments)} reviewer comments are quoted in the letter." + ("" if quoted_frac >= 0.8 else " Quote the full set of reviews with responses interleaved."))

    hostile = [m.group(0) for m in _HOSTILE.finditer(response_text)]
    add(2, "warn" if hostile else "pass",
        "Dismissive or blaming wording found. Rephrase so any misunderstanding is yours to clarify." if hostile
        else "No obviously dismissive phrases (tone is still for a human to judge).", examples=hostile[:5])

    labels = _RESPONSE_LABEL.findall(response_text)
    blocks = re.split(r"(?im)^\s*(?:\*\*)?(?:author(?:s')?\s+)?(?:response|reply|answer)\b[^\n]{0,20}[:.\-—]\s*", response_text)[1:]
    if comments:
        if len(blocks) < len(comments):
            add(5, "warn", f"{len(comments)} reviewer comments but only {len(blocks)} labelled responses. Some points may be unanswered.",
                missing_estimate=len(comments) - len(blocks))
        else:
            add(5, "pass", f"{len(blocks)} labelled responses for {len(comments)} comments.")
    elif not labels:
        add(6, "warn", "No 'Response:' labels found. Use labels and typography to separate review, response and manuscript changes.")
    if labels:
        add(6, "pass", "Responses are labelled.")

    direct = [bool(_DIRECT.match(b.strip())) for b in blocks]
    if blocks:
        frac = sum(direct) / len(blocks)
        bad = [i + 1 for i, d in enumerate(direct) if not d][:10]
        add(7, "pass" if frac >= 0.8 else "warn",
            f"{sum(direct)} of {len(blocks)} responses start with a direct answer." + ("" if frac >= 0.8 else " Begin each with yes/no/we agree/we have..., then give background."),
            responses_without_direct_answer=bad)

    vague = []
    for i, b in enumerate(blocks, 1):
        if _VAGUE_POINTER.search(b) and not _CHANGE_WORDS.search(b):
            vague.append(i)
    add(9, "warn" if vague else "pass",
        "Some responses only point to the manuscript without saying what changed." if vague else "No bare 'this is addressed in the manuscript' replies.",
        responses=vague[:15])
    if blocks:
        quoted = sum(1 for b in blocks if _QUOTED_CHANGE.search(b) or _LINE_REF.search(b))
        add(4, "pass" if quoted / len(blocks) >= 0.6 else "warn",
            f"{quoted} of {len(blocks)} responses quote changed text or give line/section references." + ("" if quoted / len(blocks) >= 0.6 else " Quote the change so the response is self-contained."))
    add(9, "pass" if _VERSION_REF.search(response_text) or re.search(r"(?i)\(original\)|\(revised\)|revised manuscript", response_text) else "info",
        "Says which version line numbers refer to." if _VERSION_REF.search(response_text) or re.search(r"(?i)\(original\)|\(revised\)|revised manuscript", response_text)
        else "State whether line numbers refer to the original or the revised manuscript.")

    oos = [i for i, b in enumerate(blocks, 1) if _OUT_OF_SCOPE.search(b)]
    if blocks:
        share = len(oos) / len(blocks)
        add(8, "warn" if share > 0.3 else "pass",
            f"{len(oos)} of {len(blocks)} responses decline as out of scope." + (" If most requests are out of scope the reviewers are unlikely to be satisfied; do some of them, or defer to the editor." if share > 0.3 else ""),
            responses=oos[:15])
    warn = sum(1 for f in findings if f["status"] == "warn")
    return {"method": "Noble (2017) ten simple rules; deterministic checks only", "words": n, "comments_found": len(comments),
            "responses_found": len(blocks), "findings": findings, "warnings": warn,
            "note": "Rules 2 (tone) and 10 (write it twice) need human judgement. A passing audit does not mean the response is persuasive."}
