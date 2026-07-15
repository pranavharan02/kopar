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


# ---------------------------------------------------------- stage 2: caps
# Rounds C G Q D S · squares I L F T · diagonals A V W X Y ·
# combos B P R M N K U J Z. All coordinates hand-derived on the grid;
# diagonals carry flat-cut apexes/vertexes (signature move 2).

def glyph_C():
    # O opened right: mouth y 230..470, flat horizontal terminals
    v = [
        (620, 470), (620, CAP + OVER, 210), (0, CAP + OVER, 210),
        (0, -OVER, 210), (620, -OVER, 210), (620, 230),
        (520, 230), (520, 68, 128, K_IN), (100, 68, 128, K_IN),
        (100, 632, 128, K_IN), (520, 632, 128, K_IN), (520, 470),
    ]
    return Glyph("C", "U+0043", 740, 60, [(v, True, K_OUT)])


def glyph_G():
    # C + crossbar jutting into the counter, solid jaw below
    v = [
        (620, 470), (620, CAP + OVER, 210), (0, CAP + OVER, 210),
        (0, -OVER, 210), (620, -OVER, 210), (620, 394),
        (356, 394), (356, 310), (520, 310),
        (520, 68, 128, K_IN), (100, 68, 128, K_IN),
        (100, 632, 128, K_IN), (520, 632, 128, K_IN), (520, 470),
    ]
    return Glyph("G", "U+0047", 740, 60, [(v, True, K_OUT)])


def glyph_Q():
    # O with the bottom-right corner sheared out 95u along 45 degrees
    outer = [
        (0, -OVER, 210), (520, -OVER), (615, -107), (715, -7),
        (620, 88), (620, CAP + OVER, 210), (0, CAP + OVER, 210),
    ]
    inner = _rect_ring(100, 68, 520, 632, 128, K_IN)
    return Glyph("Q", "U+0051", 760, 60,
                 [(outer, True, K_OUT), (inner, False, K_IN)],
                 "corner-shear tail, end face parallel to the shear")


def glyph_D():
    outer = [(0, 0), (596, 0, 200), (596, CAP, 200), (0, CAP)]
    inner = [(STEM, HORIZ), (496, HORIZ, 110, K_IN),
             (496, CAP - HORIZ, 110, K_IN), (STEM, CAP - HORIZ)]
    return Glyph("D", "U+0044", 744, 88,
                 [(outer, True, K_OUT), (inner, False, K_IN)],
                 "flat-top round: aligns to cap like n aligns to x-height")


def glyph_S():
    # double hook; upper story inset 14 left + terminal pulled 18 in
    v = [
        (0, 0), (330, 0), (470, 0, 140), (470, 408, 90),
        (110, 408, 40), (110, 616, 40), (452, 616), (452, 700),
        (14, 700, 140), (14, 324, 90), (374, 324, 40),
        (374, 84, 40), (0, 84),
    ]
    return Glyph("S", "U+0053", 594, 62, [(v, True, K_OUT)],
                 "lower story wider; flat vertical terminals")


def glyph_I():
    v = [(0, 0), (STEM, 0), (STEM, CAP), (0, CAP)]
    return Glyph("I", "U+0049", 268, 88, [(v, True, K_OUT)])


def glyph_L():
    v = [(0, 0), (420, 0), (460, CUT), (460, HORIZ),
         (STEM, HORIZ), (STEM, CAP), (0, CAP)]
    return Glyph("L", "U+004C", 604, 88, [(v, True, K_OUT)])


def glyph_F():
    v = [
        (0, 0), (STEM, 0), (STEM, BAR_LO), (440, BAR_LO),
        (440, BAR_HI - CUT), (440 - CUT, BAR_HI), (STEM, BAR_HI),
        (STEM, CAP - HORIZ), (466, CAP - HORIZ),
        (466, CAP - CUT), (466 - CUT, CAP), (0, CAP),
    ]
    return Glyph("F", "U+0046", 620, 88, [(v, True, K_OUT)])


def glyph_T():
    v = [
        (234, 0), (326, 0), (326, CAP - HORIZ), (560, CAP - HORIZ),
        (560, CAP - CUT), (560 - CUT, CAP), (CUT, CAP), (0, CAP - CUT),
        (0, CAP - HORIZ), (234, CAP - HORIZ),
    ]
    return Glyph("T", "U+0054", 640, 40, [(v, True, K_OUT)],
                 "both bar terminals cut at 45 degrees")


def glyph_A():
    # flat-cut apex 130 wide, overshoots to 712; bar low
    outer = [
        (0, 0), (100, 0), (152, 158), (448, 158), (500, 0),
        (600, 0), (365, CAP + OVER), (235, CAP + OVER),
    ]
    counter = [(180, 242), (420, 242), (320, 545), (280, 545)]
    return Glyph("A", "U+0041", 636, 18,
                 [(outer, True, K_OUT), (counter, False, K_IN)],
                 "apex flat-cut + 12u overshoot; counter apex also flat")


def glyph_V():
    v = [
        (0, CAP), (235, -OVER), (365, -OVER), (600, CAP),
        (500, CAP), (320, 155), (280, 155), (100, CAP),
    ]
    return Glyph("V", "U+0056", 636, 18, [(v, True, K_OUT)],
                 "vertex flat-cut + 12u overshoot")


def glyph_W():
    # all six apex/vertex events flat-cut; center peak overshoots
    v = [
        (0, CAP), (162, -OVER), (242, -OVER), (381, 494), (429, 494),
        (568, -OVER), (648, -OVER), (810, CAP), (714, CAP),
        (614, 259), (566, 259), (441, CAP + OVER), (369, CAP + OVER),
        (244, 259), (196, 259), (96, CAP),
    ]
    return Glyph("W", "U+0057", 842, 16, [(v, True, K_OUT)])


def glyph_X():
    v = [
        (0, 0), (104, 0), (280, 270), (456, 0), (560, 0),
        (332, 350), (560, CAP), (456, CAP), (280, 430),
        (104, CAP), (0, CAP), (228, 350),
    ]
    return Glyph("X", "U+0058", 600, 20, [(v, True, K_OUT)])


def glyph_Y():
    v = [
        (234, 0), (326, 0), (326, 274), (560, CAP), (456, CAP),
        (280, 380), (104, CAP), (0, CAP), (234, 274),
    ]
    return Glyph("Y", "U+0059", 600, 20, [(v, True, K_OUT)])


def glyph_B():
    # two bowls, lower 30u wider; waist notch bitten into the right face
    outer = [
        (0, 0), (470, 0, 125), (470, 324), (440, 324),
        (440, 345), (418, 345), (418, 385), (440, 385),
        (440, CAP, 115), (0, CAP),
    ]
    up = [(STEM, BAR_HI), (340, BAR_HI, 58, K_IN),
          (340, CAP - HORIZ, 58, K_IN), (STEM, CAP - HORIZ)]
    lo = [(STEM, HORIZ), (370, HORIZ, 64, K_IN),
          (370, BAR_LO, 64, K_IN), (STEM, BAR_LO)]
    return Glyph("B", "U+0042", 622, 88,
                 [(outer, True, K_OUT), (up, False, K_IN), (lo, False, K_IN)],
                 "waist notch on the silhouette between the bowls")


def glyph_P():
    outer = [(0, 0), (STEM, 0), (STEM, 280), (460, 280, 110),
             (460, CAP, 115), (0, CAP)]
    inner = [(STEM, 364), (360, 364, 52, K_IN),
             (360, CAP - HORIZ, 52, K_IN), (STEM, CAP - HORIZ)]
    return Glyph("P", "U+0050", 606, 88,
                 [(outer, True, K_OUT), (inner, False, K_IN)])


def glyph_R():
    # bowl + straight leg; waist notch cut up into the bowl underside
    outer = [
        (0, 0), (STEM, 0), (STEM, BAR_LO), (280, BAR_LO),
        (398, 0), (490, 0), (372, BAR_LO), (410, BAR_LO),
        (410, BAR_LO + NOTCH_D), (450, BAR_LO + NOTCH_D),
        (450, CAP, 115), (0, CAP),
    ]
    inner = [(STEM, BAR_HI), (350, BAR_HI, 55, K_IN),
             (350, CAP - HORIZ, 55, K_IN), (STEM, CAP - HORIZ)]
    return Glyph("R", "U+0052", 608, 88,
                 [(outer, True, K_OUT), (inner, False, K_IN)],
                 "leg foot lands wider than the bowl: lower story wider")


def glyph_M():
    # center vertex flat [308,392] at -12; top notch flat-cut at y=145
    v = [
        (0, 0), (STEM, 0), (STEM, 501), (308, -OVER), (392, -OVER),
        (608, 501), (608, 0), (700, 0), (700, CAP), (608, CAP),
        (374, 145), (326, 145), (STEM, CAP), (0, CAP),
    ]
    return Glyph("M", "U+004D", 860, 80, [(v, True, K_OUT)])


def glyph_N():
    # diagonal springs stem-inner y520; both crotch needles flat-cut
    v = [
        (0, 0), (STEM, 0), (STEM, 483), (116, 483), (432, 0),
        (584, 0), (584, CAP), (492, CAP), (492, 131), (464, 131),
        (STEM, CAP), (0, CAP),
    ]
    return Glyph("N", "U+004E", 760, 88, [(v, True, K_OUT)])


def glyph_K():
    # both limbs at exactly 45 degrees; rectangular slot at the waist
    v = [
        (0, 0), (STEM, 0), (STEM, 260), (352, 0), (482, 0),
        (136, 346), (114, 346), (114, 386), (136, 386),
        (450, CAP), (320, CAP), (STEM, 472), (STEM, CAP), (0, CAP),
    ]
    return Glyph("K", "U+004B", 604, 88, [(v, True, K_OUT)],
                 "45-degree limbs echo the terminal-cut angle; waist slot")


def glyph_U():
    v = [
        (0, CAP), (0, 0, 170), (584, 0, 170), (584, CAP),
        (492, CAP), (492, 84, 85, K_IN), (STEM, 84, 85, K_IN),
        (STEM, CAP),
    ]
    return Glyph("U", "U+0055", 760, 88, [(v, True, K_OUT)],
                 "flat-bottom arch, no overshoot (n rule inverted)")


def glyph_J():
    v = [
        (0, 0), (420, 0, 140), (420, CAP), (328, CAP),
        (328, 84, 56, K_IN), (0, 84),
    ]
    return Glyph("J", "U+004A", 564, 56, [(v, True, K_OUT)])


def glyph_Z():
    v = [
        (0, 0), (486, 0), (486, 84), (160, 84), (470, 616),
        (470, CAP), (10, CAP), (10, 616), (318, 616), (8, 84), (0, 84),
    ]
    return Glyph("Z", "U+005A", 606, 60, [(v, True, K_OUT)],
                 "bottom bar 486 vs top 460: lower story wider")


def stage2():
    caps = [glyph_A(), glyph_B(), glyph_C(), glyph_D(), glyph_F(),
            glyph_G(), glyph_I(), glyph_J(), glyph_K(), glyph_L(),
            glyph_M(), glyph_N(), glyph_P(), glyph_Q(), glyph_R(),
            glyph_S(), glyph_T(), glyph_U(), glyph_V(), glyph_W(),
            glyph_X(), glyph_Y(), glyph_Z()]
    return stage1() + caps


# ------------------------------------------------------- stage 3: lowercase
# From n: m h u r · from o: b d p q c e · then i j l t f k v w x y z s g.
# Notches (spec list): b d p q n m h. Terminal cuts (spec list): t r f s.

DOT_LO, DOT_HI = 610, 702      # square dot band for i j


def glyph_m():
    w, mid = 800, 354           # condensed arches: counters 262 vs n's 306
    v = [
        (0, 0), (STEM, 0),
        (STEM, 482), (STEM + NOTCH_W, 482), (STEM + NOTCH_W, 460),
        (mid, 460, 60, K_IN), (mid, 0), (mid + STEM, 0),
        (mid + STEM, 482), (mid + STEM + NOTCH_W, 482),
        (mid + STEM + NOTCH_W, 460),
        (w - STEM, 460, 85, K_IN), (w - STEM, 0), (w, 0),
        (w, XH, 170, K_OUT), (0, XH, 30, K_OUT),
    ]
    return Glyph("m", "U+006D", 968, 84, [(v, True, K_OUT)],
                 "notch at both shoulder welds")


def glyph_h():
    v = [
        (0, 0), (STEM, 0),
        (STEM, 482), (STEM + NOTCH_W, 482), (STEM + NOTCH_W, 460),
        (398, 460, 85, K_IN), (398, 0), (490, 0),
        (490, XH, 170, K_OUT), (STEM, XH), (STEM, ASC), (0, ASC),
    ]
    return Glyph("h", "U+0068", 658, 84, [(v, True, K_OUT)])


def glyph_u():
    v = [
        (0, XH), (0, 0, 170, K_OUT), (490, 0), (490, XH),
        (398, XH), (398, 58), (358, 58), (358, 80),
        (STEM, 80, 85, K_IN), (STEM, XH),
    ]
    return Glyph("u", "U+0075", 658, 84, [(v, True, K_OUT)],
                 "n inverted; notch at the bowl-stem weld, floor side")


def glyph_r():
    v = [
        (0, 0), (STEM, 0), (STEM, 460), (300, 460),
        (300, XH - CUT), (300 - CUT, XH), (0, XH),
    ]
    return Glyph("r", "U+0072", 430, 84, [(v, True, K_OUT)],
                 "45-degree cut on the arm terminal")


def glyph_b():
    outer = [
        (0, 0), (STEM, 0), (104, -OVER),
        (500, -OVER, 140, K_OUT), (500, XH + OVER, 140, K_OUT),
        (STEM, XH + OVER), (STEM, ASC), (0, ASC),
    ]
    inner = [(STEM, 68), (400, 68, 66, K_IN), (400, 472, 66, K_IN),
             (STEM + NOTCH_W, 472), (STEM + NOTCH_W, 494), (STEM, 494)]
    return Glyph("b", "U+0062", 640, 84,
                 [(outer, True, K_OUT), (inner, False, K_IN)],
                 "12u foot bevel; notch at the upper weld")


def glyph_d():
    outer = [
        (0, -OVER, 140, K_OUT), (396, -OVER), (408, 0), (500, 0),
        (500, ASC), (408, ASC), (408, XH + OVER),
        (0, XH + OVER, 140, K_OUT),
    ]
    inner = [(100, 68, 66, K_IN), (408, 68), (408, 494),
             (408 - NOTCH_W, 494), (408 - NOTCH_W, 472),
             (100, 472, 66, K_IN)]
    return Glyph("d", "U+0064", 640, 56,
                 [(outer, True, K_OUT), (inner, False, K_IN)])


def glyph_p():
    outer = [
        (0, DESC), (STEM, DESC), (STEM, -OVER),
        (500, -OVER, 140, K_OUT), (500, XH + OVER, 140, K_OUT),
        (104, XH + OVER), (STEM, XH), (0, XH),
    ]
    inner = [(STEM, 68), (400, 68, 66, K_IN), (400, 472, 66, K_IN),
             (STEM + NOTCH_W, 472), (STEM + NOTCH_W, 494), (STEM, 494)]
    return Glyph("p", "U+0070", 640, 84,
                 [(outer, True, K_OUT), (inner, False, K_IN)],
                 "12u head bevel where bowl overshoot meets stem top")


def glyph_q():
    outer = [
        (0, -OVER, 140, K_OUT), (408, -OVER), (408, DESC), (500, DESC),
        (500, XH), (420, XH), (408, XH + OVER),
        (0, XH + OVER, 140, K_OUT),
    ]
    inner = [(100, 68, 66, K_IN), (408, 68), (408, 494),
             (408 - NOTCH_W, 494), (408 - NOTCH_W, 472),
             (100, 472, 66, K_IN)]
    return Glyph("q", "U+0071", 640, 56,
                 [(outer, True, K_OUT), (inner, False, K_IN)])


def glyph_c():
    v = [
        (496, 386), (496, XH + OVER, 150, K_OUT), (0, XH + OVER, 150, K_OUT),
        (0, -OVER, 150, K_OUT), (496, -OVER, 150, K_OUT), (496, 162),
        (396, 162), (396, 68, 66, K_IN), (100, 68, 66, K_IN),
        (100, 472, 66, K_IN), (396, 472, 66, K_IN), (396, 386),
    ]
    return Glyph("c", "U+0063", 596, 56, [(v, True, K_OUT)])


def glyph_e():
    outer = [
        (0, -OVER, 150, K_OUT), (496, -OVER, 100, K_OUT), (496, 112),
        (396, 112), (396, 68, 44, K_IN), (100, 68, 66, K_IN),
        (100, 296), (496, 296), (496, XH + OVER, 150, K_OUT),
        (0, XH + OVER, 150, K_OUT),
    ]
    upper = [(100, 376), (396, 376), (396, 472, 40, K_IN),
             (100, 472, 40, K_IN)]
    return Glyph("e", "U+0065", 600, 56,
                 [(outer, True, K_OUT), (upper, False, K_IN)],
                 "bar reads through to the right silhouette")


def glyph_i():
    stem = [(0, 0), (STEM, 0), (STEM, XH), (0, XH)]
    dot = [(0, DOT_LO), (STEM, DOT_LO), (STEM, DOT_HI), (0, DOT_HI)]
    return Glyph("i", "U+0069", 268, 88,
                 [(stem, True, K_OUT), (dot, True, K_OUT)],
                 "square dot, 92x92")


def glyph_j():
    hook = [
        (0, DESC), (250, DESC, 110, K_OUT), (250, XH), (158, XH),
        (158, -106, 56, K_IN), (0, -106),
    ]
    dot = [(158, DOT_LO), (250, DOT_LO), (250, DOT_HI), (158, DOT_HI)]
    return Glyph("j", "U+006A", 394, 56,
                 [(hook, True, K_OUT), (dot, True, K_OUT)])


def glyph_l():
    v = [(0, 0), (STEM, 0), (STEM, ASC), (0, ASC)]
    return Glyph("l", "U+006C", 268, 88, [(v, True, K_OUT)])


def glyph_t():
    v = [
        (108, 0), (200, 0), (200, 456), (308, 456), (308, XH),
        (200, XH), (200, 600), (160, 640), (108, 640),
        (108, XH), (0, XH), (0, 456), (108, 456),
    ]
    return Glyph("t", "U+0074", 392, 40, [(v, True, K_OUT)],
                 "45-degree cut on the ascender terminal")


def glyph_f():
    v = [
        (108, 0), (200, 0), (200, 456), (308, 456), (308, XH),
        (200, XH), (200, 636), (336, 636), (336, 680), (296, ASC),
        (108, ASC, 70, K_OUT), (108, XH), (0, XH), (0, 456), (108, 456),
    ]
    return Glyph("f", "U+0066", 410, 40, [(v, True, K_OUT)],
                 "45-degree cut on the hook terminal")


def glyph_k():
    v = [
        (0, 0), (STEM, 0), (STEM, 164), (256, 0), (386, 0),
        (136, 250), (114, 250), (114, 290), (136, 290),
        (386, XH), (256, XH), (STEM, 376), (STEM, ASC), (0, ASC),
    ]
    return Glyph("k", "U+006B", 500, 84, [(v, True, K_OUT)],
                 "45-degree limbs + waist slot, scaled from K")


def glyph_v():
    v = [
        (0, XH), (190, -OVER), (290, -OVER), (480, XH),
        (376, XH), (258, 190), (222, 190), (104, XH),
    ]
    return Glyph("v", "U+0076", 512, 16, [(v, True, K_OUT)])


def glyph_w():
    v = [
        (0, XH), (128, -OVER), (196, -OVER), (310, 390), (350, 390),
        (464, -OVER), (532, -OVER), (660, XH), (572, XH),
        (494, 205), (454, 205), (356, XH + OVER), (304, XH + OVER),
        (206, 205), (166, 205), (88, XH),
    ]
    return Glyph("w", "U+0077", 688, 14, [(v, True, K_OUT)])


def glyph_x():
    v = [
        (0, 0), (96, 0), (235, 201), (374, 0), (470, 0),
        (283, 270), (470, XH), (374, XH), (235, 339),
        (96, XH), (0, XH), (187, 270),
    ]
    return Glyph("x", "U+0078", 506, 18, [(v, True, K_OUT)])


def glyph_y():
    v = [
        (0, XH), (189, -10), (127, DESC), (231, DESC),
        (480, XH), (376, XH), (257, 192), (221, 192), (104, XH),
    ]
    return Glyph("y", "U+0079", 512, 16, [(v, True, K_OUT)],
                 "right stroke runs straight through to the descender")


def glyph_z():
    v = [
        (0, 0), (420, 0), (420, 84), (138, 84), (404, 456),
        (404, XH), (8, XH), (8, 456), (272, 456), (6, 84), (0, 84),
    ]
    return Glyph("z", "U+007A", 524, 52, [(v, True, K_OUT)])


def glyph_s():
    v = [
        (40, 0), (280, 0), (400, 0, 100, K_OUT), (400, 316, 64, K_OUT),
        (102, 316, 30, K_OUT), (102, 460, 30, K_OUT), (386, 460),
        (386, 500), (346, XH), (12, XH, 100, K_OUT),
        (12, 236, 70, K_OUT), (310, 236, 30, K_OUT),
        (310, 80, 30, K_OUT), (0, 80), (0, 40),
    ]
    return Glyph("s", "U+0073", 508, 54, [(v, True, K_OUT)],
                 "45-degree cuts on both terminals")


def glyph_g():
    outer = [
        (0, -OVER, 140, K_OUT), (408, -OVER), (408, -106),
        (150, -106), (150, DESC), (500, DESC, 110, K_OUT),
        (500, XH), (420, XH), (408, XH + OVER),
        (0, XH + OVER, 140, K_OUT),
    ]
    inner = [(100, 68, 66, K_IN), (408, 68), (408, 472),
             (100, 472, 66, K_IN)]
    return Glyph("g", "U+0067", 618, 56,
                 [(outer, True, K_OUT), (inner, False, K_IN)],
                 "single-story; squared hook opening left")


def stage3():
    lc = [glyph_b(), glyph_c(), glyph_d(), glyph_e(), glyph_f(),
          glyph_g(), glyph_h(), glyph_i(), glyph_j(), glyph_k(),
          glyph_l(), glyph_m(), glyph_p(), glyph_q(), glyph_r(),
          glyph_s(), glyph_t(), glyph_u(), glyph_v(), glyph_w(),
          glyph_x(), glyph_y(), glyph_z()]
    return stage2() + lc
