import io
import random

import pytest

pymupdf = pytest.importorskip("pymupdf")
Image = pytest.importorskip("PIL.Image")
from PIL import ImageDraw  # noqa: E402

from referee.verification.figures import check_figures  # noqa: E402


def shapes(seed, w=240, h=240):
    r = random.Random(seed)
    im = Image.new("RGB", (w, h), (r.randint(60, 200),) * 3)
    d = ImageDraw.Draw(im)
    for _ in range(25):
        x0, y0 = r.randint(0, w - 30), r.randint(0, h - 30)
        c = tuple(r.randint(0, 255) for _ in range(3))
        (d.ellipse if r.random() < .5 else d.rectangle)([x0, y0, x0 + r.randint(15, 90), y0 + r.randint(15, 90)], fill=c)
    return im


def make_pdf(path, images):
    doc = pymupdf.open()
    for img in images:
        pg = doc.new_page()
        buf = io.BytesIO(); img.save(buf, "PNG")
        pg.insert_image(pymupdf.Rect(50, 50, 350, 350), stream=buf.getvalue())
    doc.save(str(path))


def test_flipped_duplicate_and_reused_quadrant_found_and_unrelated_images_not(tmp_path):
    A, B, C = shapes(1), shapes(2), shapes(3)
    big = Image.new("RGB", (480, 480)); big.paste(shapes(9), (0, 0)); big.paste(A, (240, 240))
    big.paste(shapes(8), (240, 0)); big.paste(shapes(7), (0, 240))
    blank = Image.new("RGB", (240, 240), (255, 255, 255))
    make_pdf(tmp_path / "f.pdf", [A, B, A.transpose(Image.FLIP_LEFT_RIGHT), big, blank, blank, C])
    r = check_figures(str(tmp_path / "f.pdf"))
    pairs = {(f["a"], f["b"]) for f in r["findings"]}
    assert ("page 1 image 0", "page 3 image 0") in pairs      # flipped copy
    assert ("page 1 image 0", "page 4 image 0") in pairs      # reused as a quadrant
    assert all(f["priority"] == "high" for f in r["findings"])
    assert not any("page 2" in a or "page 2" in b or "page 7" in a or "page 7" in b or "page 5" in a or "page 6" in b for a, b in pairs)  # unrelated + blank ones untouched


def test_no_duplicates_no_findings(tmp_path):
    make_pdf(tmp_path / "g.pdf", [shapes(1), shapes(2), shapes(3)])
    assert check_figures(str(tmp_path / "g.pdf"))["findings"] == []


def test_logo_repeated_on_many_pages_is_grouped_not_listed_as_pairs(tmp_path):
    logo = shapes(5)
    make_pdf(tmp_path / "h.pdf", [logo, shapes(2), logo, shapes(3), logo, logo])
    r = check_figures(str(tmp_path / "h.pdf"))
    assert r["repeated_elements"] and len(r["repeated_elements"][0]) == 4
    assert r["findings"] == []
