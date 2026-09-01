#!/usr/bin/env python3
"""Render every page of a slide PDF to a PNG (for the visual-audit loop).

Prefers PyMuPDF (pure Python, no system deps); falls back to `pdftoppm`.

Usage:
    python render_pages.py <slides.pdf> [--outdir build/pages] [--dpi 110]

Writes page-01.png, page-02.png, ... and prints the count.
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from _common import which, run, have_module, eprint
except ImportError:  # pragma: no cover
    from scripts._common import which, run, have_module, eprint  # type: ignore


def render_with_pymupdf(pdf: Path, outdir: Path, dpi: int) -> list[Path]:
    import fitz  # PyMuPDF

    doc = fitz.open(str(pdf))
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pages: list[Path] = []
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=mat)
        dst = outdir / f"page-{i:02d}.png"
        pix.save(str(dst))
        pages.append(dst)
    doc.close()
    return pages


def render_with_pdftoppm(pdf: Path, outdir: Path, dpi: int) -> list[Path]:
    prefix = outdir / "page"
    proc = run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(prefix)])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    # pdftoppm names files page-1.png, page-01.png depending on count; normalize.
    pages = sorted(outdir.glob("page*.png"))
    return pages


def render(pdf: Path, outdir: Path, dpi: int) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    if have_module("fitz"):
        return render_with_pymupdf(pdf, outdir, dpi)
    if which("pdftoppm"):
        return render_with_pdftoppm(pdf, outdir, dpi)
    raise RuntimeError(
        "no PDF renderer available: install PyMuPDF (pip install pymupdf) "
        "or poppler (pdftoppm)."
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render slide PDF pages to PNGs.")
    ap.add_argument("pdf", help="Path to the slide PDF.")
    ap.add_argument("--outdir", default=None, help="Default: <pdf-dir>/pages")
    ap.add_argument("--dpi", type=int, default=110)
    args = ap.parse_args(argv)

    pdf = Path(args.pdf).resolve()
    if not pdf.is_file():
        eprint(f"error: not found: {pdf}")
        return 1
    outdir = Path(args.outdir).resolve() if args.outdir else pdf.parent / "pages"

    try:
        pages = render(pdf, outdir, args.dpi)
    except RuntimeError as e:
        eprint(f"error: {e}")
        return 2

    print(f"rendered {len(pages)} pages -> {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
