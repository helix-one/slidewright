#!/usr/bin/env python3
r"""Normalize a talk's assets/ for Beamer and report on figure quality.

- SVG  -> PDF (Beamer cannot \includegraphics an .svg directly)
- video -> a still key-frame PNG (a PDF cannot play video reliably)
- raster/vector -> checked for resolution and flagged if likely too small

Prefers pure-Python backends (PyMuPDF, Pillow) so it runs without poppler /
inkscape; falls back to CLI tools when available.

Usage:
    python normalize_assets.py <talk-dir-or-assets-dir> [--min-px 900] [--json]

Outputs:
    <assets>/_normalized/*.pdf|*.png     converted assets
    <assets>/_normalized/report.md       human-readable mapping + quality flags
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:  # allow running as a script or importing as a module
    from _common import (
        RASTER_EXTS, VECTOR_EXTS, SVG_EXTS, VIDEO_EXTS, which, have_module, run,
    )
except ImportError:  # pragma: no cover
    from scripts._common import (  # type: ignore
        RASTER_EXTS, VECTOR_EXTS, SVG_EXTS, VIDEO_EXTS, which, have_module, run,
    )


def find_assets_dir(target: Path) -> Path:
    """Accept either a talk dir (containing assets/) or an assets dir itself."""
    if (target / "assets").is_dir():
        return target / "assets"
    return target


def classify(ext: str) -> str:
    ext = ext.lower()
    if ext in SVG_EXTS:
        return "svg"
    if ext in VIDEO_EXTS and ext != ".gif":
        return "video"
    if ext in RASTER_EXTS:
        return "raster"
    if ext in VECTOR_EXTS:
        return "vector"
    return "other"


def raster_dimensions(path: Path) -> tuple[int, int] | None:
    """Return (w, h) in pixels using Pillow, or None if unavailable."""
    if not have_module("PIL"):
        return None
    try:
        from PIL import Image

        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def svg_to_pdf(src: Path, dst: Path) -> bool:
    """Convert SVG->PDF. Try PyMuPDF, then cairosvg, then CLI tools."""
    if have_module("fitz"):
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(src))
            pdf_bytes = doc.convert_to_pdf()
            dst.write_bytes(pdf_bytes)
            return True
        except Exception:
            pass
    if have_module("cairosvg"):
        try:
            import cairosvg

            cairosvg.svg2pdf(url=str(src), write_to=str(dst))
            return True
        except Exception:
            pass
    for tool, cmd in (
        ("rsvg-convert", ["rsvg-convert", "-f", "pdf", "-o", str(dst), str(src)]),
        ("inkscape", ["inkscape", str(src), "--export-type=pdf", f"--export-filename={dst}"]),
    ):
        if which(tool):
            proc = run(cmd)
            if proc.returncode == 0 and dst.exists():
                return True
    return False


def video_keyframe(src: Path, dst: Path, at_seconds: float = 1.0) -> bool:
    """Grab one still frame from a video. Try imageio, opencv, then ffmpeg."""
    if have_module("imageio"):
        try:
            import imageio.v3 as iio

            frame = iio.imread(str(src), index=0)
            iio.imwrite(str(dst), frame)
            return True
        except Exception:
            pass
    if have_module("cv2"):
        try:
            import cv2

            cap = cv2.VideoCapture(str(src))
            ok, frame = cap.read()
            cap.release()
            if ok:
                cv2.imwrite(str(dst), frame)
                return True
        except Exception:
            pass
    if which("ffmpeg"):
        proc = run(["ffmpeg", "-y", "-ss", str(at_seconds), "-i", str(src),
                    "-frames:v", "1", str(dst)])
        if proc.returncode == 0 and dst.exists():
            return True
    return False


def normalize(assets_dir: Path, min_px: int) -> dict:
    out_dir = assets_dir / "_normalized"
    out_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict] = []
    for path in sorted(assets_dir.iterdir()):
        if path.is_dir() or path.name.startswith("."):
            continue
        kind = classify(path.suffix)
        entry: dict = {"file": path.name, "kind": kind, "normalized": None,
                       "flags": [], "dimensions": None}

        if kind == "svg":
            dst = out_dir / (path.stem + ".pdf")
            if svg_to_pdf(path, dst):
                entry["normalized"] = f"_normalized/{dst.name}"
            else:
                entry["flags"].append("svg->pdf failed (install pymupdf/cairosvg/inkscape)")

        elif kind == "video":
            dst = out_dir / (path.stem + ".png")
            if video_keyframe(path, dst):
                entry["normalized"] = f"_normalized/{dst.name}"
                entry["flags"].append("video: only a still frame is embedded; pick the frame you want")
            else:
                entry["flags"].append("video->frame failed; export a still PNG yourself")

        elif kind == "raster":
            dims = raster_dimensions(path)
            entry["dimensions"] = dims
            if dims and max(dims) < min_px:
                entry["flags"].append(f"low-res: {dims[0]}x{dims[1]}px (< {min_px}px) - may look blurry when enlarged")

        elif kind == "vector":
            pass  # PDF/EPS are resolution-independent; nothing to do.
        else:
            entry["flags"].append("unrecognized type - will not auto-include")

        entries.append(entry)

    report = {"assets_dir": str(assets_dir), "min_px": min_px, "entries": entries}
    _write_report(out_dir / "report.md", report)
    return report


def _write_report(path: Path, report: dict) -> None:
    lines = ["# Asset normalization report", "",
             f"- source: `{report['assets_dir']}`",
             f"- low-res threshold: {report['min_px']}px", "",
             "| file | kind | normalized | dimensions | flags |",
             "|------|------|------------|------------|-------|"]
    for e in report["entries"]:
        dims = f"{e['dimensions'][0]}x{e['dimensions'][1]}" if e["dimensions"] else "-"
        flags = "; ".join(e["flags"]) if e["flags"] else "ok"
        norm = e["normalized"] or "-"
        lines.append(f"| {e['file']} | {e['kind']} | {norm} | {dims} | {flags} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Normalize talk assets for Beamer.")
    ap.add_argument("target", help="Talk dir (with assets/) or an assets dir.")
    ap.add_argument("--min-px", type=int, default=900,
                    help="Flag raster images whose long side is below this (default 900).")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    assets_dir = find_assets_dir(Path(args.target).resolve())
    if not assets_dir.is_dir():
        print(f"error: no assets dir at {assets_dir}")
        return 1

    report = normalize(assets_dir, args.min_px)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        n = len(report["entries"])
        flagged = sum(1 for e in report["entries"] if e["flags"])
        conv = sum(1 for e in report["entries"] if e["normalized"])
        print(f"normalized {assets_dir}: {n} assets, {conv} converted, {flagged} flagged")
        print(f"report: {assets_dir / '_normalized' / 'report.md'}")
        for e in report["entries"]:
            if e["flags"]:
                print(f"  ! {e['file']}: {'; '.join(e['flags'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
