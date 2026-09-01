# Visual audit — render, look, fix, repeat

Compiling clean is not enough. Loop until the deck *looks* right.

```
build.py → check_overflow.py → render_pages.py → contact_sheet.py
        → look at the ONE contact sheet → zoom only suspect pages → fix → rebuild
```

## Commands

```bash
python scripts/build.py my-talk/slides.tex                 # compile (xelatex/latexmk)
python scripts/check_overflow.py my-talk/build/slides.pdf  # layout overruns (exit!=0 if any)
python scripts/render_pages.py my-talk/build/slides.pdf     # -> build/pages/page-NN.png
python scripts/contact_sheet.py my-talk/build/pages --label # -> build/contact-sheet.png
```

All render/check tools prefer PyMuPDF+Pillow (no system deps); poppler is a fallback.

## Cost rule (important)

Do **not** read all `page-NN.png` one by one — that is slow and expensive. Instead:

1. Read the single **`contact-sheet.png`** to judge overall rhythm and spot suspects.
2. Read **`check_overflow.py`** output (machine-precise: which page, which text, how far).
3. Zoom into **only** the flagged pages (`build/pages/page-NN.png`) at full size.

## What `check_overflow.py` catches (automatically)

- `footer_collision` — body text drops into the footer / page-number band.
- `off_canvas_*` — text past any page edge.
- `page_bottom` / `near_page_edge` — no footer detected, text near/over the bottom.
- `not_analyzable` — an image-only page (nothing to check; eyeball it).

It complements the LaTeX log's `Overfull \hbox` (line-level) that `build.py` reports.
Fix a flagged frame by: `\small`/`\footnotesize` on the body · shrink the figure
`height` · split the frame in two. Then rebuild and re-check.

## What YOU check on the contact sheet (needs judgment)

**Layout**
- overflow / overlap / abnormal margins / bad figure-to-text ratio.

**Readability**
- Are axis labels, legends, error bars legible at slide size? If a figure's text is
  unreadable, it hasn't done its job → enlarge, crop, or split.
- Equations not too dense; references not stealing visual attention.

**Information density**
- One dominant message per page? Any "wall of paper screenshots"? Any bullet walls
  (should be near zero — see `writing-style.md`)?

**Visual hierarchy** — 5-second test
- Glancing at a page, is the first thing the eye lands on the thing you *want* seen?

**Narrative continuity** — read the sheet in order
- Does slide N → N+1 follow naturally, or would it need long verbal glue? If a jump
  only works with heavy narration, the sequence is probably wrong → revisit `slide-map.md`.

## Exit criteria

- `check_overflow.py` exits clean (no errors).
- No `Overfull \hbox` on critical text frames.
- Contact sheet reads as a coherent story with large, legible figures and no bullet walls.
- Every content slide's title states its conclusion.
