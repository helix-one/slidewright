#!/usr/bin/env python3
"""Scaffold a talk project directory from the bundled templates.

Usage:
    python new_talk.py <target-dir> [--title "..."] [--author "..."]

Creates:
    <target-dir>/
      brief.md  outline.md  slide-map.md
      assets/  assets/_normalized/  build/
      references.bib
      beamerthemeAcademicTalk.sty   (copied from templates)
      slides.tex                    (from academic.tex, placeholders filled where given)
"""

from __future__ import annotations

import argparse
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def scaffold(target: Path, title: str | None, author: str | None, force: bool) -> list[str]:
    created: list[str] = []
    target.mkdir(parents=True, exist_ok=True)

    for sub in ("assets", "assets/_normalized", "build"):
        (target / sub).mkdir(parents=True, exist_ok=True)

    # Copy input templates verbatim.
    for name in ("brief.md", "outline.md", "slide-map.md"):
        dst = target / name
        if dst.exists() and not force:
            continue
        dst.write_text((TEMPLATES / name).read_text(encoding="utf-8"), encoding="utf-8")
        created.append(name)

    # Copy the theme next to the deck (Beamer needs it on TEXINPUTS).
    theme = "beamerthemeAcademicTalk.sty"
    dst = target / theme
    if not dst.exists() or force:
        dst.write_text((TEMPLATES / theme).read_text(encoding="utf-8"), encoding="utf-8")
        created.append(theme)

    # references.bib stub.
    bib = target / "references.bib"
    if not bib.exists() or force:
        bib.write_text("% Add BibTeX entries here.\n", encoding="utf-8")
        created.append("references.bib")

    # slides.tex from academic.tex, filling a couple of obvious placeholders.
    deck = (TEMPLATES / "academic.tex").read_text(encoding="utf-8")
    if title:
        deck = deck.replace("{{FULL_TITLE}}", title).replace("{{SHORT_TITLE}}", title[:24])
    if author:
        deck = deck.replace("{{AUTHOR}}", author).replace("{{SHORT_AUTHOR}}", author.split()[0] if author else "")
    dst = target / "slides.tex"
    if not dst.exists() or force:
        dst.write_text(deck, encoding="utf-8")
        created.append("slides.tex")

    return created


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scaffold an academic talk project.")
    ap.add_argument("target", help="Directory to create the talk in.")
    ap.add_argument("--title", default=None)
    ap.add_argument("--author", default=None)
    ap.add_argument("--force", action="store_true", help="Overwrite existing files.")
    args = ap.parse_args(argv)

    target = Path(args.target).resolve()
    created = scaffold(target, args.title, args.author, args.force)
    print(f"scaffolded talk at: {target}")
    for c in created:
        print(f"  + {c}")
    if not created:
        print("  (nothing new; use --force to overwrite)")
    print("\nnext: fill brief.md + outline.md, drop figures into assets/, then run"
          " normalize_assets.py and build.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
