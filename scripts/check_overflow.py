#!/usr/bin/env python3
"""Detect text that collides with the footer band or runs off the page.

Word-level layout check on a rendered slide PDF. Complements LaTeX's own
`Overfull \\hbox` warnings: those catch line-level typesetting overruns, this
catches frame contents that exceed the canvas vertically (colliding with the
footer / page-number rail) or spill off any edge.

Backends (auto): PyMuPDF (pure Python) preferred, else `pdftotext -bbox-layout`
(poppler). Both use a top-left origin in PDF points.

Adapted from dro42/presentation-kit `slide-overflow-check`, extended with a
PyMuPDF backend so it runs without poppler.

Usage:
    python check_overflow.py <slides.pdf> [--json] [--footer-clearance 20]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict

try:
    from _common import which, have_module
except ImportError:  # pragma: no cover
    from scripts._common import which, have_module  # type: ignore


# --- data model ---------------------------------------------------------------

@dataclass(frozen=True)
class Word:
    page: int
    text: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float


@dataclass
class Page:
    number: int
    width: float
    height: float
    words: list = field(default_factory=list)


@dataclass
class Issue:
    page: int
    severity: str   # "error" | "warn"
    kind: str
    text: str
    bbox: dict
    page_size: dict
    threshold_used: float | None


# --- extraction backends ------------------------------------------------------

def extract_pages_pymupdf(pdf_path: str) -> list[Page]:
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    pages: list[Page] = []
    for i, page in enumerate(doc, start=1):
        rect = page.rect
        pg = Page(number=i, width=float(rect.width), height=float(rect.height))
        for w in page.get_text("words"):
            x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4]
            if not str(text).strip():
                continue
            pg.words.append(Word(i, str(text).strip(), float(x0), float(y0), float(x1), float(y1)))
        pages.append(pg)
    doc.close()
    return pages


NS_STRIP = re.compile(rb' xmlns(:\w+)?="[^"]+"')


def extract_pages_pdftotext(pdf_path: str) -> list[Page]:
    import subprocess
    from xml.etree import ElementTree as ET

    proc = subprocess.run(["pdftotext", "-bbox-layout", pdf_path, "-"],
                          capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"pdftotext failed: {proc.stderr.decode(errors='replace')}")
    root = ET.fromstring(NS_STRIP.sub(b"", proc.stdout))
    pages: list[Page] = []
    for i, page_el in enumerate(root.iter("page"), start=1):
        pg = Page(number=i, width=float(page_el.attrib["width"]),
                  height=float(page_el.attrib["height"]))
        for w in page_el.iter("word"):
            pg.words.append(Word(i, (w.text or "").strip(),
                                 float(w.attrib["xMin"]), float(w.attrib["yMin"]),
                                 float(w.attrib["xMax"]), float(w.attrib["yMax"])))
        pages.append(pg)
    return pages


def extract_pages(pdf_path: str, backend: str = "auto") -> list[Page]:
    if backend in ("auto", "pymupdf") and have_module("fitz"):
        return extract_pages_pymupdf(pdf_path)
    if backend in ("auto", "pdftotext") and which("pdftotext"):
        return extract_pages_pdftotext(pdf_path)
    raise RuntimeError("no extraction backend: install PyMuPDF (pip install pymupdf) or poppler (pdftotext).")


# --- footer detection ---------------------------------------------------------

def detect_footer(pages: list[Page], footer_band_pct: float, coverage_pct: float):
    """Return (footer_words:set, footer_text_top:float|None)."""
    BUCKET = 10.0
    bottom_by_page: dict[int, list] = defaultdict(list)
    body_pos_by_page: dict[int, set] = defaultdict(set)

    for p in pages:
        band_top = p.height * (1 - footer_band_pct)
        for w in p.words:
            key = (round(w.x_min / BUCKET), round(w.y_min / BUCKET))
            if w.y_min >= band_top:
                bottom_by_page[p.number].append(w)
            else:
                body_pos_by_page[p.number].add(key)

    paginated = [p for p in pages if bottom_by_page[p.number]]
    if not paginated:
        return set(), None

    cluster_pages: dict[tuple, set] = defaultdict(set)
    cluster_words: dict[tuple, list] = defaultdict(list)
    for page_num, words in bottom_by_page.items():
        for w in words:
            key = (round(w.x_min / BUCKET), round(w.y_min / BUCKET))
            cluster_pages[key].add(page_num)
            cluster_words[key].append(w)

    threshold = max(2, int(len(paginated) * coverage_pct))
    footer_keys = set()
    for key, page_set in cluster_pages.items():
        if len(page_set) < threshold:
            continue
        if any(key in body_pos_by_page[p.number] for p in pages):
            continue
        footer_keys.add(key)

    if not footer_keys:
        return set(), None

    footer_words = {w for key in footer_keys for w in cluster_words[key]}
    canonical = max(footer_keys, key=lambda k: (len(cluster_pages[k]), -k[1]))
    footer_text_top = min(w.y_min for w in cluster_words[canonical])
    return footer_words, footer_text_top


# --- issue finding ------------------------------------------------------------

def _mk(p: Page, w: Word, sev: str, kind: str, threshold: float) -> Issue:
    return Issue(p.number, sev, kind, w.text,
                 {"xMin": w.x_min, "yMin": w.y_min, "xMax": w.x_max, "yMax": w.y_max},
                 {"width": p.width, "height": p.height}, threshold)


def find_issues(pages, footer_words, safe_zone_top, hard_boundary_pct, epsilon) -> list[Issue]:
    issues: list[Issue] = []
    for p in pages:
        if not p.words:
            issues.append(Issue(p.number, "warn", "not_analyzable", "<no text>", {},
                                {"width": p.width, "height": p.height}, None))
            continue
        if safe_zone_top is not None:
            v_limit, v_kind, near_limit = safe_zone_top, "footer_collision", None
        else:
            v_limit, v_kind, near_limit = p.height * hard_boundary_pct, "page_bottom", p.height * 0.95

        for w in p.words:
            if w in footer_words:
                continue
            if w.x_max > p.width + epsilon:
                issues.append(_mk(p, w, "error", "off_canvas_right", p.width)); continue
            if w.x_min < -epsilon:
                issues.append(_mk(p, w, "error", "off_canvas_left", 0.0)); continue
            if w.y_min < -epsilon:
                issues.append(_mk(p, w, "error", "off_canvas_top", 0.0)); continue
            if w.y_max > p.height + epsilon:
                issues.append(_mk(p, w, "error", "off_canvas_bottom", p.height)); continue
            if w.y_max > v_limit + epsilon:
                issues.append(_mk(p, w, "error", v_kind, v_limit)); continue
            if near_limit is not None and w.y_max > near_limit + epsilon:
                issues.append(_mk(p, w, "warn", "near_page_edge", near_limit))
    return issues


def merge_adjacent(issues: list[Issue]) -> list[Issue]:
    merged: list[Issue] = []
    by_key: dict[tuple, list] = defaultdict(list)
    for it in issues:
        by_key[(it.page, it.severity, it.kind)].append(it)
    for (page, sev, kind), group in sorted(by_key.items()):
        if kind == "not_analyzable":
            merged.append(group[0]); continue
        group.sort(key=lambda i: (i.bbox.get("yMin", 0), i.bbox.get("xMin", 0)))
        text = " ".join(i.text for i in group if i.text).strip()
        bbox = {"xMin": min(i.bbox["xMin"] for i in group),
                "yMin": min(i.bbox["yMin"] for i in group),
                "xMax": max(i.bbox["xMax"] for i in group),
                "yMax": max(i.bbox["yMax"] for i in group)}
        merged.append(Issue(page, sev, kind, text, bbox, group[0].page_size, group[0].threshold_used))
    return merged


def analyze(pdf_path: str, backend="auto", footer_band_pct=0.15, footer_coverage_pct=0.6,
            footer_clearance=20.0, hard_boundary_pct=0.97, epsilon=0.5):
    pages = extract_pages(pdf_path, backend)
    if not pages:
        raise RuntimeError("0 pages extracted")
    footer_words, footer_text_top = detect_footer(pages, footer_band_pct, footer_coverage_pct)
    safe_zone_top = (footer_text_top - footer_clearance) if footer_text_top is not None else None
    issues = merge_adjacent(find_issues(pages, footer_words, safe_zone_top, hard_boundary_pct, epsilon))
    return pages, footer_text_top, safe_zone_top, issues


# --- reporting ----------------------------------------------------------------

def text_report(pdf_path, pages, footer_text_top, safe_zone_top, issues, quiet=False) -> str:
    lines = [f"check_overflow: {pdf_path} - {len(pages)} pages, {len(issues)} issues"]
    if footer_text_top is not None:
        lines.append(f"  footer top y={footer_text_top:.0f} / safe_zone_top y={safe_zone_top:.0f}")
    else:
        lines.append("  no recurring footer detected - using hard-boundary fallback")
    lines.append("")
    issue_pages = {i.page for i in issues}
    for it in issues:
        ph = it.page_size.get("height", 0)
        if it.kind == "not_analyzable":
            lines.append(f"  Page {it.page} - warn - not analyzable (image-only page)")
        else:
            lines.append(f"  Page {it.page} - {it.severity} - {it.kind.replace('_',' ')}:")
            lines.append(f'    "{it.text}" at yMax={it.bbox.get("yMax",0):.0f}/{ph:.0f}'
                         f' (threshold {it.threshold_used:.0f})')
        lines.append("")
    if not quiet:
        clean = sorted(p.number for p in pages if p.number not in issue_pages)
        if clean:
            lines.append(f"  clean: {', '.join(map(str, clean))}")
    return "\n".join(lines).rstrip() + "\n"


def json_report(pdf_path, pages, footer_text_top, safe_zone_top, issues) -> str:
    return json.dumps({
        "pdf_path": pdf_path,
        "pages_total": len(pages),
        "pages_with_issues": len({i.page for i in issues}),
        "footer_baseline": footer_text_top,
        "safe_zone_top": safe_zone_top,
        "issues": [asdict(i) for i in issues],
    }, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Detect overflow / footer collisions in a slide PDF.")
    ap.add_argument("pdf_path")
    ap.add_argument("--backend", default="auto", choices=["auto", "pymupdf", "pdftotext"])
    ap.add_argument("--footer-band-pct", type=float, default=0.15)
    ap.add_argument("--footer-coverage-pct", type=float, default=0.6)
    ap.add_argument("--footer-clearance", type=float, default=20.0)
    ap.add_argument("--hard-boundary-pct", type=float, default=0.97)
    ap.add_argument("--epsilon", type=float, default=0.5)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-fail-on-warn", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    try:
        pages, footer_top, safe_zone_top, issues = analyze(
            args.pdf_path, args.backend, args.footer_band_pct, args.footer_coverage_pct,
            args.footer_clearance, args.hard_boundary_pct, args.epsilon)
    except (RuntimeError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.json:
        sys.stdout.write(json_report(args.pdf_path, pages, footer_top, safe_zone_top, issues))
    else:
        sys.stdout.write(text_report(args.pdf_path, pages, footer_top, safe_zone_top, issues, args.quiet))

    has_error = any(i.severity == "error" for i in issues)
    has_warn = any(i.severity == "warn" for i in issues)
    if has_error:
        return 1
    if has_warn and not args.no_fail_on_warn:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
