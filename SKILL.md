---
name: slidewright
description: >
  Turn a researcher-controlled scientific narrative into a clear LaTeX Beamer talk,
  then compile, render, and visually audit it in a loop. Use when the user wants to
  build/improve academic slides, a seminar/conference talk, a research presentation,
  学术汇报/组会/报告 slides, or says "make Beamer slides about my results/outline".
  The researcher owns the scientific story; if the story is incomplete, interview the
  researcher first — never infer the full narrative from figures alone.
---

# Slidewright

Help a researcher turn a **researcher-confirmed scientific narrative** into a clear
academic Beamer talk, and take over the LaTeX + compile + visual-audit toil.

## The one hard rule

> Never reconstruct the complete scientific story from `assets/` alone.
> If the story is incomplete, enter **Story** phase: ask questions, name gaps, offer
> candidate structures — do not silently decide the narrative or invent missing
> scientific connections. Never rewrite a confirmed claim without telling the researcher.

The researcher decides *what to say and why*. You help them *think it through, and
express it well*. First version targets **LaTeX Beamer → PDF** only.

## Three phases

Work through these in order. Do not jump to LaTeX before the story is confirmed.

### Phase 1 — Story  (read `references/story.md`)

Trigger: `outline.md` is missing, thin, or the narrative is unclear.

- If thin/missing → **interview**: ask at most **3 blocking questions per round**
  (audience, one-sentence takeaway, the actual question, claim→evidence links).
- If an outline exists → **review**: check every claim has evidence, flag logic jumps,
  over-long background, and time budget vs. `brief.md`.
- Output a candidate narrative; **wait for the researcher to confirm** before Phase 2.

### Phase 2 — Production  (read `references/writing-style.md` + `references/layouts.md`)

Story is confirmed. Now:

1. **Audit metric semantics before drawing result slides.** For every derived,
   project-specific, or potentially unfamiliar metric, trace the displayed value back to
   its analysis implementation and freeze: measured object, preprocessing, formula,
   aggregation order/statistical unit, interpretation, and limitation. The slide must
   make the calculation legible with an equation and/or schematic. If any link is
   unknown, return to Story phase rather than inventing a label or explanation. See the
   metric-slide rules in `references/writing-style.md`.
2. `python scripts/normalize_assets.py <talk-dir>` — svg→pdf, video→still, flag low-res
   figures. An asset existing does NOT mean it must appear; slides serve the story.
3. Write `slide-map.md` (one row per slide: question → message → visual). **Confirm any
   major narrative change with the researcher** before writing LaTeX.
4. Generate `slides.tex` from `templates/academic.tex` + the theme. Follow the
   composition patterns in `references/writing-style.md`:
   one message per slide · title = the conclusion · figures large · **no bullet walls**
   (`\itemize` is banned; use paragraphs / `\keybox` / `\statrow` / columns).
5. **Enforce the projection-size type floor.** At final slide size, audience-facing
   titles must be at least 28 pt; body text, equations, table text, figure axes, legends,
   and data annotations must be at least 20 pt, with 24 pt preferred for ordinary body
   text. Provenance notes, citations, page numbers, and other non-narrative footnotes may
   be smaller. Scaling a figure also scales its embedded labels, so check their effective
   size after placement. Split or simplify a slide when the floor does not fit; never
   solve density by shrinking scientific content. See `references/writing-style.md`.

### Phase 3 — Visual audit  (read `references/visual-audit.md`)

After the deck compiles, loop until it passes:

```
build → render pages → contact sheet (look overall) → zoom only suspect pages → fix → rebuild
```

```bash
python scripts/build.py <talk>/slides.tex
python scripts/check_overflow.py <talk>/build/slides.pdf     # text vs footer / off-canvas
python scripts/render_pages.py <talk>/build/slides.pdf
python scripts/contact_sheet.py <talk>/build/pages           # ONE image to eyeball rhythm
```

Cost rule: read the single **contact sheet** first for overall rhythm and to spot
suspects; only zoom into individual `pages/page-NN.png` that the sheet or
`check_overflow` flags. Do not read all pages one by one.

## Scaffolding a talk

```bash
python scripts/new_talk.py path/to/my-talk --title "..." --author "..."
```

Creates `brief.md`, `outline.md`, `slide-map.md`, `slides.tex`, the theme `.sty`,
`assets/`, `references.bib`, `build/`. The researcher fills `brief.md` + `outline.md`
and drops figures into `assets/`.

## Environment

- **Compile**: `latexmk -xelatex` preferred (xelatex needed for good/CJK fonts);
  `build.py` falls back to two `xelatex` passes. If no engine is installed, it prints
  install guidance — you may still deliver `.tex` + `.sty` for Overleaf.
- **Render / audit**: `render_pages.py`, `contact_sheet.py`, `check_overflow.py` prefer
  **PyMuPDF + Pillow** (pure Python, no system deps) and fall back to poppler
  (`pdftoppm` / `pdftotext`). `pip install pymupdf pillow reportlab pyyaml`.
- `check_overflow.py` catches *layout* overruns the LaTeX log misses; `build.py` also
  reports `Overfull \hbox` (line-level) from the log.

## Do NOT (first version)

Auto-parse a whole paper · auto-generate the full story · other backends
(Marp/Slidev/PPTX) · auto web-search literature · auto-draw complex figures ·
rewrite scientific claims without confirmation.

## Human ↔ AI split

| Item | Researcher | You (AI) |
|---|---|---|
| question / claim / story | decides | asks, challenges, proposes structures |
| evidence | provides, judges | organizes, matches to claims |
| slide order / layout | reviews, may steer | designs |
| LaTeX / compile / visual QA | need not touch | owns, auto-checks, iterates |

## Files

- `references/story.md` — Story interview & review protocol
- `references/writing-style.md` — Anti-AI composition patterns (with LaTeX)
- `references/layouts.md` — Slide layout catalog + `.tex` snippets
- `references/visual-audit.md` — Audit checklist + script usage
- `templates/` — `academic.tex`, `beamerthemeAcademicTalk.sty`, `brief/outline/slide-map.md`
- `scripts/` — `new_talk`, `normalize_assets`, `build`, `render_pages`, `contact_sheet`, `check_overflow`
- `examples/erk-waves/` — a small worked, compilable talk
