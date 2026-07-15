"""KOPAR generator.

Emits, for every glyph defined so far:
  kopar/glyphs/U+XXXX_name.svg   (deliverable: single filled path)
  kopar/metrics.json             (deliverable: global metrics + per-glyph + kerning)
  kopar/specimen/stageN.html     (live dark specimen for review)

Run:  python3 tools/generate.py  (from kopar/) or from anywhere.
"""

import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                  # kopar/
sys.path.insert(0, HERE)

from geometry import glyph_svg_d, ink_bbox, BASELINE_SVG  # noqa: E402
import glyphs as G  # noqa: E402

STAGE = 1
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


def hero_svg(gs):
    """Control glyphs on shared metrics with cyan guides."""
    track = 44
    pad_l, pad_r = 148, 40
    x = pad_l
    parts = []
    for g in gs:
        parts.append(_glyph_path_tag(g, x))
        x += g.adv + track
    w = x - track + pad_r
    top, bot = 30, 1050

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
        hline(88, "", dashed=True),                    # cap overshoot
        hline(260, "X-HEIGHT 540"),
        hline(800, "BASELINE 0", strong=True),
        hline(812, "", dashed=True),                   # baseline overshoot
    ]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {top} {w} '
        f'{bot - top}" style="width:100%;height:auto;display:block">'
        + "".join(guides) + "".join(parts) + "</svg>"
    )


def string_svg(text, gs, scale_note=""):
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
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 60 {w} 790" '
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
<title>KOPAR — Stage 1 · Control Letters</title>
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
  .panel { background: #0D1320; border: 1px solid #17202E; border-radius: 4px; }
  .hero { padding: 8px 6px; }
  .rows { display: flex; flex-direction: column; gap: 14px; }
  .row { height: 108px; padding: 10px 8px; overflow-x: auto; }
  .row.small { height: 64px; }
  .row.tiny { height: 40px; }
  .details { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
  @media (max-width: 900px) { .details { grid-template-columns: repeat(2, 1fr); } }
  .detail { padding: 14px; }
  .detail .cap { margin-top: 10px; color: #5E6E88; font-size: 12px; }
  .detail .cap b { color: %INK%; font-weight: 600; }
  table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }
  th, td { text-align: left; padding: 7px 14px 7px 0; border-bottom: 1px solid #141C29; }
  th { color: #5E6E88; font-weight: 400; font-size: 11px;
       letter-spacing: 0.18em; text-transform: uppercase; }
  td { color: #C7D3E8; }
  td.g { color: %INK%; }
  .vals { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 10px 26px; margin-top: 6px; }
  .vals div { border-left: 2px solid #1B2636; padding-left: 10px; }
  .vals b { color: %INK%; font-weight: 600; display: block; }
  .vals span { color: #5E6E88; font-size: 12px; }
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
    <span class="eyebrow">KOPAR · geometric display · stage 1 of 6</span>
    <h1>Control letters — O H E n o a</h1>
    <p class="sub">These six lock proportion, corner language and rhythm for
    the full set. Squared superellipse rounds, 45° terminal cuts on E,
    circuit notches at the n and a welds. Guides: baseline, x-height 540,
    cap 700, dashed = 12u overshoot.</p>
  </header>

  <section>
    <span class="eyebrow">Controls on the grid</span>
    <div class="panel hero">%HERO%</div>
  </section>

  <section>
    <span class="eyebrow">Rhythm — true advance widths, no kerning</span>
    <div class="rows">
      <div class="panel row">%ROW1%</div>
      <div class="panel row">%ROW2%</div>
      <div class="panel row small">%ROW3%</div>
      <div class="panel row tiny">%ROW4%</div>
    </div>
  </section>

  <section>
    <span class="eyebrow">Signature moves</span>
    <div class="details">
      <div class="panel detail">%DET1%
        <div class="cap"><b>45° cut</b> — E arm terminals, 40u legs</div></div>
      <div class="panel detail">%DET2%
        <div class="cap"><b>Circuit notch</b> — n shoulder weld, 40×22u</div></div>
      <div class="panel detail">%DET3%
        <div class="cap"><b>Circuit notch</b> — a waist weld + 12u foot bevel</div></div>
      <div class="panel detail">%DET4%
        <div class="cap"><b>Superellipse</b> — O corner, k 0.82 out / 0.86 in</div></div>
    </div>
  </section>

  %LIVE%

  <section>
    <span class="eyebrow">Numbers</span>
    <div class="vals">
      <div><b>1000</b><span>UPM</span></div>
      <div><b>700 / 540</b><span>cap / x-height</span></div>
      <div><b>92 / 84</b><span>stem / horizontal</span></div>
      <div><b>100 – 80</b><span>curve max – min</span></div>
      <div><b>12</b><span>overshoot, rounds</span></div>
      <div><b>+16</b><span>bar lift above center</span></div>
      <div><b>40</b><span>terminal cut leg</span></div>
      <div><b>40 × 22</b><span>circuit notch</span></div>
    </div>
    <div style="height:26px"></div>
    <div style="overflow-x:auto">
    <table>
      <tr><th>glyph</th><th>unicode</th><th>advance</th><th>lsb</th>
          <th>rsb</th><th>ink width</th></tr>
      %TABLE%
    </table>
    </div>
    <p class="note">Sidebearings are provisional scaffolding — real spacing is
    stage 5 (Tracy method). Space advance 260, provisional.</p>
  </section>

  <div class="foot">KOPAR working specimen · stage 1 rendered from the same
  SVG + metrics data that build.py compiles · next: stage 2, uppercase by
  group (rounds C G Q D S · squares I L F T · diagonals A V W X Y ·
  combos B P R M N K U J Z)</div>
</div>
"""

LIVE_TMPL = """<section>
    <span class="eyebrow">Live font — compiled KOPAR-Regular.woff2, real browser shaping</span>
    <div class="rows">
      <div class="panel live-row live" style="font-size:96px">%T1%</div>
      <div class="panel live-row live" style="font-size:40px">%T2%</div>
      <div class="panel live-row live edit" contenteditable="true"
           spellcheck="false" style="font-size:64px">%T3%</div>
    </div>
    <p class="note">Only H E O n o a + space exist yet — the last line is
    editable, other characters fall back to mono.</p>
  </section>"""


def build_page(gs):
    by = {g.name: g for g in gs}
    hero = hero_svg([by[n] for n in ["O", "H", "E", "n", "o", "a"]])
    row1 = string_svg("HOHOEHOE", gs)
    row2 = string_svg("nano anon oona", gs)
    row3 = string_svg("HEona Hoan onEO OHa", gs)
    row4 = string_svg("noon anon HOE EHO nano", gs)

    E, n_, a_, O_ = by["E"], by["n"], by["a"], by["O"]
    det1 = detail_svg(E, 220, 480, 560, 760, 404, 640, 484, 712)
    det2 = detail_svg(n_, -30, 300, 310, 600, 78, 446, 190, 496)
    det3 = detail_svg(a_, 150, -25, 490, 430, 344, 304, 412, 354)
    det4 = detail_svg(O_, 330, 420, 670, 760, 380, 500, 634, 726)

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
                .replace("%T1%", "HOnE anEO")
                .replace("%T2%", "nano oona anon HOEH OEHO")
                .replace("%T3%", "Hana noEH"))
    else:
        ff = ""
        live = ""

    page = (PAGE
            .replace("%BG%", BG).replace("%INK%", INK).replace("%GUIDE%", GUIDE)
            .replace("%FONTFACE%", ff)
            .replace("%HERO%", hero)
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
    gs = G.stage1()
    svgdir = write_glyph_svgs(gs)
    mpath = write_metrics(gs)
    spath = build_page(gs)
    for g in gs:
        x0, y0, x1, y1 = ink_bbox(g.contours)
        print(f"  {g.name}: ink {x1 - x0}x{y1 - y0}  adv {g.adv} "
              f"lsb {g.lsb} rsb {g.rsb}")
    print(f"svgs -> {svgdir}\nmetrics -> {mpath}\nspecimen -> {spath}")


if __name__ == "__main__":
    main()
