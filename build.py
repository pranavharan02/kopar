#!/usr/bin/env python3
"""Compile KOPAR from glyph SVGs + metrics.json.

Ingests:
  glyphs/U+XXXX_name.svg   one filled path per glyph, viewBox 1000 tall,
                           baseline at y=800 (cap 700 spans y=100..800)
  metrics.json             global metrics, per-glyph advances/sidebearings,
                           kerning table {"A,V": -40, ...}

Produces:
  dist/KOPAR-Regular.otf
  dist/KOPAR-Regular.ttf
  dist/KOPAR-Regular.woff2

Conventions the SVGs follow (enforced by tools/generate.py):
  - absolute M/L/C/Z commands only, integer coordinates
  - outer contours clockwise in SVG space (= CCW in font space after the
    y-flip), counters the other way

Usage: python3 build.py [project_dir]
"""

import json
import os
import re
import sys

from fontTools.fontBuilder import FontBuilder
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path

FAMILY = "KOPAR"
STYLE = "Regular"
VERSION = "0.100"

# SVG y-down with baseline at 800  ->  font y-up with baseline at 0
SVG_TO_FONT = Transform(1, 0, 0, -1, 0, 800)


def read_svg_paths(svg_file):
    with open(svg_file) as f:
        text = f.read()
    ds = re.findall(r'\bd="([^"]+)"', text)
    if not ds:
        raise ValueError(f"no path data in {svg_file}")
    return " ".join(ds)


def record_glyph(d):
    """Parse SVG path -> RecordingPen in font space (y-up)."""
    rec = RecordingPen()
    parse_path(d, TransformPen(rec, SVG_TO_FONT))
    return rec


def glyph_bounds(rec):
    bp = BoundsPen(None)
    rec.replay(bp)
    return bp.bounds  # None for empty


def notdef_recording(upm, cap):
    """Simple open box .notdef."""
    rec = RecordingPen()
    w, m, s = 500, 60, 50
    outer = [(m, 0), (w - m, 0), (w - m, cap), (m, cap)]
    inner = [(m + s, s), (m + s, cap - s), (w - m - s, cap - s), (w - m - s, s)]
    for ring in (outer, inner):
        rec.moveTo(ring[0])
        for p in ring[1:]:
            rec.lineTo(p)
        rec.closePath()
    return rec


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                           os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "metrics.json")) as f:
        metrics = json.load(f)

    upm = metrics["upm"]
    svgdir = os.path.join(root, "glyphs")
    dist = os.path.join(root, "dist")
    os.makedirs(dist, exist_ok=True)

    # ---------------------------------------------------------- collect
    glyph_entries = sorted(metrics["glyphs"], key=lambda e: e["unicode"])
    recordings = {}      # glyph name -> RecordingPen (font space)
    advances = {}        # glyph name -> advance
    cmap = {}

    recordings[".notdef"] = notdef_recording(upm, metrics["capHeight"])
    advances[".notdef"] = 500

    for e in glyph_entries:
        name = e["name"]
        cp = int(e["unicode"][2:], 16)
        cmap[cp] = name
        advances[name] = e["advanceWidth"]
        svg = os.path.join(svgdir, f'{e["unicode"]}_{name}.svg')
        if os.path.exists(svg):
            recordings[name] = record_glyph(read_svg_paths(svg))
        else:
            recordings[name] = RecordingPen()   # e.g. space

    order = [".notdef"] + [e["name"] for e in glyph_entries]

    # vertical metrics
    asc, desc = metrics["ascender"], metrics["descender"]
    ink_top, ink_bot = asc, desc
    for rec in recordings.values():
        b = glyph_bounds(rec)
        if b:
            ink_bot = min(ink_bot, b[1])
            ink_top = max(ink_top, b[3])
    win_asc = int(max(asc, ink_top))
    win_desc = int(abs(min(desc, ink_bot)))

    def build(is_ttf):
        fb = FontBuilder(upm, isTTF=is_ttf)
        fb.setupGlyphOrder(order)
        fb.setupCharacterMap(cmap)

        hmtx = {}
        if is_ttf:
            glyf = {}
            for name in order:
                pen = TTGlyphPen(None)
                q = Cu2QuPen(pen, max_err=1.0, reverse_direction=True)
                recordings[name].replay(q)
                glyf[name] = pen.glyph()
            fb.setupGlyf(glyf)
            for name in order:
                b = glyph_bounds(recordings[name])
                hmtx[name] = (advances[name], int(b[0]) if b else 0)
        else:
            charstrings = {}
            for name in order:
                pen = T2CharStringPen(advances[name], None)
                recordings[name].replay(pen)
                charstrings[name] = pen.getCharString()
            fb.setupCFF(
                f"{FAMILY}-{STYLE}",
                {"FullName": f"{FAMILY} {STYLE}", "FamilyName": FAMILY,
                 "Weight": STYLE},
                charstrings, {})
            for name in order:
                b = glyph_bounds(recordings[name])
                hmtx[name] = (advances[name], int(b[0]) if b else 0)

        fb.setupHorizontalMetrics(hmtx)
        fb.setupHorizontalHeader(ascent=win_asc, descent=-win_desc)
        fb.setupNameTable({
            "familyName": FAMILY,
            "styleName": STYLE,
            "uniqueFontIdentifier": f"{VERSION};{FAMILY}-{STYLE}",
            "fullName": f"{FAMILY} {STYLE}",
            "psName": f"{FAMILY}-{STYLE}",
            "version": f"Version {VERSION}",
        })
        fb.setupOS2(
            sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=180,
            usWinAscent=win_asc, usWinDescent=win_desc,
            sxHeight=metrics["xHeight"], sCapHeight=metrics["capHeight"],
            achVendID="KPAR",
        )
        fb.setupPost()

        kerning = metrics.get("kerning") or {}
        pairs = {tuple(k.split(",")): v for k, v in kerning.items()
                 if all(n.strip() in set(order) for n in k.split(","))}
        if pairs:
            rules = "\n".join(
                f"    pos {l.strip()} {r.strip()} {v};"
                for (l, r), v in sorted(pairs.items()))
            fea = ("languagesystem DFLT dflt;\nlanguagesystem latn dflt;\n"
                   f"feature kern {{\n{rules}\n}} kern;\n")
            from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
            addOpenTypeFeaturesFromString(fb.font, fea)
        return fb.font

    otf = build(is_ttf=False)
    otf.save(os.path.join(dist, f"{FAMILY}-{STYLE}.otf"))

    ttf = build(is_ttf=True)
    ttf.save(os.path.join(dist, f"{FAMILY}-{STYLE}.ttf"))

    ttf.flavor = "woff2"
    ttf.save(os.path.join(dist, f"{FAMILY}-{STYLE}.woff2"))

    n = len(order)
    print(f"compiled {n} glyphs -> {dist}/{FAMILY}-{STYLE}"
          ".otf/.ttf/.woff2")


if __name__ == "__main__":
    main()
