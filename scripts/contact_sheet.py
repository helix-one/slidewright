#!/usr/bin/env python3
"""Tile per-page PNGs into a single contact sheet for a first-pass overview.

The audit strategy: the model reads ONE contact sheet to judge overall rhythm
and spot suspects cheaply, then zooms into flagged pages individually. Uses
Pillow only.

Usage:
    python contact_sheet.py <pages-dir> [--out build/contact-sheet.png]
        [--cols 4] [--thumb 480] [--label]
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from _common import have_module, eprint
except ImportError:  # pragma: no cover
    from scripts._common import have_module, eprint  # type: ignore


def build_sheet(page_paths: list[Path], out: Path, cols: int, thumb_w: int,
                label: bool, pad: int = 12, bg=(255, 255, 255)) -> Path:
    from PIL import Image, ImageDraw

    if not page_paths:
        raise RuntimeError("no page images found")

    thumbs = []
    for p in page_paths:
        im = Image.open(p).convert("RGB")
        w, h = im.size
        tw = thumb_w
        th = max(1, round(h * tw / w))
        thumbs.append((p.stem, im.resize((tw, th))))

    cell_w = thumb_w
    cell_h = max(t.size[1] for _, t in thumbs)
    label_h = 18 if label else 0
    rows = (len(thumbs) + cols - 1) // cols

    sheet_w = cols * cell_w + (cols + 1) * pad
    sheet_h = rows * (cell_h + label_h) + (rows + 1) * pad
    sheet = Image.new("RGB", (sheet_w, sheet_h), bg)
    draw = ImageDraw.Draw(sheet)

    for idx, (name, tim) in enumerate(thumbs):
        r, c = divmod(idx, cols)
        x = pad + c * (cell_w + pad)
        y = pad + r * (cell_h + label_h + pad)
        sheet.paste(tim, (x, y))
        if label:
            draw.text((x + 2, y + tim.size[1] + 2), name, fill=(90, 90, 90))

    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(str(out))
    return out


def collect_pages(pages_dir: Path) -> list[Path]:
    def key(p: Path):
        import re
        m = re.search(r"(\d+)", p.stem)
        return int(m.group(1)) if m else 0
    return sorted(pages_dir.glob("*.png"), key=key)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build a contact sheet from page PNGs.")
    ap.add_argument("pages_dir", help="Directory containing page-*.png")
    ap.add_argument("--out", default=None, help="Default: <pages-dir>/../contact-sheet.png")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--thumb", type=int, default=480, help="Thumbnail width in px.")
    ap.add_argument("--label", action="store_true", help="Draw page labels.")
    args = ap.parse_args(argv)

    if not have_module("PIL"):
        eprint("error: Pillow is required (pip install pillow).")
        return 2

    pages_dir = Path(args.pages_dir).resolve()
    page_paths = collect_pages(pages_dir)
    if not page_paths:
        eprint(f"error: no PNGs in {pages_dir}")
        return 1
    out = Path(args.out).resolve() if args.out else pages_dir.parent / "contact-sheet.png"

    try:
        out = build_sheet(page_paths, out, args.cols, args.thumb, args.label)
    except RuntimeError as e:
        eprint(f"error: {e}")
        return 1
    print(f"contact sheet: {out}  ({len(page_paths)} pages, {args.cols} cols)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
