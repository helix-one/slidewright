# slidewright

> Turn a researcher-controlled scientific narrative into a clear Beamer talk,
> with an automatic visual-audit loop.

A Cursor/Claude **skill** — not a "figures → PPT" button: the researcher owns the story;
the AI helps think it through and takes over the LaTeX + compile + layout-checking toil.

> Design rationale: [`DESIGN.md`](DESIGN.md). Runtime instructions: [`SKILL.md`](SKILL.md).

## What it does

```
Story (interview/review)  →  Production (assets → slide-map → Beamer)  →  Visual audit (render → check → fix)
        researcher confirms            AI drafts, researcher steers              AI loops until it looks right
```

- **Story first.** If the outline is thin, the skill interviews the researcher
  (≤3 questions/round) instead of inventing a narrative from the figures.
- **Anti-AI slides.** One message per slide, conclusion-titles, big figures,
  no bullet walls (`\itemize` is banned) — see `references/writing-style.md`.
- **Closed-loop QA.** Renders every page, tiles a contact sheet, and runs a word-level
  overflow/footer-collision check so problems are found automatically, cheaply.

## Layout

```
slidewright/                (this folder = the skill)
├── SKILL.md                # runtime instructions (thin; points to references/)
├── DESIGN.md               # design rationale (slim)
├── README.md
├── requirements.txt
├── references/             # loaded on demand
│   ├── story.md            # interview & review protocol
│   ├── writing-style.md    # 6 composition patterns (with LaTeX)
│   ├── layouts.md          # slide layout catalog + snippets
│   └── visual-audit.md     # audit checklist + script usage
├── templates/
│   ├── academic.tex        # deck skeleton (placeholders)
│   ├── beamerthemeAcademicTalk.sty
│   └── brief.md / outline.md / slide-map.md
├── scripts/                # cross-platform, pure-Python backends preferred
│   ├── new_talk.py         # scaffold a talk project
│   ├── normalize_assets.py # svg→pdf, video→still, flag low-res
│   ├── build.py            # compile via latexmk/xelatex + parse log
│   ├── render_pages.py     # pdf → per-page png (PyMuPDF/pdftoppm)
│   ├── contact_sheet.py    # tile pages into one overview (Pillow)
│   └── check_overflow.py   # text-vs-footer / off-canvas detector
├── examples/erk-waves/     # a small, self-contained, compilable talk
└── tests/                  # unit + CLI smoke tests (no LaTeX needed)
```

## Quick start

```bash
pip install -r requirements.txt        # pymupdf pillow pyyaml reportlab

# 1. scaffold
python scripts/new_talk.py my-talk --title "..." --author "..."
#    → fill my-talk/brief.md + outline.md, drop figures into my-talk/assets/

# 2. produce
python scripts/normalize_assets.py my-talk        # svg→pdf, video→still, quality flags
#    → AI writes my-talk/slides.tex from the confirmed slide-map

# 3. build + audit
python scripts/build.py my-talk/slides.tex                 # → build/slides.pdf
python scripts/check_overflow.py my-talk/build/slides.pdf  # layout overruns
python scripts/render_pages.py my-talk/build/slides.pdf     # → build/pages/*.png
python scripts/contact_sheet.py my-talk/build/pages --label # → build/contact-sheet.png
```

## Requirements

- **Python 3.10+** with `pymupdf`, `pillow` (and `reportlab` for tests). These give the
  render + audit tools **without any system dependency**.
- **LaTeX** with `xelatex` (and ideally `latexmk`) to compile `.tex → .pdf`.
  Install MiKTeX/TeX Live (Windows), MacTeX (macOS), or `texlive-xetex` (Linux).
  Without it you can still author and deliver `.tex` + `.sty` for Overleaf.
- Optional CLI fallbacks: poppler (`pdftoppm`/`pdftotext`), inkscape/librsvg, ffmpeg.

## Tests

```bash
python -m unittest discover -s tests      # 13 tests + optional: python tests/smoke_cli.py
```

The suite synthesizes a slide PDF with `reportlab` and assets with `Pillow`, so it runs
**without LaTeX or poppler**. All scripts are exercised through their core logic.

> Note: the bundled `examples/erk-waves/slides.tex` is standard Beamer using the bundled
> theme and is structurally validated (balanced environments), but compiling it to PDF
> requires a local LaTeX install.

## Credits

Builds on ideas from:

- [`Faust-Donf/beamer-academic`](https://github.com/Faust-Donf/beamer-academic) — the
  academic Beamer theme and the anti-AI writing patterns.
- [`dro42/presentation-kit`](https://github.com/dro42/presentation-kit) — skill
  engineering structure and the `slide-overflow-check` layout audit.

## License

MIT — see [`LICENSE`](LICENSE).
