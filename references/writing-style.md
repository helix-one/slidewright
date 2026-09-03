# Writing style — make it look like a researcher wrote it

The #1 tell of AI-generated slides is bullet-list abuse and uniform pages. Avoid it.

## Hard rules

1. **One main message per slide.** If a page needs to say A, B, C, D, split it.
2. **Title = the conclusion**, not a topic.
   - weak: `Cross correlation` → better: `ERK activation precedes cell extension`.
3. **`\itemize` is banned.** Use paragraphs, `\enumerate` with an intro sentence, or the
   theme helpers (`\keybox`, `\statrow`, `\hyporow`, columns). ~80% of pages should be
   paragraph-style.
4. **Adjacent slides use different composition patterns** (see below).
5. **Figures large**; `figure + one sentence`, never `6 bullets + tiny figure`.
6. Inline emphasis instead of lists: `\alert{keyword}` (1-2/slide),
   `\textbf{term}\,---\,explanation`, `$\bullet$ \textbf{point}`.

## Projection readability gate

Font sizes are judged at the final projected slide, not in the source asset:

- **slide titles:** at least 28 pt;
- **ordinary body text:** 24 pt preferred and never below 20 pt;
- **equations, tables, figure axes, tick labels, legends, scale bars, and scientific
  annotations:** at least 20 pt equivalent;
- **provenance-only material** such as citations, source paths, page numbers, and notes
  that are not needed to follow the argument may be smaller.

The floor includes text baked into PNGs and other figures. If a figure is generated at
font size $F$ and placed at scale $s$, its approximate effective size is $sF$; inspect the
rendered slide rather than trusting the plotting script. A listener should be able to
read every scientific label from the back of a seminar room.

When content does not fit, first remove repetition, then enlarge/crop the figure, and
then split the slide. Do not reduce audience-facing text below the floor. A clean compile
or lack of geometric overflow does not constitute a readability pass.

## Metric semantics gate

A plotted number is not self-explanatory. Before placing a derived, project-specific, or
potentially unfamiliar metric on a slide, verify it against the analysis code and source
table. Freeze all six links below:

1. **Measured object** — what entity and raw quantity enter the calculation;
2. **Preprocessing** — normalization, detrending, smoothing, windows, and exclusions;
3. **Formula** — the exact mathematical definition used by the implementation;
4. **Aggregation order** — whether averaging occurs over time, cells, regions, fields,
   or biological repeats, and in what order;
5. **Interpretation** — what a larger or smaller value physically means;
6. **Limitation** — what the metric cannot distinguish or establish.

Do not coin a compact label such as “collective fluctuation”, “integration gain”, or
“relay score” unless it is either standard in the field or explicitly defined on first
use. Prefer a literal name that exposes the operation, for example “amplitude of the
per-frame regional median ERK trace”. Do not silently combine a formula from one
analysis variant with values from another.

For a metric-introduction slide, show the chain visually:

`raw image/trace → selected objects/window → preprocessing → equation → plotted summary`.

Use a small schematic or representative traces alongside the equation, then state in one
sentence what high and low values mean. If this cannot remain readable at presentation
size, split method and result across two slides. A result-only bar chart with an undefined
metric fails production review even when its layout is clean.

## Red-flag phrasing (rewrite)

Titles: "深入探讨…" / "全面分析…" / "…的重要性" / generic "Methods" / "Results".
Body: "值得注意的是…" / "综上所述" / "显而易见" / "本研究具有重要的理论与实践价值".
Test: *"Does this read like a researcher wrote it, or an AI?"* If AI, rewrite.

## Composition patterns (rotate these)

### 1 · paragraph + take-home box
```latex
\begin{frame}
  \frametitle{Mechanical deformation can feed back into ERK}
  \vskip0.1cm
  In migrating MDCK monolayers, ERK activity travels as waves whose fronts
  track regions of active cell extension.
  \vskip0.2cm
  \keybox{\textbf{Question:} is deformation alone enough to \alert{sustain} the wave?}
\end{frame}
```

### 2 · paragraph + equation + interpretation
```latex
\begin{frame}
  \frametitle{A two-variable minimal model}
  \vskip0.1cm
  Couple ERK activity $E$ to local strain $s$:
  \[ \dot E = -\,kE + f(s),\qquad \dot s = \alpha E - \beta s. \]
  \vskip0.1cm
  The single feedback term $f(s)$ is sufficient to generate traveling oscillations.
\end{frame}
```

### 3 · intro + enumerate (only allowed list form)
```latex
\begin{frame}
  \frametitle{Three predictions we can test}
  \vskip0.15cm
  The model makes concrete, falsifiable predictions:
  \vskip0.25cm
  \begin{enumerate}\setlength\itemsep{0.5em}
    \item \textbf{Phase lead}\,---\,ERK leads strain by a fixed lag;
    \item \textbf{Speed}\,---\,wave speed scales with $\alpha$;
    \item \textbf{Arrest}\,---\,blocking feedback halts propagation.
  \end{enumerate}
\end{frame}
```

### 4 · paragraph + booktabs table + conclusion
```latex
\begin{frame}
  \frametitle{The model reproduces the measured phase relation}
  \vskip0.1cm
  \begin{center}\small
  \begin{tabular}{@{}lcc@{}}
    \toprule
    & \textbf{Experiment} & \textbf{Model} \\ \midrule
    Phase lag (min) & $19\pm3$ & $21$ \\
    Wave speed (\si{\micro m/min}) & $2.4$ & $2.2$ \\
    \bottomrule
  \end{tabular}
  \end{center}
  \vskip0.15cm
  Both quantities fall within experimental error — no parameter tuning.
\end{frame}
```

### 5 · text-left + figure-right (columns)
```latex
\begin{frame}
  \frametitle{ERK fronts track extension, not compression}
  \begin{columns}[T, onlytextwidth]
    \column{0.52\textwidth}
      \vskip0.1cm
      Cross-correlating the two channels gives a single, consistent lag.\par\vskip0.15cm
      $\bullet$ \textbf{Sign}\,---\,ERK leads;\par\vskip0.1cm
      $\bullet$ \textbf{Lag}\,---\,$\sim$20 min across fields.
    \column{0.46\textwidth}
      \includegraphics[width=\linewidth, height=0.62\textheight, keepaspectratio]{fig_xcorr}
      \figcap{Fig 3\;cross-correlation}
  \end{columns}
\end{frame}
```

### 6 · full-bleed figure + one caption line
```latex
\begin{frame}
  \frametitle{The feedback generates traveling oscillations}
  \begin{tikzpicture}[remember picture, overlay]
    \node[anchor=center] at ([yshift=-0.25cm]current page.center) {%
      \includegraphics[width=0.90\paperwidth, height=0.70\paperheight, keepaspectratio]{fig_sim}};
  \end{tikzpicture}
  \vskip-0.4cm
  \begin{flushleft}\scriptsize\itshape\color{textgray}
  Fig 5\;kymograph of simulated ERK activity
  \end{flushleft}
\end{frame}
```

## Figures from papers

You MAY crop a panel, enlarge a region, split across two slides, add a box/arrow, or a
short annotation. You MAY NOT alter the scientific data. Number figures sequentially
(`Fig 1`, `Fig 2`, …) with `\figcap{}`.

## Density budget

| item | limit |
|---|---|
| text on a text-only slide | ~150-200 chars |
| text on a slide with a figure | ~100-150 chars |
| equations per slide | ≤ 2 |
| table rows | 3-8 |
| `\alert{}` per slide | 1-2 |
