"""Figure integrity check: duplicated images (no training, no API key).

Extracts embedded images from a PDF (PyMuPDF) and compares them with a
perceptual difference hash (dHash). Reports image pairs that look the same, or
the same after a flip or rotation, including quadrant-level matches (a panel
reused inside a larger figure). Low-detail regions (blank backgrounds,
plain axes) are skipped so uniform areas do not match each other.

This is classical image forensics, not a neural network. A CNN could make it
more robust to heavy editing, but it needs trained weights and has not been
validated here. Treat every finding as "a human should look at these two
images", never as proof of misconduct: legitimate reuse (a control shown twice,
a schematic repeated, compression) also matches.
Optional dependencies: pip install pymupdf pillow
"""
from __future__ import annotations

from itertools import combinations
from typing import Any

HASH = 16            # 16x16 dHash = 256 bits
MAX_DIST = 18        # <= ~7% differing bits counts as the same image
MIN_SIDE = 90        # ignore icons and tiny images
MIN_DETAIL = 14.0    # grayscale std-dev below this = blank or flat, skipped

_TRANSFORMS = ("same", "flipped horizontally", "flipped vertically", "rotated 180", "rotated 90", "rotated 270")


def _dhash(img) -> int:
    g = img.convert("L").resize((HASH + 1, HASH))
    px = list(g.getdata())
    bits = 0
    for y in range(HASH):
        row = px[y * (HASH + 1):(y + 1) * (HASH + 1)]
        for x in range(HASH):
            bits = (bits << 1) | (1 if row[x] > row[x + 1] else 0)
    return bits


def _std(img) -> float:
    g = img.convert("L").resize((32, 32))
    px = list(g.getdata())
    m = sum(px) / len(px)
    return (sum((p - m) ** 2 for p in px) / len(px)) ** 0.5


def _variants(img):
    from PIL import Image
    yield "same", img
    yield "flipped horizontally", img.transpose(Image.FLIP_LEFT_RIGHT)
    yield "flipped vertically", img.transpose(Image.FLIP_TOP_BOTTOM)
    yield "rotated 180", img.transpose(Image.ROTATE_180)
    yield "rotated 90", img.transpose(Image.ROTATE_90)
    yield "rotated 270", img.transpose(Image.ROTATE_270)


def _regions(img):
    w, h = img.size
    yield "whole", img
    if w >= 2 * MIN_SIDE and h >= 2 * MIN_SIDE:
        hw, hh = w // 2, h // 2
        for name, box in (("top-left", (0, 0, hw, hh)), ("top-right", (hw, 0, w, hh)),
                          ("bottom-left", (0, hh, hw, h)), ("bottom-right", (hw, hh, w, h))):
            yield name, img.crop(box)


def _popcount(x: int) -> int:
    return bin(x).count("1")


def extract_images(pdf_path: str) -> list[dict[str, Any]]:
    import fitz
    from PIL import Image
    import io
    out = []
    doc = fitz.open(pdf_path)
    for pno in range(len(doc)):
        for idx, info in enumerate(doc[pno].get_images(full=True)):
            try:
                pix = fitz.Pixmap(doc, info[0])
                if pix.n - pix.alpha >= 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
            except Exception:
                continue
            if min(img.size) >= MIN_SIDE:
                out.append({"page": pno + 1, "index": idx, "image": img})
    return out


def find_duplicate_images(images: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """images: [{page, index, image(PIL)}]. Returns suspicious pairs."""
    fingerprints = []
    for im in images:
        regs = {}
        for rname, region in _regions(im["image"]):
            if _std(region) >= MIN_DETAIL:
                regs[rname] = _dhash(region)
        fingerprints.append((im, regs))
    findings = []
    for (a, ra), (b, rb) in combinations(fingerprints, 2):
        if a["page"] == b["page"] and a["index"] == b["index"]:
            continue
        best = None
        for rn_b, img_b in _regions(b["image"]):
            if _std(img_b) < MIN_DETAIL:
                continue
            for tname, tv in _variants(img_b):
                hb = _dhash(tv)
                for rn_a, ha in ra.items():
                    # compare like with like: whole-vs-whole or the same quadrant name against any transformed region
                    d = _popcount(ha ^ hb)
                    if d <= MAX_DIST and (best is None or d < best[0]):
                        best = (d, rn_a, rn_b, tname)
        if best:
            d, rn_a, rn_b, tname = best
            high = tname != "same" or rn_a != rn_b   # flipped/rotated, or a panel re-used in a different position
            findings.append({
                "check": "duplicate_image", "priority": "high" if high else "low",
                "a": f"page {a['page']} image {a['index']}", "b": f"page {b['page']} image {b['index']}",
                "match": f"{rn_a} of A ~ {rn_b} of B ({tname})", "hash_distance_bits_of_256": d,
                "note": ("Same content found after a flip/rotation or in a different position. A human should compare the two images."
                         if high else
                         "Identical image or corner in the same position. Most often a repeated logo, icon, template or the same panel exported twice; check only if it should be unique data."),
            })
    findings.sort(key=lambda f: (f["priority"] != "high", f["hash_distance_bits_of_256"]))
    return findings


def cluster_repeats(findings: list[dict[str, Any]]) -> list[list[str]]:
    """Groups of 3+ images tied together by low-priority matches: almost always a logo, icon or template."""
    parent: dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for f in findings:
        if f["priority"] == "low":
            parent[find(f["a"])] = find(f["b"])
    groups: dict[str, set[str]] = {}
    for x in list(parent):
        groups.setdefault(find(x), set()).add(x)
    return [sorted(g) for g in groups.values() if len(g) >= 3]


def check_figures(pdf_path: str) -> dict[str, Any]:
    try:
        imgs = extract_images(pdf_path)
    except ImportError:
        return {"status": "unavailable", "note": "Install optional dependencies: pip install pymupdf pillow"}
    findings = find_duplicate_images(imgs)
    clusters = cluster_repeats(findings)
    in_cluster = {x for g in clusters for x in g}
    findings = [f for f in findings if not (f["priority"] == "low" and f["a"] in in_cluster and f["b"] in in_cluster)]
    return {"status": "ok", "images_examined": len(imgs), "findings": findings, "repeated_elements": clusters,
            "method": "perceptual hash (dHash), flips/rotations, quadrant regions; no model",
            "note": "Absence of findings does not mean the figures are clean: edited, rescaled or heavily re-compressed duplicates, and duplicates inside plots, can be missed."}
