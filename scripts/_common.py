"""Shared helpers for the academic-slides scripts.

Cross-platform (Windows/macOS/Linux). Prefers pure-Python backends
(PyMuPDF, Pillow) so the visual-audit loop works without poppler; falls
back to CLI tools (latexmk, pdftoppm, pdftotext) when they are present.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def which(name: str) -> str | None:
    """Return the resolved path of a CLI tool, or None."""
    return shutil.which(name)


def have_module(name: str) -> bool:
    """True if an importable Python module is available."""
    import importlib.util

    return importlib.util.find_spec(name) is not None


def run(cmd: list[str], cwd: str | Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess:
    """Run a command, capturing output. Never raises on non-zero exit."""
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


def die(msg: str, code: int = 1) -> "None":
    eprint(f"error: {msg}")
    raise SystemExit(code)


# Extensions we treat as raster / vector / video assets.
RASTER_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"}
VECTOR_EXTS = {".pdf", ".eps"}
SVG_EXTS = {".svg"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".gif"}
