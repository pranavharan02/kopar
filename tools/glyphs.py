"""KOPAR glyph definitions.

Stage 1: control letters O H E n o a.

Everything is defined ink-relative (ink left edge at x=0) in font space
(y-up, baseline 0); generate.py shifts by lsb on emission.

Signature moves:
  1. 45-degree corner cuts (CUT x CUT chamfers) on selected terminals.
  2. Flat-cut apexes/vertexes (stage 2).
  3. Rectangular circuit notches (NOTCH_W x NOTCH_D) cut into the
     bowl-side member at every bowl->stem weld, flush to the weld corner.
"""

# ---------------------------------------------------------------- grid
UPM = 1000
CAP = 700
XH = 540
ASC = 720
DESC = -190
OVER = 12          # overshoot for rounds and cut apexes

STEM = 92          # vertical stems
HORIZ = 84         # horizontal strokes (thinned vs stems)
CURVE_MAX = 100    # curve stroke at thickest (sides of bowls)
CURVE_MIN = 80     # curve stroke at thinnest (tops/bottoms of bowls)

CUT = 40           # 45-degree terminal chamfer leg length
NOTCH_W = 40       # circuit notch: length along the weld
NOTCH_D = 22       # circuit notch: depth into the stroke

K_OUT = 0.82       # superellipse tension, outer contours
K_IN = 0.86        # superellipse tension, counters

BAR_RAISE = 16     # crossbar centers sit this far above math center
BAR_LO = 350 + BAR_RAISE - HORIZ // 2   # 324
BAR_HI = BAR_LO + HORIZ                 # 408


class Glyph:
    def __init__(self, name, unicode_, adv, lsb, contours, note=""):
        self.name = name
        self.unicode = unicode_          # e.g. "U+0048"
        self.adv = adv
        self.lsb = lsb
        self.contours = contours         # [(verts, is_outer, k_default)]
        self.note = note

    @property
    def ink_w(self):
        from geometry import ink_bbox
        x0, _, x1, _ = ink_bbox(self.contours)
        return x1 - x0

    @property
    def rsb(self):
        return self.adv - self.lsb - self.ink_w


def _rect_ring(x0, y0, x1, y1, r, k):
    """Rounded rect as a vertex ring (same radius on all four corners)."""
    return [(x0, y0, r, k), (x1, y0, r, k), (x1, y1, r, k), (x0, y1, r, k)]


# ------------------------------------------------------------- controls

def glyph_H():
    w = 584
    v = [
        (0, 0), (STEM, 0), (STEM, BAR_LO), (w - STEM, BAR_LO),
        (w - STEM, 0), (w, 0), (w, CAP), (w - STEM, CAP),
        (w - STEM, BAR_HI), (STEM, BAR_HI), (STEM, CAP), (0, CAP),
    ]
    return Glyph("H", "U+0048", 760, 88, [(v, True, K_OUT)],
                 "pure control: stems 92, bar 84 centered +16 above middle")


def glyph_E():
    arm_bot = 478    # lower story widest
    arm_top = 466
    arm_mid = 440
    v = [
        (0, 0),
        (arm_bot - CUT, 0), (arm_bot, CUT),                # 45-deg cut, bottom arm
        (arm_bot, HORIZ), (STEM, HORIZ),
        (STEM, BAR_LO), (arm_mid, BAR_LO),
        (arm_mid, BAR_HI - CUT), (arm_mid - CUT, BAR_HI),  # 45-deg cut, middle arm
        (STEM, BAR_HI),
        (STEM, CAP - HORIZ), (arm_top, CAP - HORIZ),
        (arm_top, CAP - CUT), (arm_top - CUT, CAP),        # 45-deg cut, top arm
        (0, CAP),
    ]
    return Glyph("E", "U+0045", 630, 88, [(v, True, K_OUT)],
                 "three arm terminals carry the 45-deg corner cut")


def glyph_O():
    w = 620
    outer = _rect_ring(0, -OVER, w, CAP + OVER, 210, K_OUT)
    inner = _rect_ring(CURVE_MAX, -OVER + CURVE_MIN,
                       w - CURVE_MAX, CAP + OVER - CURVE_MIN, 128, K_IN)
    return Glyph("O", "U+004F", 740, 60,
                 [(outer, True, K_OUT), (inner, False, K_IN)],
                 "squared superellipse: sides 100, top/bottom 80, overshoot 12")


def glyph_o():
    w = 496
    outer = _rect_ring(0, -OVER, w, XH + OVER, 150, K_OUT)
    inner = _rect_ring(CURVE_MAX, -OVER + CURVE_MIN,
                       w - CURVE_MAX, XH + OVER - CURVE_MIN, 66, K_IN)
    return Glyph("o", "U+006F", 608, 56,
                 [(outer, True, K_OUT), (inner, False, K_IN)])


def glyph_n():
    w = 490
    ceil_ = XH - CURVE_MIN               # 460, counter ceiling
    v = [
        (0, 0), (STEM, 0),
        # up the counter's left wall, into the circuit notch at the weld
        (STEM, ceil_ + NOTCH_D),
        (STEM + NOTCH_W, ceil_ + NOTCH_D),
        (STEM + NOTCH_W, ceil_),
        (w - STEM, ceil_, 85, K_IN),     # counter's squared shoulder
        (w - STEM, 0), (w, 0),
        (w, XH, 170, K_OUT),             # outer squared shoulder
        (0, XH, 30, K_OUT),              # eased square at stem top
    ]
    return Glyph("n", "U+006E", 658, 84, [(v, True, K_OUT)],
                 "arch flat-top sits on x-height (not a round); "
                 "notch at shoulder-stem weld")


def glyph_a():
    w = 490
    stem_l = w - STEM                    # 398, stem left edge
    eye_top = 260                        # eye ceiling = waist underside
    waist_top = eye_top + CURVE_MIN      # 340, aperture floor
    cap_under = XH + OVER - CURVE_MIN    # 472, top cap underside
    tab_x = 120                          # hook tab outer edge
    tab_w = 94                           # hook tab thickness
    tab_end = 430                        # hook tab terminal
    outer = [
        (tab_x, XH + OVER, 90, K_OUT),   # squared top-left of cap
        (w, XH + OVER, 90, K_OUT),       # cap rounds into stem outer
        (w, 0),
        (stem_l + OVER, 0), (stem_l, -OVER),   # 12x12 bevel: foot -> bowl overshoot
        (0, -OVER, 110, K_OUT),
        (0, waist_top, 44, K_OUT),       # bowl left rises to aperture floor
        (stem_l - NOTCH_W, waist_top),
        (stem_l - NOTCH_W, waist_top - NOTCH_D),
        (stem_l, waist_top - NOTCH_D),   # circuit notch at waist-stem weld
        (stem_l, cap_under, 24, K_IN),
        (tab_x + tab_w, cap_under, 24, K_IN),
        (tab_x + tab_w, tab_end),
        (tab_x, tab_end),                # flat-cut hook terminal
    ]
    eye = _rect_ring(CURVE_MAX, -OVER + CURVE_MIN, stem_l, eye_top, 44, K_IN)
    # eye ceiling corners tighter than its floor: rebuild with split radii
    eye = [
        (CURVE_MAX, -OVER + CURVE_MIN, 56, K_IN),
        (stem_l, -OVER + CURVE_MIN, 56, K_IN),
        (stem_l, eye_top, 30, K_IN),
        (CURVE_MAX, eye_top, 30, K_IN),
    ]
    return Glyph("a", "U+0061", 642, 68,
                 [(outer, True, K_OUT), (eye, False, K_IN)],
                 "double-story; squared L-hook; notch at waist-stem weld")


def stage1():
    return [glyph_O(), glyph_H(), glyph_E(),
            glyph_n(), glyph_o(), glyph_a()]


# Space: metrics-only entry (no ink, no SVG file)
SPACE = {"unicode": "U+0020", "name": "space", "advanceWidth": 260,
         "lsb": 0, "rsb": 0}
