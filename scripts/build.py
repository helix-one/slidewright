#!/usr/bin/env python3
"""Compile a Beamer deck to PDF and surface layout warnings.

Prefers `latexmk -xelatex`; falls back to two `xelatex` passes. If no LaTeX
engine is installed it prints an actionable message and exits non-zero (the
skill can still deliver the .tex + .sty for Overleaf).

Usage:
    python build.py <slides.tex> [--outdir build] [--engine auto|latexmk|xelatex|pdflatex]

Parses the .log for:
    - errors (lines starting with '!')
    - Overfull \\hbox / \\vbox warnings (per-page typesetting overruns)
    - missing-file / undefined-reference warnings
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    from _common import which, run, eprint
except ImportError:  # pragma: no cover
    from scripts._common import which, run, eprint  # type: ignore


def pick_engine(preferred: str) -> str | None:
    order = {
        "auto": ["latexmk", "xelatex", "pdflatex"],
        "latexmk": ["latexmk"],
        "xelatex": ["xelatex"],
        "pdflatex": ["pdflatex"],
    }[preferred]
    for e in order:
        if which(e):
            return e
    return None


def compile_deck(tex: Path, outdir: Path, engine: str) -> tuple[int, Path | None]:
    outdir.mkdir(parents=True, exist_ok=True)
    cwd = tex.parent
    name = tex.name

    if engine == "latexmk":
        cmd = ["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error",
               f"-outdir={outdir}", name]
        proc = run(cmd, cwd=cwd, timeout=600)
        rc = proc.returncode
    else:
        # Two passes so the progress bar / toc / refs settle.
        rc = 0
        for _ in range(2):
            cmd = [engine, "-interaction=nonstopmode", "-halt-on-error",
                   f"-output-directory={outdir}", name]
            proc = run(cmd, cwd=cwd, timeout=600)
            rc = proc.returncode
            if rc != 0:
                break

    pdf = outdir / (tex.stem + ".pdf")
    return rc, (pdf if pdf.exists() else None)


LOG_ERROR = re.compile(r"^!(.*)")
LOG_OVERFULL = re.compile(r"^(Overfull|Underfull) \\([hv])box.*")
LOG_MISSING = re.compile(r"File `([^']+)' not found")
LOG_UNDEF = re.compile(r"Reference `([^']+)' on page (\d+) undefined")


def parse_log(log_path: Path) -> dict:
    result = {"errors": [], "overfull": [], "missing_files": [], "undefined_refs": []}
    if not log_path.exists():
        return result
    text = log_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        m = LOG_ERROR.match(line)
        if m and m.group(1).strip():
            result["errors"].append(line.strip())
        if LOG_OVERFULL.match(line):
            result["overfull"].append(line.strip())
        m = LOG_MISSING.search(line)
        if m:
            result["missing_files"].append(m.group(1))
        m = LOG_UNDEF.search(line)
        if m:
            result["undefined_refs"].append(f"{m.group(1)} (p{m.group(2)})")
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compile a Beamer deck to PDF.")
    ap.add_argument("tex", help="Path to slides.tex")
    ap.add_argument("--outdir", default="build")
    ap.add_argument("--engine", default="auto",
                    choices=["auto", "latexmk", "xelatex", "pdflatex"])
    args = ap.parse_args(argv)

    tex = Path(args.tex).resolve()
    if not tex.is_file():
        eprint(f"error: not found: {tex}")
        return 1

    engine = pick_engine(args.engine)
    if engine is None:
        eprint("error: no LaTeX engine found (latexmk / xelatex / pdflatex).")
        eprint("install a TeX distribution, e.g.:")
        eprint("  Windows: install MiKTeX or TeX Live, ensure xelatex is on PATH")
        eprint("  macOS:   brew install --cask mactex-no-gui")
        eprint("  Linux:   sudo apt install texlive-xetex texlive-fonts-recommended")
        eprint("or deliver the .tex + .sty and compile on Overleaf.")
        return 2

    outdir = (tex.parent / args.outdir).resolve()
    rc, pdf = compile_deck(tex, outdir, engine)
    log = parse_log(outdir / (tex.stem + ".log"))

    print(f"engine: {engine}  ->  exit {rc}")
    if pdf:
        print(f"pdf: {pdf}")
    if log["errors"]:
        print(f"\nLaTeX errors ({len(log['errors'])}):")
        for e in log["errors"][:15]:
            print(f"  {e}")
    if log["missing_files"]:
        print(f"\nmissing files ({len(log['missing_files'])}):")
        for f in log["missing_files"][:15]:
            print(f"  {f}")
    if log["overfull"]:
        print(f"\noverfull/underfull boxes ({len(log['overfull'])}) - check those frames:")
        for o in log["overfull"][:15]:
            print(f"  {o}")
    if log["undefined_refs"]:
        print(f"\nundefined refs ({len(log['undefined_refs'])}): {', '.join(log['undefined_refs'][:10])}")

    if pdf is None or rc != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
