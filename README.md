# KOPAR

Original futuristic-cyberpunk display typeface. Geometric sans, monolinear,
vertical stress, slightly extended stance. Squared-Eurostile-era geometry,
HUD/terminal graphics, neon signage — precision-engineered, never distressed.
No existing font is traced or copied; every outline is generated
parametrically by the tools in this directory.

## Design DNA

Three signature moves, applied consistently:

1. **45° corner cuts** on selected stroke terminals (arms of E F L T,
   ends of t r f s) — 40-unit legs.
2. **Flat-cut apexes/vertexes** on A V W M N — no sharp points; cut apexes
   overshoot by 12.
3. **Circuit notches** — 40×22 rectangular steps cut into the bowl-side
   member at every bowl→stem weld (b d p q n m h) and at the waists of
   B R K, flush to the weld corner, opening toward the adjacent
   counter/aperture.

Rounds (O C G D o b d p q) are squared superellipses: rounded rects with
corner tension k = 0.82 outside / 0.86 inside (0.5523 ≈ circular).

## Grid (non-negotiable)

| unit | value |
|---|---|
| UPM / baseline | 1000 / y=0 (SVG deliverables: baseline y=800) |
| cap / x-height | 700 / 540 |
| ascender / descender | 720 / −190 |
| vertical stems | 92 |
| horizontals | 84 |
| curves | 100 thickest → 80 thinnest |
| overshoot (rounds, cut apexes) | 12 |
| crossbar centers (E H B R) | math center +16 |

Figures: cap height, tabular, slashed zero. Lower stories of B E K R S
wider than upper.

## Layout

```
glyphs/          deliverable SVGs, one per glyph  (U+0048_H.svg)
metrics.json     global metrics + per-glyph advance/lsb/rsb + kerning
build.py         fontTools compiler → dist/KOPAR-Regular.{otf,ttf,woff2}
tools/           parametric glyph sources (geometry.py, glyphs.py, generate.py)
specimen/        live dark review specimens per stage
```

Regenerate everything: `python3 tools/generate.py`
Compile the font:      `python3 build.py`   (needs `pip install fonttools brotli`)
Then re-run generate.py once more to embed the fresh woff2 in the specimen.

SVG convention: outer contours clockwise in SVG space (= CCW in font space
after the y-flip), counters opposite. build.py relies on this; it feeds CFF
directly and reverses for TrueType quadratics.

## Stage log

- **Stage 1 — control letters O H E n o a** (this commit): locks proportion,
  corner language, rhythm. Decisions taken:
  - H ink 584 wide (counter 400) — the "slightly extended" stance.
  - n/m/h arches are flat-topped squares → they sit ON x-height, no
    overshoot (the spec's overshoot list covers true rounds only).
  - a is double-story with a squared L-hook and flat-cut terminal; its
    bowl-bottom overshoot meets the flat stem foot through a 12×12
    45° transition bevel at the weld.
  - Sidebearings are provisional scaffolding until stage 5 (Tracy method).
  - Space advance 260, provisional.
- Stage 2 — uppercase by group: rounds C G Q D S · squares I L F T ·
  diagonals A V W X Y · combos B P R M N K U J Z.
- Stage 3 — lowercase (from n: m h u r · from o: b d p q c e · then
  i j l t f k v w x y z s g) + hamburgefontsiv.
- Stage 4 — figures 0-9, punctuation, currency.
- Stage 5 — spacing (Tracy) + kerning pass.
- Stage 6 — QA specimen, pangram, mock UI panel at 96/32/16/12 px.
