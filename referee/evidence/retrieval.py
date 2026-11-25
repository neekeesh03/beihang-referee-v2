"""Dependency-free passage retrieval over the manuscript itself (paper RAG).

Why this exists: the independent verifier used to see only the first N
characters of the manuscript. A concern about Methods or a supplement could be
judged without the relevant text in view, which risks false rejections and
fabricated reasoning. This module splits every document into overlapping
passages, ranks them with BM25 and returns the passages most relevant to a
concern, each labelled with a stable id so the verifier can cite it.

No network, no embeddings, no API key: results are deterministic.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

_TOKEN = re.compile(r"[A-Za-z0-9_]+(?:[-.][A-Za-z0-9_]+)*")
_STOP = frozenset(
    "a an and are as at be been by for from has have in is it its of on or that the this to was were which with not no".split()
)


def _tokens(text: str) -> list[str]:
    return [t for t in (m.group(0).lower() for m in _TOKEN.finditer(text)) if t not in _STOP and len(t) > 1]


@dataclass(frozen=True)
class Passage:
    passage_id: str
    document_id: str
    start: int
    end: int
    text: str


def split_passages(document_id: str, text: str, size: int = 1200, overlap: int = 200) -> list[Passage]:
    """Split on paragraph boundaries where possible, falling back to fixed windows."""
    out: list[Passage] = []
    if not text:
        return out
    pos, n, idx = 0, len(text), 0
    while pos < n:
        end = min(pos + size, n)
        if end < n:
            cut = text.rfind("\n\n", pos + size // 2, end)
            if cut == -1:
                cut = text.rfind(". ", pos + size // 2, end)
            if cut != -1:
                end = cut + 1
        chunk = text[pos:end].strip()
        if chunk:
            out.append(Passage(f"{document_id}:P{idx:03d}", document_id, pos, end, chunk))
            idx += 1
        if end >= n:
            break
        pos = max(end - overlap, pos + 1)
    return out


class PassageIndex:
    def __init__(self, passages: Iterable[Passage], k1: float = 1.5, b: float = 0.75):
        self.passages = list(passages)
        self.k1, self.b = k1, b
        self._tf = [Counter(_tokens(p.text)) for p in self.passages]
        self._len = [sum(c.values()) for c in self._tf]
        self._avg = (sum(self._len) / len(self._len)) if self._len else 0.0
        df: Counter[str] = Counter()
        for c in self._tf:
            df.update(c.keys())
        n = len(self.passages)
        self._idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def search(self, query: str, k: int = 6) -> list[tuple[Passage, float]]:
        q = _tokens(query)
        if not q or not self.passages:
            return []
        scored: list[tuple[int, float]] = []
        for i, tf in enumerate(self._tf):
            score = 0.0
            for t in set(q):
                f = tf.get(t)
                if not f:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * self._len[i] / (self._avg or 1.0))
                score += self._idf.get(t, 0.0) * f * (self.k1 + 1) / denom
            if score > 0:
                scored.append((i, score))
        scored.sort(key=lambda x: (-x[1], x[0]))
        return [(self.passages[i], s) for i, s in scored[:k]]


def build_index(documents: Iterable[dict[str, Any]]) -> PassageIndex:
    passages: list[Passage] = []
    for d in documents:
        passages.extend(split_passages(str(d.get("document_id") or "doc"), d.get("text") or ""))
    return PassageIndex(passages)


def context_for_concern(index: PassageIndex, concern_text: str, anchor_quotes: Iterable[str] = (),
                        k: int = 6, max_chars: int = 9000) -> str:
    """Render the best passages for one concern as labelled, citable text.

    Anchor quotes are added to the query so the passage the concern points at
    is always retrieved, plus its neighbours through the overlap.
    """
    query = concern_text + " " + " ".join(anchor_quotes)
    hits = index.search(query, k=k)
    hits.sort(key=lambda h: (h[0].document_id, h[0].start))  # reading order
    parts, used = [], 0
    for p, score in hits:
        block = f"[{p.passage_id} chars {p.start}-{p.end} score {score:.2f}]\n{p.text}"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts) if parts else "(no relevant passage found in the supplied material)"
