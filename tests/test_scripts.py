#!/usr/bin/env python3
"""End-to-end-ish tests for the academic-slides scripts.

Runs without LaTeX/poppler by synthesizing a slide PDF with reportlab and
assets with Pillow, then exercising every script's core logic. Run:

    python tests/test_scripts.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_overflow  # noqa: E402
import render_pages  # noqa: E402
import contact_sheet  # noqa: E402
import normalize_assets  # noqa: E402
import build  # noqa: E402
import new_talk  # noqa: E402

PAGE_W, PAGE_H = 720.0, 405.0  # 16:9-ish, in points


def make_slide_pdf(path: Path, n_clean: int = 3) -> None:
    """Synthesize a deck: n_clean good pages, 1 footer-collision, 1 off-canvas."""
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H))

    def footer(pageno: int):
        c.setFont("Helvetica", 8)
        c.drawString(345, 10, str(pageno))  # recurring page number (same position)

    page = 0
    for _ in range(n_clean):
        page += 1
        c.setFont("Helvetica", 14)
        c.drawString(60, 360, f"Clean slide {page} — a normal title")
        c.setFont("Helvetica", 11)
        c.drawString(60, 320, "Body text sitting comfortably in the upper area.")
        footer(page)
        c.showPage()

    # footer-collision page: body text pushed down into the footer band.
    page += 1
    c.setFont("Helvetica", 14)
    c.drawString(60, 360, "Overstuffed slide")
    c.setFont("Helvetica", 11)
    c.drawString(60, 18, "This line has slid down and collides with the footer rail.")
    footer(page)
    c.showPage()

    # off-canvas page: text runs past the right edge.
    page += 1
    c.setFont("Helvetica", 14)
    c.drawString(60, 360, "Runaway line")
    c.setFont("Helvetica", 11)
    c.drawString(690, 300, "THIS_WORD_RUNS_OFF_THE_RIGHT_EDGE")
    footer(page)
    c.showPage()

    c.save()


class TestCheckOverflow(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pdf = self.tmp / "deck.pdf"
        make_slide_pdf(self.pdf)

    def test_detects_footer_and_flags_bad_pages(self):
        pages, footer_top, safe_zone_top, issues = check_overflow.analyze(str(self.pdf))
        self.assertEqual(len(pages), 5)
        # A recurring footer must be detected.
        self.assertIsNotNone(footer_top, "footer baseline should be detected")
        # Pages 4 (collision) and 5 (off-canvas) must be flagged as errors.
        error_pages = {i.page for i in issues if i.severity == "error"}
        self.assertIn(4, error_pages, f"expected collision on p4; issues={issues}")
        self.assertIn(5, error_pages, f"expected off-canvas on p5; issues={issues}")
        # Pages 1-3 must be clean.
        flagged = {i.page for i in issues}
        self.assertFalse({1, 2, 3} & flagged, f"pages 1-3 should be clean; flagged={flagged}")

    def test_kinds(self):
        _, _, _, issues = check_overflow.analyze(str(self.pdf))
        kinds = {i.page: i.kind for i in issues if i.severity == "error"}
        self.assertEqual(kinds.get(4), "footer_collision")
        self.assertEqual(kinds.get(5), "off_canvas_right")

    def test_json_and_text_reports(self):
        pages, ft, sz, issues = check_overflow.analyze(str(self.pdf))
        txt = check_overflow.text_report(str(self.pdf), pages, ft, sz, issues)
        js = check_overflow.json_report(str(self.pdf), pages, ft, sz, issues)
        self.assertIn("check_overflow", txt)
        import json
        self.assertEqual(json.loads(js)["pages_total"], 5)

    def test_cli_exit_code(self):
        rc = check_overflow.main([str(self.pdf)])
        self.assertEqual(rc, 1)  # errors present -> non-zero


class TestRenderAndContactSheet(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pdf = self.tmp / "deck.pdf"
        make_slide_pdf(self.pdf)

    def test_render_pages(self):
        pages = render_pages.render(self.pdf, self.tmp / "pages", dpi=90)
        self.assertEqual(len(pages), 5)
        for p in pages:
            self.assertTrue(p.exists() and p.stat().st_size > 0)

    def test_contact_sheet(self):
        render_pages.render(self.pdf, self.tmp / "pages", dpi=90)
        page_paths = contact_sheet.collect_pages(self.tmp / "pages")
        self.assertEqual(len(page_paths), 5)
        out = contact_sheet.build_sheet(page_paths, self.tmp / "sheet.png",
                                        cols=3, thumb_w=240, label=True)
        self.assertTrue(out.exists() and out.stat().st_size > 0)

    def test_contact_sheet_page_order(self):
        # Ensure natural sort (page-2 before page-10).
        d = self.tmp / "ord"
        d.mkdir()
        for n in (1, 2, 10, 3):
            (d / f"page-{n:02d}.png").write_bytes(b"")
        names = [p.name for p in contact_sheet.collect_pages(d)]
        self.assertEqual(names, ["page-01.png", "page-02.png", "page-03.png", "page-10.png"])


class TestNormalizeAssets(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.assets = self.tmp / "assets"
        self.assets.mkdir()

    def test_low_res_flag(self):
        from PIL import Image
        Image.new("RGB", (120, 90), (200, 50, 50)).save(self.assets / "tiny.png")
        Image.new("RGB", (1600, 1000), (50, 50, 200)).save(self.assets / "big.png")
        report = normalize_assets.normalize(self.assets, min_px=900)
        by = {e["file"]: e for e in report["entries"]}
        self.assertTrue(any("low-res" in f for f in by["tiny.png"]["flags"]))
        self.assertEqual(by["big.png"]["flags"], [])

    def test_svg_to_pdf(self):
        svg = ('<?xml version="1.0"?>'
               '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
               '<rect x="10" y="10" width="180" height="100" fill="#1a3a5c"/></svg>')
        (self.assets / "diagram.svg").write_text(svg, encoding="utf-8")
        report = normalize_assets.normalize(self.assets, min_px=900)
        entry = next(e for e in report["entries"] if e["file"] == "diagram.svg")
        # Either converted (preferred) or clearly flagged if no backend.
        if entry["normalized"]:
            self.assertTrue((self.assets / "_normalized" / "diagram.pdf").exists())
        else:
            self.assertTrue(entry["flags"], "svg conversion failed but no flag set")

    def test_report_written(self):
        from PIL import Image
        Image.new("RGB", (1000, 800)).save(self.assets / "ok.png")
        normalize_assets.normalize(self.assets, min_px=900)
        self.assertTrue((self.assets / "_normalized" / "report.md").exists())


class TestBuild(unittest.TestCase):
    def test_parse_log(self):
        tmp = Path(tempfile.mkdtemp())
        log = tmp / "slides.log"
        log.write_text(
            "! Undefined control sequence.\n"
            "Overfull \\hbox (12.3pt too wide) in paragraph at lines 4--5\n"
            "LaTeX Warning: File `missing.png' not found.\n"
            "LaTeX Warning: Reference `fig:x' on page 3 undefined on input line 9.\n",
            encoding="utf-8")
        parsed = build.parse_log(log)
        self.assertTrue(any("Undefined control sequence" in e for e in parsed["errors"]))
        self.assertEqual(len(parsed["overfull"]), 1)
        self.assertIn("missing.png", parsed["missing_files"])
        self.assertTrue(parsed["undefined_refs"])

    def test_engine_selection_or_graceful_message(self):
        engine = build.pick_engine("auto")
        # On a machine without LaTeX this is None; main must exit 2 with guidance.
        if engine is None:
            tmp = Path(tempfile.mkdtemp())
            tex = tmp / "slides.tex"
            tex.write_text("\\documentclass{beamer}\\begin{document}\\end{document}", encoding="utf-8")
            rc = build.main([str(tex)])
            self.assertEqual(rc, 2)


class TestNewTalk(unittest.TestCase):
    def test_scaffold(self):
        tmp = Path(tempfile.mkdtemp())
        target = tmp / "my-talk"
        created = new_talk.scaffold(target, title="A Minimal Feedback Model", author="Jane Roe", force=False)
        for f in ("brief.md", "outline.md", "slide-map.md", "slides.tex",
                  "beamerthemeAcademicTalk.sty", "references.bib"):
            self.assertTrue((target / f).exists(), f"missing {f}")
        for d in ("assets", "assets/_normalized", "build"):
            self.assertTrue((target / d).is_dir(), f"missing dir {d}")
        deck = (target / "slides.tex").read_text(encoding="utf-8")
        self.assertIn("A Minimal Feedback Model", deck)
        self.assertIn("Jane Roe", deck)
        self.assertIn("slides.tex", created)


if __name__ == "__main__":
    unittest.main(verbosity=2)
