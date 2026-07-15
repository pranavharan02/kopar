"""KOPAR generator.

Emits, for every glyph defined so far:
  glyphs/U+XXXX_name.svg    (deliverable: single filled path)
  metrics.json              (deliverable: global metrics + per-glyph + kerning)
  specimen/stageN.html      (live dark specimen for review)

Run:  python3 tools/generate.py  (from repo root or anywhere).
"""

import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from geometry import glyph_svg_d, ink_bbox, BASELINE_SVG  # noqa: E402
import glyphs as G  # noqa: E402

STAGE = 3
INK = "#E8F0FF"
BG = "#0A0E14"
GUIDE = "#00F0FF"

KERNING = {}   # populated in stage 5


# ----------------------------------------------------------- deliverables

def write_glyph_svgs(gs):
    outdir = os.path.join(ROOT, "glyphs")
    os.makedirs(outdir, exist_ok=True)
    for g in gs:
        d = glyph_svg_d(g.contours, lsb=g.lsb)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {g.adv} 1000">'
            f'<path d="{d}" fill="#000000"/></svg>\n'
        )
        fname = f"{g.unicode}_{g.name}.svg"
        with open(os.path.join(outdir, fname), "w") as f:
            f.write(svg)
    return outdir


def write_metrics(gs):
    entries = [{
        "unicode": g.unicode, "name": g.name, "advanceWidth": g.adv,
        "lsb": g.lsb, "rsb": g.rsb,
    } for g in gs]
    entries.append(dict(G.SPACE))
    entries.sort(key=lambda e: e["unicode"])
    data = {
        "upm": G.UPM, "capHeight": G.CAP, "xHeight": G.XH,
        "ascender": G.ASC, "descender": G.DESC,
        "baselineY": BASELINE_SVG, "overshoot": G.OVER,
        "glyphs": entries,
        "kerning": KERNING,
    }
    path = os.path.join(ROOT, "metrics.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


# ------------------------------------------------------------- specimen

def _glyph_path_tag(g, x_origin, fill=INK):
    d = glyph_svg_d(g.contours, lsb=g.lsb)
    return f'<g transform="translate({x_origin} 0)"><path d="{d}" fill="{fill}"/></g>'


def guide_row_svg(row, track=44):
    """One row of glyphs on shared metrics with cyan guides."""
    pad_l, pad_r = 148, 40
    x = pad_l
    parts = []
    for g in row:
        parts.append(_glyph_path_tag(g, x))
        x += g.adv + track
    w = x - track + pad_r
    top, bot = 30, 1000

    def hline(y, label, dashed=False, strong=False):
        dash = ' stroke-dasharray="3 7"' if dashed else ""
        op = "0.9" if strong else "0.55"
        t = (f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="{GUIDE}" '
             f'stroke-width="1" opacity="{op}"{dash}/>')
        if label:
            t += (f'<text x="10" y="{y - 8}" fill="{GUIDE}" opacity="0.85" '
                  f'font-family="inherit" font-size="24" '
                  f'letter-spacing="2">{label}</text>')
        return t

    guides = [
        hline(100, "CAP 700", strong=True),
        hline(88, "", dashed=True),
        hline(260, "X-HEIGHT 540"),
        hline(800, "BASELINE 0", strong=True),
        hline(812, "", dashed=True),
    ]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {top} {w} '
        f'{bot - top}" style="width:100%;height:auto;display:block">'
        + "".join(guides) + "".join(parts) + "</svg>"
    )


def string_svg(text, gs, y0=60, h=790):
    """Compose a test string at true advance widths."""
    by_name = {g.name: g for g in gs}
    x = 30
    parts = []
    for ch in text:
        if ch == " ":
            x += G.SPACE["advanceWidth"]
            continue
        g = by_name.get(ch)
        if g is None:
            continue
        parts.append(_glyph_path_tag(g, x))
        x += g.adv
    w = x + 30
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {y0} {w} {h}" '
        f'style="width:auto;height:100%;display:block">'
        + "".join(parts) + "</svg>"
    )


def detail_svg(g, fx0, fy0, fx1, fy1, hx0, hy0, hx1, hy1):
    """Crop of one glyph in font coords, with a dashed highlight box."""
    vx = fx0 + g.lsb
    vy = BASELINE_SVG - fy1
    vw, vh = fx1 - fx0, fy1 - fy0
    d = glyph_svg_d(g.contours, lsb=g.lsb)
    rx, ry = hx0 + g.lsb, BASELINE_SVG - hy1
    rw, rh = hx1 - hx0, hy1 - hy0
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vx} {vy} {vw} {vh}" '
        f'style="width:100%;height:auto;display:block">'
        f'<path d="{d}" fill="{INK}"/>'
        f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="none" '
        f'stroke="{GUIDE}" stroke-width="6" stroke-dasharray="14 10" '
        f'opacity="0.9"/></svg>'
    )


def load_woff2_b64():
    p = os.path.join(ROOT, "dist", "KOPAR-Regular.woff2")
    if not os.path.exists(p):
        return None
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


PAGE = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KOPAR — Stage 3 · Lowercase</title>
<style>
  :root { color-scheme: dark; }
  html, body { background: %BG%; }
  body {
    margin: 0; color: #C7D3E8;
    font-family: ui-monospace, "SF Mono", "Cascadia Mono", "JetBrains Mono",
      Menlo, Consolas, monospace;
    font-size: 14px; line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }
  .wrap { max-width: 1180px; margin: 0 auto; padding: 40px 28px 90px; }
  .eyebrow {
    color: %GUIDE%; font-size: 11px; letter-spacing: 0.28em;
    text-transform: uppercase; opacity: 0.9;
  }
  h1 {
    color: %INK%; font-size: 30px; letter-spacing: 0.06em;
    margin: 6px 0 4px; font-weight: 600;
  }
  .sub { color: #5E6E88; max-width: 68ch; }
  section { border-top: 1px solid #17202E; margin-top: 52px; padding-top: 26px; }
  section > .eyebrow { display: block; margin-bottom: 18px; }
  .grouplabel { color: #5E6E88; font-size: 11px; letter-spacing: 0.22em;
    text-transform: uppercase; margin: 16px 0 8px; }
  .panel { background: #0D1320; border: 1px solid #17202E; border-radius: 4px; }
  .hero { padding: 8px 6px; }
  .rows { display: flex; flex-direction: column; gap: 14px; }
  .row { height: 104px; padding: 10px 8px; overflow-x: auto; }
  .row.small { height: 62px; }
  .details { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
  @media (max-width: 900px) { .details { grid-template-columns: repeat(2, 1fr); } }
  .detail { padding: 14px; }
  .detail .cap { margin-top: 10px; color: #5E6E88; font-size: 12px; }
  .detail .cap b { color: %INK%; font-weight: 600; }
  table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }
  th, td { text-align: left; padding: 6px 14px 6px 0; border-bottom: 1px solid #141C29; }
  th { color: #5E6E88; font-weight: 400; font-size: 11px;
       letter-spacing: 0.18em; text-transform: uppercase; }
  td { color: #C7D3E8; }
  td.g { color: %INK%; }
  .live { font-family: "KOPAR", monospace; color: %INK%; }
  .live-row { padding: 14px 16px; overflow-x: auto; white-space: nowrap; }
  .edit { outline: none; border: 1px dashed #23405A; border-radius: 4px; }
  .edit:focus { border-color: %GUIDE%; }
  .note { color: #5E6E88; font-size: 12px; margin-top: 8px; }
  .foot { color: #45526A; font-size: 12px; margin-top: 60px;
          border-top: 1px solid #17202E; padding-top: 18px; }
  %FONTFACE%
</style>
<div class="wrap">
  <header>
    <span class="eyebrow">KOPAR · geometric display · stage 3 of 6</span>
    <h1>Lowercase complete — a to z</h1>
    <p class="sub">22 new glyphs derived from the n / o controls. Circuit
    notches at every spec'd bowl-stem weld (b d p q m h u), 45° terminal
    cuts on t r f s, flat-cut vertexes on v w x y, square dots on i j,
    single-story g. Guides: baseline, x-height, cap, dashed = overshoot.</p>
  </header>

  <section>
    <span class="eyebrow">Lowercase by derivation group</span>
    <div class="grouplabel">From n — m h u r</div>
    <div class="panel hero">%HERO_R%</div>
    <div class="grouplabel">From o — b d p q c e</div>
    <div class="panel hero">%HERO_S%</div>
    <div class="grouplabel">Verticals &amp; cuts — i j l t f k</div>
    <div class="panel hero">%HERO_D%</div>
    <div class="grouplabel">Diagonals &amp; spine — v w x y z s g</div>
    <div class="panel hero">%HERO_C%</div>
  </section>

  <section>
    <span class="eyebrow">Rhythm — true advance widths, no kerning</span>
    <div class="rows">
      <div class="panel row">%ROW1%</div>
      <div class="panel row">%ROW2%</div>
      <div class="panel row small">%ROW3%</div>
      <div class="panel row small">%ROW4%</div>
    </div>
  </section>

  <section>
    <span class="eyebrow">Signature moves, stage 2</span>
    <div class="details">
      <div class="panel detail">%DET1%
        <div class="cap"><b>Weld notch</b> — b, 40×22u step at the upper weld</div></div>
      <div class="panel detail">%DET2%
        <div class="cap"><b>Terminal cuts</b> — s, 45° on both ends</div></div>
      <div class="panel detail">%DET3%
        <div class="cap"><b>Double notch</b> — m, both shoulder welds</div></div>
      <div class="panel detail">%DET4%
        <div class="cap"><b>Squared hook</b> — g, single-story descender</div></div>
    </div>
  </section>

  %LIVE%

  <section>
    <span class="eyebrow">Numbers</span>
    <div style="overflow-x:auto">
    <table>
      <tr><th>glyph</th><th>unicode</th><th>advance</th><th>lsb</th>
          <th>rsb</th><th>ink width</th></tr>
      %TABLE%
    </table>
    </div>
    <p class="note">Sidebearings remain provisional until stage 5 (Tracy
    method). Q's negative rsb is the tail crossing its advance — intended.</p>
  </section>

  <div class="foot">KOPAR working specimen · stage 3 rendered from the same
  SVG + metrics data that build.py compiles · next: stage 4, figures 0-9
  (tabular, slashed zero) + punctuation + currency</div>
</div>
"""

LIVE_TMPL = """<section>
    <span class="eyebrow">Live font — compiled KOPAR-Regular.woff2, real browser shaping</span>
    <div class="rows">
      <div class="panel live-row live" style="font-size:110px">%T1%</div>
      <div class="panel live-row live" style="font-size:44px">%T2%</div>
      <div class="panel live-row live" style="font-size:34px">%T3%</div>
      <div class="panel live-row live edit" contenteditable="true"
           spellcheck="false" style="font-size:64px">%T4%</div>
    </div>
    <p class="note">Full A-Z + a-z + space exist — the last line is editable;
    figures and punctuation arrive in stage 4.</p>
  </section>"""


def build_page(gs):
    by = {g.name: g for g in gs}

    def pick(names):
        return [by[n] for n in names]

    hero_r = guide_row_svg(pick(["n", "m", "h", "u", "r"]))
    hero_s = guide_row_svg(pick(["o", "b", "d", "p", "q", "c", "e"]), track=36)
    hero_d = guide_row_svg(pick(["i", "j", "l", "t", "f", "k"]))
    hero_c = guide_row_svg(pick(["v", "w", "x", "y", "z", "s", "g"]), track=36)

    row1 = string_svg("hamburgefontsiv", gs)
    row2 = string_svg("abcdefghijklmnopqrstuvwxyz", gs)
    row3 = string_svg("the quick brown fox jumps over the lazy dog", gs)
    row4 = string_svg("Sphinx of black quartz judge my vow", gs)

    b_, s_, m_, g_ = by["b"], by["s"], by["m"], by["g"]
    det1 = detail_svg(b_, 40, 340, 340, 640, 88, 448, 180, 518)
    det2 = detail_svg(s_, 220, 360, 480, 600, 320, 474, 412, 566)
    det3 = detail_svg(m_, 300, 300, 620, 600, 422, 436, 514, 506)
    det4 = detail_svg(g_, 60, -230, 460, 90, 126, -214, 340, -82)

    rows = []
    for g in gs:
        rows.append(
            f"<tr><td class=g>{g.name}</td><td>{g.unicode}</td>"
            f"<td>{g.adv}</td><td>{g.lsb}</td><td>{g.rsb}</td>"
            f"<td>{g.ink_w}</td></tr>"
        )

    b64 = load_woff2_b64()
    if b64:
        ff = ('@font-face { font-family: "KOPAR"; '
              f'src: url(data:font/woff2;base64,{b64}) format("woff2"); }}')
        live = (LIVE_TMPL
                .replace("%T1%", "hamburgefontsiv")
                .replace("%T2%", "Sphinx of black quartz judge my vow")
                .replace("%T3%", "the quick brown fox jumps over the lazy dog")
                .replace("%T4%", "Kopar Night Runner"))
    else:
        ff = ""
        live = ""

    page = (PAGE
            .replace("%BG%", BG).replace("%INK%", INK).replace("%GUIDE%", GUIDE)
            .replace("%FONTFACE%", ff)
            .replace("%HERO_R%", hero_r).replace("%HERO_S%", hero_s)
            .replace("%HERO_D%", hero_d).replace("%HERO_C%", hero_c)
            .replace("%ROW1%", row1).replace("%ROW2%", row2)
            .replace("%ROW3%", row3).replace("%ROW4%", row4)
            .replace("%DET1%", det1).replace("%DET2%", det2)
            .replace("%DET3%", det3).replace("%DET4%", det4)
            .replace("%TABLE%", "".join(rows))
            .replace("%LIVE%", live))
    outdir = os.path.join(ROOT, "specimen")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"stage{STAGE}.html")
    with open(path, "w") as f:
        f.write(page)
    return path


def main():
    gs = G.stage3()
    svgdir = write_glyph_svgs(gs)
    mpath = write_metrics(gs)
    spath = build_page(gs)
    print(f"{len(gs)} glyphs")
    print(f"svgs -> {svgdir}\nmetrics -> {mpath}\nspecimen -> {spath}")


if __name__ == "__main__":
    main()
