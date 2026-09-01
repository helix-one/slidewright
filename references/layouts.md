# Layouts — catalog + `.tex` snippets

Each `slide-map.md` row names a `layout`. Pick by content; do not use the same layout
3 slides in a row. All snippets assume the `beamerthemeAcademicTalk` theme is loaded.

| layout | use for | helper |
|---|---|---|
| `title` | opener | `\titlepage` |
| `toc` | one-line agenda with em-dash subtitles | `tabbing` (see template) |
| `section-divider` | chapter boundary | `\sectiondivider{n}{Title}` |
| `text-keybox` | context + the question/claim | `\keybox{}` |
| `text-left-image-right` | text-primary + supporting figure | `columns` |
| `image-left-text-right` | figure-primary + interpretation | `columns` |
| `full-image` | one high-information figure | tikz overlay + `\figcap` |
| `text-eq-text` | derivation / model | `\[ ... \]` |
| `table` | multi-row comparison | `booktabs` |
| `stats` | 3 headline numbers | `\statrow{}{}...` |
| `hypotheses` | 3 parallel claims | `\hyporow{}{}...` |
| `statement` | one full-bleed sentence | `\statementframe{}` |
| `thanks` | closing (no "THANK YOU") | `\thanksframe{}{}` |

## Selection rules

1. Chapter start → `section-divider`.
2. Core model/equation → `text-eq-text`.
3. Multi-row data → `table`; 3 key numbers → `stats`.
4. High-information single figure → `full-image`.
5. Text-primary w/ figure → `text-left-image-right`; figure-primary → `image-left-text-right`.
6. Pure background/concept → `text-keybox`.
7. Key take-home → `statement`.

## Snippets not shown in writing-style.md

### toc (one line per section, subtitle carries the message)
```latex
\begin{frame}
  \frametitle{Outline}
  \vskip0.3cm
  {\footnotesize
  \begin{tabbing}
  \hspace{0.4cm}\=\hspace{0.6cm}\=\kill
  \textbf{\color{accentcolor}1}\>\textbf{Question}\,---\,why waves need an explanation\\[8pt]
  \textbf{\color{accentcolor}2}\>\textbf{Observation}\,---\,ERK leads extension\\[8pt]
  \textbf{\color{accentcolor}3}\>\textbf{Mechanism}\,---\,a minimal feedback\\[8pt]
  \textbf{\color{accentcolor}4}\>\textbf{Test}\,---\,it predicts the phase lead\\
  \end{tabbing}}
\end{frame}
```

### stats (three headline numbers)
```latex
\begin{frame}
  \frametitle{The minimal model, in three numbers}
  \statrow{2}{coupled variables}{1}{feedback term}{0}{fitted parameters}
\end{frame}
```

### hypotheses (three parallel columns)
```latex
\begin{frame}
  \frametitle{Three testable predictions}
  \hyporow{H1}{ERK leads strain by a fixed lag.}
          {H2}{Wave speed scales with $\alpha$.}
          {H3}{Blocking feedback halts the wave.}
\end{frame}
```

### image-left-text-right
```latex
\begin{frame}
  \frametitle{Existing models predict the wrong phase}
  \begin{columns}[T, onlytextwidth]
    \column{0.46\textwidth}
      \includegraphics[width=\linewidth, height=0.62\textheight, keepaspectratio]{fig_prior}
      \figcap{Fig 4\;prior model}
    \column{0.52\textwidth}
      \vskip0.1cm
      A purely chemical model reproduces the wave but puts ERK \alert{behind} strain.\par
      \vskip0.15cm
      That sign flip is exactly what the mechanical feedback fixes.
  \end{columns}
\end{frame}
```

## Overflow-safe defaults (apply while writing, not only after)

- `text-left-image-right`: left text ≤ ~150 chars, image `height ≤ 0.62\textheight`.
- `full-image`: only tikz-overlay positioning + `\figcap`; no surrounding paragraphs.
- `text-eq-text`: ≤ 2 equations, `\vskip0.1cm` between.
- Never more than ~3 `\vskip` in one frame (a sign of overstuffing → split the slide).
- Frames with verbatim/code need `\begin{frame}[fragile]`.

After building, `check_overflow.py` verifies none of this leaked; fix flagged frames by
`\small`/`\footnotesize` on the body, shrinking a figure, or splitting the frame.
