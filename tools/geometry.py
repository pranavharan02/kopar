"""KOPAR geometry kit.

All glyph construction happens in FONT SPACE: y-up, baseline at y=0,
cap height 700, UPM 1000. SVG emission flips to the deliverable
convention: viewBox 1000 units tall, baseline at y=800.

Contours are "rounded polygons": lists of vertices
    (x, y)             sharp corner
    (x, y, r)          corner replaced by a cubic arc, radius r
    (x, y, r, k)       same, with per-vertex tension override

k controls superellipse tension: 0.5523 approximates a circle,
higher values pull the curve toward the corner point (squarer).

Winding is normalized on emission: outer contours are CCW in font
space, counters CW. build.py relies on this convention.
"""

import math

BASELINE_SVG = 800  # font y=0 maps to SVG y=800


def signed_area(verts):
    s = 0.0
    n = len(verts)
    for i in range(n):
        x1, y1 = verts[i][0], verts[i][1]
        x2, y2 = verts[(i + 1) % n][0], verts[(i + 1) % n][1]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def orient(verts, ccw=True):
    """Return verts wound CCW (font space) if ccw else CW."""
    if (signed_area(verts) > 0) != ccw:
        return list(reversed(verts))
    return list(verts)


def _unit(ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    if d == 0:
        raise ValueError(f"zero-length edge at ({ax},{ay})")
    return dx / d, dy / d


def _pieces(verts, k_default):
    """Expand vertices into drawing pieces.

    Yields ('corner', pt) or ('arc', entry, c1, c2, exit) per vertex.
    """
    n = len(verts)
    out = []
    for i in range(n):
        v = verts[i]
        x, y = float(v[0]), float(v[1])
        r = float(v[2]) if len(v) > 2 else 0.0
        k = float(v[3]) if len(v) > 3 else k_default
        if r <= 0:
            out.append(("corner", (x, y)))
            continue
        px, py = verts[i - 1][0], verts[i - 1][1]
        nx, ny = verts[(i + 1) % n][0], verts[(i + 1) % n][1]
        ux, uy = _unit(px, py, x, y)      # incoming direction
        wx, wy = _unit(x, y, nx, ny)      # outgoing direction
        ax, ay = x - ux * r, y - uy * r   # arc entry
        bx, by = x + wx * r, y + wy * r   # arc exit
        c1 = (ax + ux * k * r, ay + uy * k * r)
        c2 = (bx - wx * k * r, by - wy * k * r)
        out.append(("arc", (ax, ay), c1, c2, (bx, by)))
    return out


def _fx(x, dx):
    return int(round(x + dx))


def _fy(y):
    return int(round(BASELINE_SVG - y))


def contour_svg_d(verts, k_default=0.82, ccw=True, dx=0):
    """Emit one closed contour as an SVG path-d fragment (font->SVG flip)."""
    verts = orient(verts, ccw=ccw)
    pieces = _pieces(verts, k_default)
    cmds = []
    cur = None

    def pt(p):
        return (_fx(p[0], dx), _fy(p[1]))

    # start point
    first = pieces[0]
    start = pt(first[1])
    cmds.append(f"M{start[0]} {start[1]}")
    cur = start
    for i, pc in enumerate(pieces):
        if pc[0] == "corner":
            p = pt(pc[1])
            if i > 0 and p != cur:
                cmds.append(f"L{p[0]} {p[1]}")
            cur = p
        else:
            entry, c1, c2, exit_ = pt(pc[1]), pt(pc[2]), pt(pc[3]), pt(pc[4])
            if i > 0 and entry != cur:
                cmds.append(f"L{entry[0]} {entry[1]}")
            cmds.append(
                f"C{c1[0]} {c1[1]} {c2[0]} {c2[1]} {exit_[0]} {exit_[1]}"
            )
            cur = exit_
    cmds.append("Z")
    return "".join(cmds)


def glyph_svg_d(contours, lsb=0):
    """Full path d for a glyph: list of (verts, is_outer, k_default)."""
    frags = []
    for verts, is_outer, k in contours:
        frags.append(contour_svg_d(verts, k_default=k, ccw=is_outer, dx=lsb))
    return "".join(frags)


def ink_bbox(contours):
    """Approximate ink bbox from vertex positions (font space)."""
    xs, ys = [], []
    for verts, _, _ in contours:
        for v in verts:
            xs.append(v[0])
            ys.append(v[1])
    return min(xs), min(ys), max(xs), max(ys)
