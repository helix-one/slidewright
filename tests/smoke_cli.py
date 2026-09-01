#!/usr/bin/env python3
"""CLI smoke test: scaffold → assets → normalize → render → contact → overflow."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"\n$ {' '.join(args)}")
    proc = subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    # Windows consoles may be GBK; never crash the smoke on print encoding.
    def _safe(s: str) -> str:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        return s.encode(enc, errors="replace").decode(enc, errors="replace")

    if proc.stdout:
        print(_safe(proc.stdout.rstrip()))
    if proc.stderr:
        print(_safe(proc.stderr.rstrip()), file=sys.stderr)
    if check and proc.returncode != 0:
        raise SystemExit(f"FAILED (exit {proc.returncode}): {' '.join(args)}")
    return proc


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="academic-slides-smoke-"))
    talk = tmp / "talk"
    print(f"smoke dir: {tmp}")

    try:
        run([sys.executable, str(SCRIPTS / "new_talk.py"), str(talk),
             "--title", "Smoke Test Talk", "--author", "Test User"])

        # Create assets: high-res, low-res, svg
        from PIL import Image
        assets = talk / "assets"
        Image.new("RGB", (1200, 800), (30, 80, 140)).save(assets / "fig01.png")
        Image.new("RGB", (80, 60), (200, 40, 40)).save(assets / "tiny.png")
        (assets / "diagram.svg").write_text(
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">'
            '<circle cx="50" cy="50" r="40" fill="#1a3a5c"/></svg>',
            encoding="utf-8",
        )
        print("assets: fig01.png, tiny.png, diagram.svg")

        proc = run([sys.executable, str(SCRIPTS / "normalize_assets.py"), str(talk)])
        report = (assets / "_normalized" / "report.md").read_text(encoding="utf-8")
        assert "tiny.png" in report and "low-res" in report, "low-res flag missing"
        assert (assets / "_normalized" / "diagram.pdf").exists(), "svg→pdf missing"
        print("normalize: OK (low-res flagged, svg converted)")

        # Synthesize a PDF and exercise render/contact/overflow
        sys.path.insert(0, str(SCRIPTS))
        import check_overflow  # noqa: E402
        import contact_sheet  # noqa: E402
        import render_pages  # noqa: E402
        from reportlab.pdfgen import canvas

        pdf = talk / "build" / "smoke.pdf"
        pdf.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(pdf), pagesize=(720, 405))
        for i in range(1, 4):
            c.setFont("Helvetica", 14)
            c.drawString(60, 360, f"Page {i}")
            c.setFont("Helvetica", 8)
            c.drawString(345, 10, str(i))
            c.showPage()
        # collision page
        c.setFont("Helvetica", 11)
        c.drawString(60, 18, "collides with footer")
        c.setFont("Helvetica", 8)
        c.drawString(345, 10, "4")
        c.showPage()
        c.save()

        pages = render_pages.render(pdf, talk / "build" / "pages", dpi=90)
        assert len(pages) == 4, f"expected 4 pages, got {len(pages)}"
        sheet = contact_sheet.build_sheet(
            contact_sheet.collect_pages(talk / "build" / "pages"),
            talk / "build" / "contact-sheet.png", cols=2, thumb_w=200, label=True,
        )
        assert sheet.exists() and sheet.stat().st_size > 0
        print(f"render+contact: OK ({len(pages)} pages)")

        _, _, _, issues = check_overflow.analyze(str(pdf))
        err_pages = {i.page for i in issues if i.severity == "error"}
        assert 4 in err_pages, f"expected collision on p4; got {issues}"
        assert not ({1, 2, 3} & err_pages), f"clean pages flagged: {err_pages}"
        print(f"overflow: OK (flagged p4, clean 1-3)")

        # build.py without LaTeX should exit 2 with guidance
        proc = run([sys.executable, str(SCRIPTS / "build.py"), str(talk / "slides.tex")], check=False)
        assert proc.returncode == 2, f"expected exit 2 without LaTeX, got {proc.returncode}"
        print("build (no LaTeX): OK (graceful exit 2)")

        print("\n=== SMOKE PASSED ===")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
