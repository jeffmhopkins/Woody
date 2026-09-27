#!/usr/bin/env python3
"""A board's first PCB: placed from the body CAD and the KiCad sheets, routed, checked.

    python3 tools/pcb.py layout hardware/boards/key-board-lh   # write <board>.kicad_pcb (refuses if it exists; --force)
    python3 tools/pcb.py check  hardware/boards/key-board-lh   # DRC + schematic parity + fab limits + CAD agreement
    python3 tools/pcb.py render hardware/boards/key-board-lh   # 3D top/bottom and 2D copper PNGs, fab/ (refuses a board that fails check)

WHERE THINGS COME FROM - nothing on this board is typed in by hand twice:

  the netlist, footprints, references   the board's KiCad sheets (ADR 0019), via kicad-cli
  the board outline                     mechanical/export/key-board-<lh|rh>.dxf (the body CAD)
  switch and ribbon-connector places    mechanical/export/pcb-geometry.echo (the body CAD)
  everything else's place               layout.yaml beside the board: the underside parts,
                                        each beside what it serves, and the routing rules

`layout` writes the PCB ONCE. From then on the .kicad_pcb is the source, like
the sheets: open it in KiCad 9, move and re-route by hand. `check` is what
keeps it honest whoever edits it: KiCad's DRC with schematic parity (every
footprint and net agrees with the sheets), zero unrouted connections, its
warnings counted as failures; the design settings still those of layout.yaml
rules:/fab:, and the silkscreen limits DRC does not test (line width, silk to
a pad opening, silk off the board); and the body CAD's outline, thickness,
and every switch, standoff and the ribbon connector still where - and which
way up - it puts them.

COORDINATES. The body CAD's x runs along the body from the mouth and y across
it, seen from above. The PCB is drawn as seen from above too (KiCad's top
view): pcb x = body x + OX, pcb y = OY - body y. Switches sit on the TOP side
(into the plate); everything else - resistors, capacitors, the register and
the ribbon connector - is on the BOTTOM, facing the main board.
"""
import math
import os
import re
import subprocess
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sch import parse, find, kicad_env  # noqa: E402

import pcbnew  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPDIRS = {"woody": os.path.join(ROOT, "hardware", "lib", "woody.pretty")}
SYS_FP = "/usr/share/kicad/footprints"
OX, OY = 60.0, 150.0
MM = pcbnew.FromMM


def to_pcb(x, y):
    return (x + OX, OY - y)


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


# ------------------------------------------------------------------ inputs

def cad_geometry(cluster):
    geo = {"switches": {}, "chain": None, "standoffs": []}
    for line in open(os.path.join(ROOT, "mechanical", "export", "pcb-geometry.echo")):
        m = re.match(r'ECHO: "PCB", "(\w+)", "(\w+)", (.*)', line)
        if not m or m.group(1) != cluster:
            continue
        kind, rest = m.group(2), [t.strip().strip('"') for t in m.group(3).split(",")]
        if kind == "switch":
            geo["switches"][rest[0]] = (float(rest[1]), float(rest[2]), float(rest[3]))
        elif kind == "chain":
            # mouth x, centre y, which way the mouth faces along the body (+1 the tail), length, mouth to far pin row
            geo["chain"] = tuple(float(v) for v in rest[1:6])
        elif kind == "standoff":
            geo["standoffs"].append(tuple(float(v) for v in rest[1:6]))
        elif kind == "board":
            geo["thickness"] = float(rest[1])
    return geo


def dxf_segments(path):
    lines = [l.strip() for l in open(path).read().split("\n")]
    segs, i = [], 0
    while i < len(lines):
        if lines[i] == "LINE":
            d, j = {}, i + 1
            while j + 1 < len(lines) and lines[j] != "0":
                d[lines[j]] = lines[j + 1]
                j += 2
            segs.append(((float(d["10"]), float(d["20"])), (float(d["11"]), float(d["21"]))))
            i = j
        else:
            i += 1
    return segs


def sheet_netlist(sch):
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "n.net")
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, sch],
                       capture_output=True, text=True, check=True, env=kicad_env())
        tree = parse(open(out).read())[0]
    comps = {}
    for c in find(find(tree, "components")[0], "comp"):
        ref = find(c, "ref")[0][1]
        fp = find(c, "footprint")
        tst = find(c, "tstamps")
        sp = find(find(c, "sheetpath")[0], "tstamps")[0][1]
        flags = {find(p, "name")[0][1] for p in find(c, "property")}
        comps[ref] = {"value": find(c, "value")[0][1], "footprint": fp[0][1] if fp else "",
                      "path": sp + (tst[0][1] if tst else ""),
                      # the symbol's own "Exclude from BOM" and "Do not populate": the footprint carries both
                      "exclude_from_bom": "exclude_from_bom" in flags, "dnp": "dnp" in flags}
    nets = []
    for n in find(find(tree, "nets")[0], "net"):
        nets.append((find(n, "name")[0][1], [(find(x, "ref")[0][1], find(x, "pin")[0][1]) for x in find(n, "node")]))
    return comps, nets


def load_fp(libid):
    lib, name = libid.split(":", 1)
    d = FPDIRS.get(lib, os.path.join(SYS_FP, lib + ".pretty"))
    fp = pcbnew.FootprintLoad(d, name)
    if fp is None:
        sys.exit(f"pcb: footprint {libid} not found in {d}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ------------------------------------------------------------------ building the board

def new_board(bdir, lay, geo):
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    rules = lay["rules"]
    if "thickness" not in geo:
        sys.exit("pcb: pcb-geometry.echo gives no board thickness for this cluster - run: python3 tools/cad.py build pcb-geometry")
    ds.SetBoardThickness(MM(geo["thickness"]))
    ds.m_TrackMinWidth = MM(rules["track_min"])
    ds.m_MinClearance = MM(rules["clearance"])
    ds.m_ViasMinSize = MM(rules["via_min"])
    ds.m_MinThroughDrill = MM(rules["drill_min"])
    ds.m_CopperEdgeClearance = MM(rules["edge_clearance"])
    # the board house's own minimums (layout.yaml fab:), so KiCad's DRC checks them
    fabr = lay.get("fab", {})
    if fabr:
        ds.m_HoleClearance = MM(fabr["hole_clearance"])
        ds.m_HoleToHoleMin = MM(fabr["hole_to_hole"])
        ds.m_ViasMinAnnularWidth = MM(fabr["annular_min"])
        ds.m_MinSilkTextHeight = MM(fabr["silk_text_min"])
        ds.m_MinSilkTextThickness = MM(fabr["silk_line_min"])
        ds.m_SilkClearance = MM(fabr["silk_to_pad"])
        ds.m_HasStackup = True
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(MM(rules["clearance"]))
    nc.SetTrackWidth(MM(rules["track"]))
    nc.SetViaDiameter(MM(rules["via"]))
    nc.SetViaDrill(MM(rules["via_drill"]))
    board.SetCopperLayerCount(2)
    return board


def add_outline(board, segs):
    for (a, b) in segs:
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(V(*to_pcb(*a)))
        s.SetEnd(V(*to_pcb(*b)))
        s.SetWidth(MM(0.1))
        board.Add(s)


def chain_target(geo):
    """Where J-CHAIN's pads must centre, in PCB mm, and which way (PCB x) its mouth faces."""
    x, y, d, _, back = geo["chain"]
    return to_pcb(x - d * (back - 0.635), y), d


def pads_centre(fp):
    ps = [p.GetPosition() for p in fp.Pads()]
    return (sum(pcbnew.ToMM(p.x) for p in ps) / len(ps), sum(pcbnew.ToMM(p.y) for p in ps) / len(ps))


def place_chain(board, fp, geo):
    """The chain header on the bottom, its mouth facing along the body the way
    the body CAD says: the rotation is FOUND, not assumed - on the bottom KiCad
    mirrors rotation, and the footprint's own frame puts the mouth at +x from
    pin 1's row (pads 1 -> 2 point at the mouth)."""
    (tx, ty), d = chain_target(geo)
    for rot in (0, 90, 180, 270):
        place(board, fp, 0, 0, rot, True)
        p1, p2 = fp.FindPadByNumber("1").GetPosition(), fp.FindPadByNumber("2").GetPosition()
        dx, dy = pcbnew.ToMM(p2.x - p1.x), pcbnew.ToMM(p2.y - p1.y)
        if abs(dy) < 1e-3 and dx * d > 0:
            cx, cy = pads_centre(fp)
            fp.SetPosition(V(tx - cx, ty - cy))
            return rot
        board.Remove(fp)
        if fp.IsFlipped():
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    raise SystemExit("pcb: no rotation puts J-CHAIN's mouth where the body CAD faces it")


def place(board, fp, x, y, rot, bottom):
    board.Add(fp)
    fp.SetPosition(V(x, y))
    if bottom:
        fp.Flip(V(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot)


# A KEY NETWORK's three 0805s, as a T round the node they share (the KEY net:
# C-KEY pad 1, R-KEY-SER pad 1, R-KEY-PU pad 2), so no other pad stands
# between them and the node needs no via: S and P end to end, their KEY pads
# facing across the junction, and C hanging off the junction at right angles.
# On the bottom side, in body coordinates, an 0805's pad 1 faces -x at 0,
# +x at 180, +y at 90 and -y at 270 (measured through place()).
NET_PITCH = 2.7     # junction to each part's centre: two 0805 courtyards (±1.68 × ±0.95) apart


def network_parts(lay, geo):
    """layout.yaml networks: -> parts: entries. ONE PATTERN, RELATIVE TO EACH KEY'S
    SWITCH, so every key's network sits exactly the same way round its switch:
    `offset` (body mm, switch centre to the T's junction), `axis` (x or y: the line
    S and P lie along), `leg` (+1/-1: which way along that axis the series
    resistor sits - its SWITCH_LEG end, toward the switch's pin 1) and `c` (+1/-1:
    which way across it the capacitor hangs). A key that cannot take the pattern
    goes in `except:` with its own `at` and the reason beside it."""
    n = lay.get("networks") or {}
    pat, exc = n.get("pattern"), n.get("except") or {}
    if not pat:
        return {}
    for key in exc:
        if key not in geo["switches"]:
            sys.exit(f"pcb: networks: except: {key!r} names no switch on this board ({', '.join(sorted(geo['switches']))})")
    for key, spec in [("pattern", pat)] + [(k, {**pat, **v}) for k, v in exc.items()]:
        if spec.get("axis") not in ("x", "y") or spec.get("leg") not in (1, -1) or spec.get("c") not in (1, -1):
            sys.exit(f"pcb: networks: {key}: axis must be x or y, leg and c +1 or -1 - got {spec}")
    out = {}
    for key, (sx, sy, sr) in geo["switches"].items():
        spec = {**pat, **exc.get(key, {})}
        if "at" in spec:
            x, y = spec["at"]
        else:
            if sr % 360:
                sys.exit(f"pcb: networks: pattern is written for switches at 0 deg; SW-{key} is at {sr} - "
                         "give it an except: entry with its own `at`")
            x, y = sx + spec["offset"][0], sy + spec["offset"][1]
        d, c = spec["leg"], spec["c"]
        if spec["axis"] == "x":
            rot = 0 if d > 0 else 180         # S's pad 1 (KEY) and P's pad 2 (KEY) toward the junction
            out[f"R-KEY-SER-{key}"] = [x + d * NET_PITCH, y, rot]
            out[f"R-KEY-PU-{key}"] = [x - d * NET_PITCH, y, rot]
            out[f"C-KEY-{key}"] = [x, y + c * NET_PITCH, 270 if c > 0 else 90]
        else:
            rot = 90 if d > 0 else 270        # pad 1 faces -y at 90 and +y at 270 (measured through place())
            out[f"R-KEY-SER-{key}"] = [x, y + d * NET_PITCH, rot]
            out[f"R-KEY-PU-{key}"] = [x, y - d * NET_PITCH, rot]
            out[f"C-KEY-{key}"] = [x + c * NET_PITCH, y, 0 if c > 0 else 180]
    return out


SILK_H, SILK_W = 1.0, 0.18     # silkscreen text height and stroke, mm: JLC's 1.0 minimum height, and a stroke over its 0.15 minimum near its preferred 1:6 (R3-8)


def silk_text(board, text, x, y, h=SILK_H, justify=0, top=False, angle=0):
    """A line of text on the silkscreen: the BOTTOM (the parts side) by default,
    mirrored so it reads from below, or the TOP (the switch side). x, y in PCB mm;
    justify -1 left, 0 centre, +1 right, as read from that side."""
    edge = board.GetBoardEdgesBoundingBox()
    if not (pcbnew.ToMM(edge.GetLeft()) < x < pcbnew.ToMM(edge.GetRight()) and pcbnew.ToMM(edge.GetTop()) < y < pcbnew.ToMM(edge.GetBottom())):
        sys.exit(f"pcb: silkscreen label {text!r} would sit off the board at ({x:.1f}, {y:.1f})")
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(pcbnew.F_SilkS if top else pcbnew.B_SilkS)
    t.SetMirrored(not top)
    t.SetTextSize(V(h, h))
    t.SetTextThickness(MM(SILK_W))
    t.SetPosition(V(x, y))
    t.SetTextAngleDegrees(angle)
    # mirrored: what reads as "left" from below is the text's right
    left, right = (pcbnew.GR_TEXT_H_ALIGN_LEFT, pcbnew.GR_TEXT_H_ALIGN_RIGHT) if top else (pcbnew.GR_TEXT_H_ALIGN_RIGHT, pcbnew.GR_TEXT_H_ALIGN_LEFT)
    t.SetHorizJustify({-1: left, 0: pcbnew.GR_TEXT_H_ALIGN_CENTER, 1: right}[justify])
    board.Add(t)


def silk_arrow(board, x, y, d, s=1.2, top=False):
    """A filled triangle on the silkscreen pointing along PCB x (d = +1/-1)."""
    c = pcbnew.PCB_SHAPE(board)
    c.SetShape(pcbnew.SHAPE_T_POLY)
    c.SetLayer(pcbnew.F_SilkS if top else pcbnew.B_SilkS)
    c.SetFilled(True)
    c.SetWidth(MM(SILK_W))
    c.SetPolyPoints([V(x - d * s / 2, y - s / 2), V(x + d * s / 2, y), V(x - d * s / 2, y + s / 2)])
    board.Add(c)


def fit_footprint_silk(board, fab):
    """The library footprints' own silkscreen, made legal for the board house:
    every stroke widened to its minimum line, and a stroke that then comes
    nearer a pad's mask opening than its silk-to-pad limit removed (the
    board house would clip it anyway; the part letters mark the parts)."""
    from shapely.geometry import LineString, Point, Polygon
    wmin, gap = fab["silk_line_min"], fab["silk_to_pad"]
    removed = {}
    for fp in board.GetFootprints():
        pads = []
        for p in fp.Pads():
            poly = p.GetEffectivePolygon(pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu, pcbnew.ERROR_INSIDE)
            ol = poly.Outline(0)
            g = Polygon([(pcbnew.ToMM(ol.CPoint(k).x), pcbnew.ToMM(ol.CPoint(k).y)) for k in range(ol.PointCount())])
            m = pcbnew.ToMM(p.GetSolderMaskExpansion(pcbnew.B_Mask if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Mask))
            pads.append((p, g.buffer(m)))
        for item in list(fp.GraphicalItems()):
            if item.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS) or not isinstance(item, pcbnew.PCB_SHAPE):
                continue
            item.SetWidth(max(item.GetWidth(), MM(wmin)))
            xy = lambda v: (pcbnew.ToMM(v.x), pcbnew.ToMM(v.y))
            sh = item.GetShape()
            # the stroke as drawn: an outline is its ring, not the area it encloses
            if sh == pcbnew.SHAPE_T_SEGMENT:
                g = LineString([xy(item.GetStart()), xy(item.GetEnd())])
            elif sh == pcbnew.SHAPE_T_RECT:
                (x0, y0), (x1, y1) = xy(item.GetStart()), xy(item.GetEnd())
                g = LineString([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])
            elif sh == pcbnew.SHAPE_T_CIRCLE:
                g = Point(xy(item.GetCenter())).buffer(pcbnew.ToMM(item.GetRadius())).exterior
            elif sh == pcbnew.SHAPE_T_ARC:
                g = LineString([xy(item.GetStart()), xy(item.GetArcMid()), xy(item.GetEnd())])
            elif sh == pcbnew.SHAPE_T_POLY:
                ol = item.GetPolyShape().Outline(0)
                g = LineString([xy(ol.CPoint(k)) for k in range(ol.PointCount())] + [xy(ol.CPoint(0))])
            else:
                continue
            if item.IsFilled():
                g = Polygon(g.coords) if sh != pcbnew.SHAPE_T_CIRCLE else Polygon(g)
            side = pcbnew.B_Cu if item.GetLayer() == pcbnew.B_SilkS else pcbnew.F_Cu
            if any(p.IsOnLayer(side) and g.distance(pg) - pcbnew.ToMM(item.GetWidth()) / 2 < gap for p, pg in pads):
                fp.Remove(item)
                removed.setdefault(fp.GetFPID().GetLibItemName().wx_str(), set()).add(fp.GetReference())
    for name, refs in sorted(removed.items()):
        print(f"pcb: silk adapted - {name}: library silk too near its pads removed ({', '.join(sorted(refs))})")


def silk_dot(board, x, y, r=0.3, top=False):
    c = pcbnew.PCB_SHAPE(board)
    c.SetShape(pcbnew.SHAPE_T_CIRCLE)
    c.SetLayer(pcbnew.F_SilkS if top else pcbnew.B_SilkS)
    c.SetFilled(True)
    c.SetCenter(V(x, y))
    c.SetEnd(V(x + r, y))
    c.SetWidth(MM(SILK_W))
    board.Add(c)


def add_silk(board, lay):
    """The parts-side silkscreen, so the board can be assembled and probed by
    hand: references like R-KEY-SER-LH1 do not fit beside an 0805, so each key
    network's three parts get a letter (C the capacitor, S the series resistor,
    P the pull-up) under the key's name, and everything else a short name.
    The full references are on the fabrication layer, for the assembly drawing."""
    def box(fp):
        b = fp.GetCourtyard(pcbnew.B_CrtYd).BBox()
        return pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom())
    groups = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        m = re.match(r"(C-KEY|R-KEY-SER|R-KEY-PU)-(.+)$", ref)
        if m and not m.group(2).startswith("FREE"):
            groups.setdefault(m.group(2), []).append((m.group(1), fp))
    letter = {"C-KEY": "C", "R-KEY-SER": "S", "R-KEY-PU": "P"}
    edge = board.GetBoardEdgesBoundingBox()
    ex0, ey0, ex1, ey1 = (pcbnew.ToMM(edge.GetLeft()) + 0.5, pcbnew.ToMM(edge.GetTop()) + 0.5,
                          pcbnew.ToMM(edge.GetRight()) - 0.5, pcbnew.ToMM(edge.GetBottom()) - 0.5)
    crt = [box(fp) for fp in board.GetFootprints() if fp.GetCourtyard(pcbnew.B_CrtYd).OutlineCount()]
    # and every pad the parts side can see - the switches' pins and the holes
    # carry no bottom courtyard, but a label on them is silk on a solder joint
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.B_Cu) or p.HasHole():
                b = p.GetBoundingBox()
                crt.append((pcbnew.ToMM(b.GetLeft()) - 0.3, pcbnew.ToMM(b.GetTop()) - 0.3, pcbnew.ToMM(b.GetRight()) + 0.3, pcbnew.ToMM(b.GetBottom()) + 0.3))

    def clear(a0, b0, a1, b1):
        """A text box, in PCB mm, off every bottom courtyard and inside the board."""
        return (a0 >= ex0 and b0 >= ey0 and a1 <= ex1 and b1 <= ey1
                and not any(a0 < c[2] and a1 > c[0] and b0 < c[3] and b1 > c[1] for c in crt))

    placed_txt = []

    def put(text, x, y, justify=0):
        """Every label goes through here, so each later one keeps off it."""
        w = SILK_H * 0.9 * len(text)
        a0 = x - w / 2 if justify == 0 else (x - w if justify == 1 else x)
        placed_txt.append((a0, y - SILK_H / 2, a0 + w, y + SILK_H / 2))
        silk_text(board, text, x, y, justify=justify)

    def free(a0, b0, a1, b1, m=0.25):
        """clear(), and off every label already placed by m: the board house's silk-to-silk
        clearance, with room for the stroke font's glyphs running wider than the estimate."""
        return clear(a0, b0, a1, b1) and not any(a0 < t[2] + m and a1 > t[0] - m and b0 < t[3] + m and b1 > t[1] - m for t in placed_txt)

    def beside(x0, y0, x1, y1, text, under_first=False):
        """A short label over the part, else under it, else to either side:
        the first place off every courtyard and every label already placed."""
        w, h = SILK_H * 0.9 * len(text) / 2, SILK_H / 2
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        spots = [(cx, y0 - SILK_H * 0.75), (cx, y1 + SILK_H * 0.75), (x0 - 0.4 - w, cy), (x1 + 0.4 + w, cy)]
        if under_first:
            spots[0], spots[1] = spots[1], spots[0]
        for px, py in spots:
            if free(px - w, py - h, px + w, py + h):
                return px, py
        sys.exit(f"pcb: no clear place for the silkscreen label {text!r} at ({cx:.1f}, {cy:.1f}) - move parts in layout.yaml")
    above_or_below = beside
    def fixed(text, x, y):
        w = SILK_H * 0.9 * len(text) / 2
        if not free(x - w, y - SILK_H / 2, x + w, y + SILK_H / 2):
            sys.exit(f"pcb: the key-network label {text!r} at ({x:.1f}, {y:.1f}) is not clear - every key's labels sit "
                     "the same way round its network; move the part in the way, or the pattern (layout.yaml networks:)")
        put(text, x, y)
    for key, parts in groups.items():
        if len(parts) == 3:
            # A T (network_parts): every key's labels the same way round it. S's and P's
            # letters outside the column, away from C; C's letter on the S side of C,
            # the key's name on the P side of it.
            f = {kind: fp for kind, fp in parts}
            xy = {k: (pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y)) for k, v in f.items()}
            jx, jy = (xy["R-KEY-SER"][0] + xy["R-KEY-PU"][0]) / 2, (xy["R-KEY-SER"][1] + xy["R-KEY-PU"][1]) / 2
            ux, uy = xy["C-KEY"][0] - jx, xy["C-KEY"][1] - jy
            n = math.hypot(ux, uy)
            ux, uy = ux / n, uy / n                       # junction -> C
            ax, ay = xy["R-KEY-PU"][0] - jx, xy["R-KEY-PU"][1] - jy
            n = math.hypot(ax, ay)
            ax, ay = ax / n, ay / n                       # junction -> P
            for kind in ("R-KEY-SER", "R-KEY-PU"):
                fixed(letter[kind], xy[kind][0] - ux * 1.7, xy[kind][1] - uy * 1.7)
            fixed("C", xy["C-KEY"][0] - ax * 1.7, xy["C-KEY"][1] - ay * 1.7)
            fixed(key, xy["C-KEY"][0] + ax * 1.7, xy["C-KEY"][1] + ay * 1.7)
            continue
        boxes = [box(fp) for _, fp in parts]
        top = min(b[1] for b in boxes)
        for kind, fp in parts:
            put(letter[kind], *beside(*box(fp), letter[kind]))
        # the key's name beside its row, on whichever side is clear
        x0, x1 = min(b[0] for b in boxes), max(b[2] for b in boxes)
        cy = (min(b[1] for b in boxes) + max(b[3] for b in boxes)) / 2
        w = SILK_H * 0.9 * len(key)
        for bx, j in ((x0 - 0.5 - w, 1), (x1 + 0.5, -1)):
            if free(bx - 0.3, cy - SILK_H, bx + w + 0.3, cy + SILK_H):
                put(key, bx + w if j == 1 else bx, cy, justify=j)
                break
        else:
            put(key, *beside(x0, top - SILK_H * 1.6, x1, top - SILK_H * 1.6, key))
    # fixed-place labels (the test pads' row) first, so the searched ones keep off them
    # fixed-place marks first - the test pads' labels, J-CHAIN's dot and arrow - so
    # every searched label keeps off them
    for fp in sorted(board.GetFootprints(), key=lambda f: (not f.GetReference().startswith("TP-"), f.GetReference() != "J-CHAIN")):
        ref = fp.GetReference()
        x0, y0, x1, y1 = box(fp) if fp.GetCourtyard(pcbnew.B_CrtYd).OutlineCount() else (0, 0, 0, 0)
        if ref.startswith("U-"):
            put(fp.GetValue(), *beside(x0, y0, x1, y1, fp.GetValue()))
        elif ref.startswith("C-DECOUPLE"):
            put("CD", *above_or_below(x0, y0, x1, y1, "CD"))
        elif ref.startswith("C-BULK"):
            # under it: over it the label reads as J-CHAIN's, whose pads are beside
            put("CB DNP", *beside(x0, y0, x1, y1, "CB DNP", under_first=True))
        elif ref.startswith("R-KEY-PU-FREE"):
            put("PF", *above_or_below(x0, y0, x1, y1, "PF"))
        elif ref.startswith("TP-"):
            # test pads sit in a row: their names alternate under and over it
            name = ref[3:].rsplit("-", 1)[0].replace("SHLD", "SH/LD")
            row = sorted((f for f in board.GetFootprints() if f.GetReference().startswith("TP-")), key=lambda f: f.GetPosition().x)
            under = [f.GetReference() for f in row].index(ref) % 2 == 0
            # alternating, where that side is free; else the other side; else anywhere near
            w = SILK_H * 0.9 * len(name) / 2
            cx = (x0 + x1) / 2
            for py in ((y1 + SILK_H * 0.75, y0 - SILK_H * 0.75) if under else (y0 - SILK_H * 0.75, y1 + SILK_H * 0.75)):
                if free(cx - w, py - SILK_H / 2, cx + w, py + SILK_H / 2):
                    put(name, cx, py)
                    break
            else:
                put(name, *beside(x0, y0, x1, y1, name))
        elif ref == "J-CHAIN":
            p1 = fp.FindPadByNumber("1").GetPosition()
            p2 = fp.FindPadByNumber("2").GetPosition()
            # pin 1's dot outside the pad array, away from the mouth
            dx = pcbnew.ToMM(p1.x - p2.x)
            dxd = pcbnew.ToMM(p1.x) + (1.3 if dx > 0 else -1.3)
            silk_dot(board, dxd, pcbnew.ToMM(p1.y))   # its edge 0.39 off the pad: fab silk_to_pad
            placed_txt.append((dxd - 0.6, pcbnew.ToMM(p1.y) - 0.6, dxd + 0.6, pcbnew.ToMM(p1.y) + 0.6))
            put("J-CHAIN", *above_or_below(x0, y0, x1, y1, "J-CHAIN"))
            # which way its mouth faces: pads 1 -> 2 point at it (place_chain); a
            # header soldered backward puts 3V3 on a ground pin (key-chain-loom.md)
            mx = pcbnew.ToMM(p2.x - p1.x) > 0
            ax = x1 + 1.2 if mx else x0 - 1.2
            silk_arrow(board, ax, (y0 + y1) / 2, 1 if mx else -1)
            placed_txt.append((ax - 0.9, (y0 + y1) / 2 - 0.9, ax + 0.9, (y0 + y1) / 2 + 0.9))
    # which end of the board faces the mouth: body x runs from the mouth, so the
    # board's low-x edge - an arrow at it and the word beside, clear of everything
    mx, my = ex0 + 0.9, (ey0 + ey1) / 2
    if not clear(mx - 0.8, my - 0.8, mx + 1.2 + SILK_H * 0.9 * 5 + 0.3, my + 0.8):
        sys.exit("pcb: no clear place for the MOUTH marker at the board's mouth-end edge")
    silk_arrow(board, mx, my, -1)
    put("MOUTH", mx + 1.1 + SILK_H * 0.9 * 5 / 2, my)
    t = lay.get("silk", {})
    if t:
        # the title block too: the Gerber job file's "Revision" is its
        tb = board.GetTitleBlock()
        tb.SetTitle(t["title"])
        tb.SetRevision(t["rev"])
        tb.SetDate(t["date"])
        board.SetTitleBlock(tb)
        x, y = to_pcb(*t["at"])
        for i, line in enumerate([t["title"], f"rev {t['rev']}  {t['date']}"]):
            put(line, x, y + i * SILK_H * 1.8, justify=-1)


def add_top_silk(board, lay):
    """The switch side's silkscreen. J-CHAIN is soldered from this side and the
    board is lowered onto the switch pins top first, so it carries each key's name
    beside its switch, J-CHAIN's pin 1 and the way its mouth faces, the MOUTH end,
    and the board's title and revision. Not mirrored: it reads from above."""
    edge = board.GetBoardEdgesBoundingBox()
    ex0, ey0, ex1, ey1 = (pcbnew.ToMM(edge.GetLeft()) + 0.5, pcbnew.ToMM(edge.GetTop()) + 0.5,
                          pcbnew.ToMM(edge.GetRight()) - 0.5, pcbnew.ToMM(edge.GetBottom()) - 0.5)
    keep = []
    for fp in board.GetFootprints():
        if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount():
            b = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            keep.append((pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom())))
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.F_Cu) or p.HasHole():
                b, m = p.GetBoundingBox(), 0.3
                keep.append((pcbnew.ToMM(b.GetLeft()) - m, pcbnew.ToMM(b.GetTop()) - m, pcbnew.ToMM(b.GetRight()) + m, pcbnew.ToMM(b.GetBottom()) + m))
    placed = []

    def free(a0, b0, a1, b1, m=0.25):
        return (a0 >= ex0 and b0 >= ey0 and a1 <= ex1 and b1 <= ey1
                and not any(a0 < c[2] and a1 > c[0] and b0 < c[3] and b1 > c[1] for c in keep)
                and not any(a0 < c[2] + m and a1 > c[0] - m and b0 < c[3] + m and b1 > c[1] - m for c in placed))

    def put(text, x, y):
        w = SILK_H * 0.9 * len(text)
        placed.append((x - w / 2, y - SILK_H / 2, x + w / 2, y + SILK_H / 2))
        silk_text(board, text, x, y, top=True)

    def beside(x0, y0, x1, y1, text):
        w, h = SILK_H * 0.9 * len(text) / 2, SILK_H / 2
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for px, py in ((cx, y0 - SILK_H * 0.75), (cx, y1 + SILK_H * 0.75), (x0 - 0.4 - w, cy), (x1 + 0.4 + w, cy)):
            if free(px - w, py - h, px + w, py + h):
                return px, py
        sys.exit(f"pcb: no clear place on the top silkscreen for {text!r} at ({cx:.1f}, {cy:.1f}) - move parts in layout.yaml")
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        if ref.startswith("SW-"):
            b = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            put(ref[3:], *beside(pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom()), ref[3:]))
        elif ref == "J-CHAIN":
            p1, p2 = fp.FindPadByNumber("1").GetPosition(), fp.FindPadByNumber("2").GetPosition()
            dx = pcbnew.ToMM(p1.x - p2.x)
            silk_dot(board, pcbnew.ToMM(p1.x) + (1.3 if dx > 0 else -1.3), pcbnew.ToMM(p1.y), top=True)
            xs = [pcbnew.ToMM(p.GetPosition().x) for p in fp.Pads()]
            ys = [pcbnew.ToMM(p.GetPosition().y) for p in fp.Pads()]
            x0, x1, y0, y1 = min(xs) - 0.8, max(xs) + 0.8, min(ys) - 0.8, max(ys) + 0.8
            put("J-CHAIN", *beside(x0, y0, x1, y1, "J-CHAIN"))
            # its mouth faces the way pads 1 -> 2 point (place_chain)
            silk_arrow(board, (x1 + 1.0) if dx < 0 else (x0 - 1.0), (y0 + y1) / 2, 1 if dx < 0 else -1, top=True)
    # the MOUTH end: here the first switch leaves too narrow a strip for the word
    # across it, so it runs along the edge, the arrow beside it
    mx, my, tl = ex0 + 0.9, (ey0 + ey1) / 2, SILK_H * 0.9 * 5
    box = (mx - 0.8, my - tl / 2, mx + 1.2 + SILK_H + 0.2, my + tl / 2)
    if not free(*box):
        sys.exit("pcb: no clear place on the top silkscreen for the MOUTH marker")
    placed.append(box)
    silk_arrow(board, mx, my, -1, top=True)
    silk_text(board, "MOUTH", mx + 1.2 + SILK_H / 2, my, top=True, angle=90)
    t = lay.get("silk", {})
    if t.get("top_at"):
        x, y = to_pcb(*t["top_at"])
        for i, line in enumerate([t["title"], f"rev {t['rev']}  {t['date']}"]):
            w = SILK_H * 0.9 * len(line)
            if not free(x, y + i * SILK_H * 1.8 - SILK_H / 2, x + w, y + i * SILK_H * 1.8 + SILK_H / 2):
                sys.exit(f"pcb: the top silkscreen title at layout.yaml silk.top_at is not clear: {line!r}")
            placed.append((x, y + i * SILK_H * 1.8 - SILK_H / 2, x + w, y + i * SILK_H * 1.8 + SILK_H / 2))
            silk_text(board, line, x, y + i * SILK_H * 1.8, top=True, justify=-1)


def keepout(board, px, py, r, n=32):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    layers = pcbnew.LSET()
    layers.AddLayer(pcbnew.F_Cu)
    layers.AddLayer(pcbnew.B_Cu)
    z.SetLayerSet(layers)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ol = z.Outline()
    ol.NewOutline()
    for k in range(n):
        a = 2 * math.pi * k / n
        ol.Append(MM(px + r * math.cos(a)), MM(py + r * math.sin(a)))
    board.Add(z)


def build(bdir):
    name = os.path.basename(bdir)
    lay = yaml.safe_load(open(os.path.join(bdir, "layout.yaml")))
    cluster, suffix = lay["cluster"], lay["suffix"]
    geo = cad_geometry(cluster)
    comps, nets = sheet_netlist(os.path.join(bdir, name + ".kicad_sch"))
    board = new_board(bdir, lay, geo)
    add_outline(board, dxf_segments(os.path.join(ROOT, "mechanical", "export", f"key-board-{suffix.lower()}.dxf")))

    netinfo = {}
    for nname, _ in nets:
        ni = pcbnew.NETINFO_ITEM(board, nname)
        board.Add(ni)
        netinfo[nname] = ni
    padnet = {(r, p): n for n, nodes in nets for r, p in nodes}

    fps = {}
    for ref, c in sorted(comps.items()):
        if ref.startswith("#"):
            continue
        if not c["footprint"]:
            sys.exit(f"pcb: {ref} has no footprint on its sheet - set its Footprint field")
        fp = load_fp(c["footprint"])
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH(c["path"]))
        if c["exclude_from_bom"]:
            fp.SetExcludedFromBOM(True)
        if c["dnp"]:
            fp.SetDNP(True)
            fp.SetExcludedFromPosFiles(True)
        # References this long (R-KEY-SER-LH1) do not fit as silkscreen on an 0805:
        # they stay on the fabrication layer, where the assembly drawing reads them.
        fp.Reference().SetLayer(pcbnew.F_Fab)
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.5), MM(0.5)))
        fp.Reference().SetTextThickness(MM(0.08))
        for pad in fp.Pads():
            n = padnet.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(netinfo[n])
        fps[ref] = fp

    # The switch's 3D model has its origin at the plate seat (docs/reference/ks33-geometry.md);
    # the PCB top sits switch.pcb_below_seat below it (config/body.yaml), so lift the model by that.
    body = yaml.safe_load(open(os.path.join(ROOT, "config", "body.yaml")))
    below_seat = float(body["switch"]["pcb_below_seat"]["value"])
    for ref, fp in fps.items():
        if ref.startswith("SW-"):
            models = fp.Models()
            for i in range(len(models)):      # by index: SWIG's iterator hands out copies
                models[i].m_Offset.z = below_seat

    placed = set()
    # switches: top side, exactly where the body CAD puts them
    for key, (x, y, r) in geo["switches"].items():
        ref = f"SW-{key}"
        px, py = to_pcb(x, y)
        place(board, fps[ref], px, py, r + lay.get("switch_rot", 0), False)
        placed.add(ref)
    # the chain header: bottom side, where the body CAD stacks it over the
    # main board's, its mouth facing along the body toward the ribbon's fold
    place_chain(board, fps["J-CHAIN"], geo)
    placed.add("J-CHAIN")
    # the standoffs' screw holes (ADR 0020): board-only footprints, no symbol - the
    # screw and standoff are mechanical, in hardware/unplaced.csv. On the BOTTOM,
    # so their courtyard keeps the underside parts off the screw heads.
    for i, (x, y, hole, head, od) in enumerate(geo["standoffs"], 1):
        h = load_fp(lay["standoff_footprint"])
        h.SetReference(f"H{i}")
        h.SetValue("M2 standoff")
        h.SetBoardOnly(True)
        h.SetExcludedFromBOM(True)
        h.SetExcludedFromPosFiles(True)
        h.Reference().SetLayer(pcbnew.F_Fab)
        px, py = to_pcb(x, y)
        place(board, h, px, py, 0, True)
        # The standoff's end face presses on the top copper and the screw head on
        # the bottom, and both are the plate, which is grounded through its own
        # bond: no copper under either, or the board gets a second ground bond
        # and every net routed there a short. A rule area on both layers, which
        # the router also treats as an obstacle.
        keepout(board, px, py, max(head, od) / 2 + lay["rules"]["clearance"])
    # everything else: layout.yaml, in body coordinates, bottom side
    for ref, (x, y, r) in {**network_parts(lay, geo), **lay["parts"]}.items():
        px, py = to_pcb(x, y)
        place(board, fps[ref], px, py, r, True)
        placed.add(ref)
    # every key's T must have its node's three pads nearest the junction, or the
    # pattern turned a part the wrong way round (R6-3)
    for key in (lay.get("networks") or {}).get("pattern") and geo["switches"] or []:
        refs = [f"R-KEY-SER-{key}", f"R-KEY-PU-{key}", f"C-KEY-{key}"]
        if not all(r in fps for r in refs):
            continue
        s_, p_ = fps[refs[0]].GetPosition(), fps[refs[1]].GetPosition()
        jx, jy = (s_.x + p_.x) / 2, (s_.y + p_.y) / 2
        pads = sorted((pd for r in refs for pd in fps[r].Pads()), key=lambda pd: math.hypot(pd.GetPosition().x - jx, pd.GetPosition().y - jy))
        if len({pd.GetNetname() for pd in pads[:3]}) != 1:
            sys.exit(f"pcb: {key}'s network is not a T round its node: the pads nearest its junction are "
                     f"{', '.join(pd.GetParentFootprint().GetReference() + '.' + pd.GetNumber() + ' ' + pd.GetNetname() for pd in pads[:3])}")
    missing = sorted(set(fps) - placed)
    if missing:
        sys.exit(f"pcb: not placed (add them to layout.yaml parts): {', '.join(missing)}")
    if lay.get("fab"):
        fit_footprint_silk(board, lay["fab"])
    add_silk(board, lay)
    add_top_silk(board, lay)
    return board, fps, netinfo, lay


def save(board, path):
    board.BuildConnectivity()
    pcbnew.SaveBoard(path, board)


MASK_T = 0.01      # solder mask thickness in the stackup: KiCad's own default; it only splits the board's thickness


def set_stackup(path, fab, thickness):
    """KiCad's Python API does not reach the stackup, which the Gerber job file
    reports to the board house - finish, mask colour, copper weight: write it
    into the saved file, after the last save (the zone fill re-saves the board).
    The core is what is left of the board's thickness."""
    cu = fab["copper_oz"] * 0.035
    core = thickness - 2 * cu - 2 * MASK_T
    L = lambda name, typ, extra="": f'\t\t\t(layer "{name}"\n\t\t\t\t(type "{typ}"){extra}\n\t\t\t)\n'
    mask = f'\n\t\t\t\t(color "{fab["mask"]}")\n\t\t\t\t(thickness {MASK_T})'
    silk = f'\n\t\t\t\t(color "{fab["silk"]}")'
    block = ("\t\t(stackup\n" + L("F.SilkS", "Top Silk Screen", silk) + L("F.Paste", "Top Solder Paste")
             + L("F.Mask", "Top Solder Mask", mask) + L("F.Cu", "copper", f"\n\t\t\t\t(thickness {cu:.3f})")
             + L("dielectric 1", "core", f'\n\t\t\t\t(thickness {core:.3f})\n\t\t\t\t(material "FR4")\n\t\t\t\t(epsilon_r 4.5)\n\t\t\t\t(loss_tangent 0.02)')
             + L("B.Cu", "copper", f"\n\t\t\t\t(thickness {cu:.3f})") + L("B.Mask", "Bottom Solder Mask", mask)
             + L("B.Paste", "Bottom Solder Paste") + L("B.SilkS", "Bottom Silk Screen", silk)
             + f'\t\t\t(copper_finish "{fab["finish"]}")\n\t\t\t(dielectric_constraints no)\n\t\t)\n')
    t = open(path).read()
    t2, n = re.subn(r"\t\t\(stackup\n.*?\n\t\t\)\n", lambda m: block, t, count=1, flags=re.S)
    if not n:
        t2 = t.replace("\t(setup\n", "\t(setup\n" + block, 1)
        if t2 == t:
            sys.exit("pcb: could not write the stackup - no (setup) section found")
    open(path, "w").write(t2)


def cmd_layout(bdir, force=False):
    name = os.path.basename(bdir)
    out = os.path.join(bdir, name + ".kicad_pcb")
    if os.path.exists(out) and not force:
        sys.exit(f"pcb: {os.path.relpath(out, ROOT)} exists and is the source now; --force overwrites it")
    layout_yaml(bdir)      # a clear message, not build()'s traceback, when there is none
    board, fps, netinfo, lay = build(bdir)
    if lay.get("route", True):
        import pcb_route
        failed = pcb_route.route(board, lay)
        if failed:
            # the existing board, if any, is the source: a half-routed one does not replace it
            print(f"pcb: could not route {', '.join(failed)} - move parts in layout.yaml and re-run; "
                  f"{os.path.relpath(out, ROOT)} {'left as it was' if os.path.exists(out) else 'not written'}")
            return 1
    # Written in a scratch directory beside the board and moved in only when complete.
    # SaveBoard writes <name>.kicad_pro beside the .kicad_pcb, from the board (the design
    # rules are in it), so the scratch copy keeps the board's own name and both move.
    import shutil
    t = tempfile.mkdtemp(prefix=".layout-", dir=bdir)
    try:
        tmp = os.path.join(t, name + ".kicad_pcb")
        save(board, tmp)
        if lay.get("route", True):
            # zones are filled in a fresh process: an in-process fill of a just-built board crashes
            subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {os.path.dirname(os.path.abspath(__file__))!r}); "
                            f"import pcb_route; pcb_route.fill_zones({tmp!r})"], check=True)
        if lay.get("fab"):
            set_stackup(tmp, lay["fab"], board.GetDesignSettings().GetBoardThickness() / 1e6)
            # fit_footprint_silk adapts the library footprints' silkscreen to the board
            # house on purpose, so "does not match the library copy" is expected, not a finding
            import json
            pro = os.path.join(t, name + ".kicad_pro")
            j = json.load(open(pro))
            j["board"]["design_settings"]["rule_severities"]["lib_footprint_mismatch"] = "ignore"
            json.dump(j, open(pro, "w"), indent=2)
        os.replace(os.path.join(t, name + ".kicad_pro"), os.path.join(bdir, name + ".kicad_pro"))
        os.replace(tmp, out)
    finally:
        shutil.rmtree(t, ignore_errors=True)
    print(f"pcb: wrote {os.path.relpath(out, ROOT)}")


def drc(pcb):
    import json
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "drc.json")
        r = subprocess.run(["kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all",
                            "--format", "json", "-o", out, pcb], capture_output=True, text=True, env=kicad_env())
        if not os.path.exists(out):
            # kicad-cli exits non-zero when it FINDS violations, so the report's absence is the failure
            sys.exit(f"pcb: KiCad's DRC did not run on {os.path.relpath(pcb, ROOT)} (exit {r.returncode}):\n{r.stdout}{r.stderr}")
        return json.load(open(out))


def layout_yaml(bdir):
    p = os.path.join(bdir, "layout.yaml")
    if not os.path.exists(p):
        sys.exit(f"pcb: {os.path.relpath(p, ROOT)} does not exist - a board's first layout needs one; "
                 f"hardware/boards/key-board-lh/layout.yaml is the pattern")
    return yaml.safe_load(open(p))


def shapely_of(ps):
    """A KiCad SHAPE_POLY_SET as one shapely geometry, in PCB mm, holes kept: a
    test pad's silk ring has its pad in the hole, not under the ring."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    def ring(c):
        return [(pcbnew.ToMM(c.CPoint(j).x), pcbnew.ToMM(c.CPoint(j).y)) for j in range(c.PointCount())]
    return unary_union([Polygon(ring(ps.Outline(i)), [ring(ps.Hole(i, h)) for h in range(ps.HoleCount(i))])
                        for i in range(ps.OutlineCount())])


def item_shape(item, layer, grow=0):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, layer, grow, MM(0.005), pcbnew.ERROR_OUTSIDE)
    return shapely_of(ps)


# The layout.yaml limits the .kicad_pcb must still carry after a hand edit in KiCad's
# Board Setup (K7-14): (section, key, design-settings attribute). new_board sets them.
RULE_SETTINGS = [
    ("rules", "track_min", "m_TrackMinWidth"), ("rules", "clearance", "m_MinClearance"),
    ("rules", "via_min", "m_ViasMinSize"), ("rules", "drill_min", "m_MinThroughDrill"),
    ("rules", "edge_clearance", "m_CopperEdgeClearance"),
    ("fab", "hole_clearance", "m_HoleClearance"), ("fab", "hole_to_hole", "m_HoleToHoleMin"),
    ("fab", "annular_min", "m_ViasMinAnnularWidth"), ("fab", "silk_text_min", "m_MinSilkTextHeight"),
    ("fab", "silk_line_min", "m_MinSilkTextThickness"), ("fab", "silk_to_pad", "m_SilkClearance"),
]
# DRC tests that enforce a board house's limit. Set to "ignore" in the .kicad_pro they
# vanish from the report, and a DRC with nothing to say reads as a pass.
FAB_TESTS = ["clearance", "track_width", "annular_width", "drill_out_of_range", "hole_clearance",
             "hole_to_hole", "copper_edge_clearance", "text_height", "text_thickness",
             "silk_edge_clearance", "silk_over_copper", "silk_overlap", "solder_mask_bridge"]


# DRC tests that may be set to ignore, each for a reason; any other ignored test
# fails the check (R6-2: an ignored unconnected_items passed a board with a whole
# net unrouted).
IGNORE_OK = {
    "lib_footprint_mismatch": "fit_footprint_silk adapts the library silk to the board house on purpose",
    "footprint_filters_mismatch": "the sheets' symbols carry no footprint filters",
    "footprint_type_mismatch": "a hand-fitted THT part is marked SMD-excluded for placement files, not mistyped",
    "missing_courtyard": "the board-only mounting holes have none",
    "npth_inside_courtyard": "a switch's centre-pole hole lies inside its own courtyard",
    "pth_inside_courtyard": "a switch's pins lie inside its own courtyard",
}


def check_rules(board, bdir, name, lay):
    """The board's design settings still say what layout.yaml says, and no fab test is off."""
    import json
    bad = []
    ds = board.GetDesignSettings()
    for sec, key, attr in RULE_SETTINGS:
        want = lay.get(sec, {}).get(key)
        if want is None:
            continue
        got = pcbnew.ToMM(getattr(ds, attr))
        if abs(got - float(want)) > 1e-4:
            bad.append(f"error: [rules] the board's {attr} is {got:g} mm, layout.yaml {sec}.{key} says {want} - "
                       f"set it back in Board Setup, or change layout.yaml and say why")
    nc = ds.m_NetSettings.GetDefaultNetclass()
    if pcbnew.ToMM(nc.GetClearance()) + 1e-4 < float(lay["rules"]["clearance"]):
        bad.append(f"error: [rules] the Default net class clearance is {pcbnew.ToMM(nc.GetClearance()):g} mm, "
                   f"under layout.yaml rules.clearance {lay['rules']['clearance']}")
    pro = os.path.join(bdir, name + ".kicad_pro")
    sev = json.load(open(pro))["board"]["design_settings"].get("rule_severities", {}) if os.path.exists(pro) else {}
    for test, level in sorted(sev.items()):
        if level == "ignore" and test not in IGNORE_OK:
            why = "it enforces a board-house limit" if test in FAB_TESTS else "an ignored test drops out of the report, and a check with nothing to say reads as a pass"
            bad.append(f"error: [rules] DRC test {test} is set to ignore in {name}.kicad_pro - {why}; "
                       f"set it back, or add it to tools/pcb.py IGNORE_OK with the reason")
    return bad


def check_silk(board, fab):
    """What KiCad 9's DRC does not check (K3-2): silk LINE width (min_text_thickness is
    text only), silk to a pad's mask opening (min_silk_clearance is silk to silk, and
    silk over a pad fires only when they overlap), and silk wholly off the board (not
    a DRC item at all). Whole shapes, not anchors: a title anchored on the board can
    still run off it."""
    bad = []
    ol = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(ol):
        return ["error: [silk] the Edge.Cuts outline is not one closed shape, so silk cannot be checked against it"]
    outline = shapely_of(ol)
    silk = {pcbnew.F_SilkS: pcbnew.F_Mask, pcbnew.B_SilkS: pcbnew.B_Mask}
    openings = {s: [] for s in silk}
    items = [("board", d) for d in board.GetDrawings() if d.GetLayer() in silk]
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        items += [(ref, g) for g in fp.GraphicalItems() if g.GetLayer() in silk]
        items += [(ref, f) for f in fp.GetFields() if f.GetLayer() in silk and f.IsVisible()]
        for pad in fp.Pads():
            for s, mask in silk.items():
                if pad.IsOnLayer(mask):
                    openings[s].append((f"{ref} pad {pad.GetNumber()}" if pad.GetNumber() else f"{ref}'s hole",
                                        item_shape(pad, mask, pad.GetSolderMaskExpansion(mask))))
    line_min, text_min, to_pad = (float(fab.get(k, 0)) for k in ("silk_line_min", "silk_text_min", "silk_to_pad"))
    # a tented via has no mask opening, but silk on it prints onto its tent over
    # an open hole: keep silk off every via's copper (R3-2, R3-3)
    from shapely.geometry import Point as _P
    vias = [(v.GetNetname(), _P(pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y)).buffer(pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)) / 2))
            for v in board.GetTracks() if isinstance(v, pcbnew.PCB_VIA)]
    thin, near = {}, {}
    for who, it in items:
        layer = it.GetLayer()
        text = hasattr(it, "GetText")
        what = f"{who} text {it.GetText()!r}" if text else f"{who} silk {it.ShowShape().lower()}"
        c = it.GetBoundingBox().Centre()
        where = f"({pcbnew.ToMM(c.x):.2f}, {pcbnew.ToMM(c.y):.2f})"
        shape = item_shape(it, layer)
        if not outline.contains(shape):
            bad.append(f"error: [silk] {what} at {where} is {'partly' if outline.intersects(shape) else 'wholly'} off the board")
        if not text:
            # a filled shape prints its fill, so the fill must be as wide as a line
            if it.IsFilled():
                if shape.buffer(-line_min / 2 + 1e-3).is_empty:
                    bad.append(f"error: [silk] {what} at {where} is a filled sliver narrower than fab.silk_line_min {line_min:g}")
            elif pcbnew.ToMM(it.GetWidth()) + 1e-4 < line_min:
                thin.setdefault((who, pcbnew.ToMM(it.GetWidth())), []).append(where)
        elif pcbnew.ToMM(it.GetTextHeight()) + 1e-4 < text_min or pcbnew.ToMM(it.GetTextThickness()) + 1e-4 < line_min:
            bad.append(f"error: [silk] {what} is {pcbnew.ToMM(it.GetTextHeight()):g} mm high with a "
                       f"{pcbnew.ToMM(it.GetTextThickness()):g} mm stroke; fab: needs {text_min:g} / {line_min:g}")
        for vnet, vg in vias:
            if shape.intersects(vg):
                c2 = vg.centroid
                bad.append(f"error: [silk] {what} at {where} lies on a via ({vnet} at ({c2.x:.2f}, {c2.y:.2f})) - "
                           "move the label, or the via")
        for pname, opening in openings[layer]:
            gap = shape.distance(opening)
            if gap + 1e-4 < to_pad:
                k = (f"{what} at {where}", pname)
                near[k] = min(gap, near.get(k, gap))
    for (who, w), wheres in sorted(thin.items()):
        bad.append(f"error: [silk] {who}: {len(wheres)} silk line(s) {w:g} mm wide, under fab.silk_line_min {line_min:g}")
    for (who, pname), gap in sorted(near.items()):
        bad.append(f"error: [silk] {who} is {gap:.3f} mm from {pname}'s mask opening, "
                   f"under fab.silk_to_pad {to_pad:g}")
    return bad


def check_tracks(board):
    """Two tracks of one net meeting on one layer at under 90 degrees leave a wedge
    the etch pools in and the pour cannot fill (an acid trap). KiCad's DRC has no
    such test. Joins at a shared end AND a track ending in the middle of another
    (R6-1) are both tested; a wedge whose apex a via or pad of the net fills is
    not a trap (pcb_route.acute_closed, R6-7)."""
    import pcb_route
    bad, arms = [], {}
    tracks = [t for t in board.GetTracks() if type(t) is pcbnew.PCB_TRACK]
    for t in tracks:
        for e, o in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
            arms.setdefault((t.GetNetname(), t.GetLayer(), e.x, e.y), []).append(((o.x - e.x, o.y - e.y), t.GetWidth()))
    # a track end inside another track of the net: that track's two halves are arms there
    for (net, layer, x, y) in list(arms):
        for u in tracks:
            if u.GetNetname() != net or u.GetLayer() != layer:
                continue
            a, b = u.GetStart(), u.GetEnd()
            dx, dy = b.x - a.x, b.y - a.y
            l2 = dx * dx + dy * dy
            if not l2 or (x, y) in ((a.x, a.y), (b.x, b.y)):
                continue
            k = ((x - a.x) * dx + (y - a.y) * dy) / l2
            if 0 < k < 1 and abs((x - a.x) * dy - (y - a.y) * dx) / math.sqrt(l2) < 1000:
                arms[(net, layer, x, y)] += [((a.x - x, a.y - y), u.GetWidth()), ((b.x - x, b.y - y), u.GetWidth())]
    for (net, layer, x, y), vs in arms.items():
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                ((ax, ay), wa), ((cx, cy), wc) = vs[i], vs[j]
                na, nc = math.hypot(ax, ay), math.hypot(cx, cy)
                if not (na and nc) or (ax * cx + ay * cy) / (na * nc) <= math.cos(math.radians(89.5)):
                    continue
                if pcb_route.acute_closed(board, net, layer, (x, y), (ax, ay), (cx, cy), max(wa, wc)):
                    continue
                ang = math.degrees(math.acos(min(1.0, (ax * cx + ay * cy) / (na * nc))))
                bad.append(f"error: [tracks] {net} on {board.GetLayerName(layer)}: two tracks meet at {ang:.0f} deg "
                           f"at ({x / 1e6:.2f}, {y / 1e6:.2f}) - an acid trap; re-route one")
    return bad


def track_path_mm(board, pa, pb):
    """The shortest route in the net's own tracks and vias from pad pa to pad pb
    (pad objects), in mm, or None: the pour does not count - it is what a signal
    track can cut (R3-1)."""
    import heapq as hq
    net = pa.GetNetname()
    node = lambda layer, v: (layer, round(v.x / 1000), round(v.y / 1000))
    adj = {}

    def edge(u, v, w):
        adj.setdefault(u, []).append((v, w))
        adj.setdefault(v, []).append((u, w))
    items = [t for t in board.GetTracks() if t.GetNetname() == net]
    for t in items:
        if isinstance(t, pcbnew.PCB_VIA):
            edge(node(pcbnew.F_Cu, t.GetPosition()), node(pcbnew.B_Cu, t.GetPosition()), 0.0)
        else:
            edge(node(t.GetLayer(), t.GetStart()), node(t.GetLayer(), t.GetEnd()), pcbnew.ToMM(t.GetLength()))
    for tag, pad in (("A", pa), ("B", pb)):
        for t in items:
            if isinstance(t, pcbnew.PCB_VIA):
                continue
            for v in (t.GetStart(), t.GetEnd()):
                if pad.IsOnLayer(t.GetLayer()) and pad.HitTest(v):
                    edge(tag, node(t.GetLayer(), v), 0.0)
    dist, q = {"A": 0.0}, [(0.0, "A")]
    while q:
        d, u = hq.heappop(q)
        if u == "B":
            return d
        if d > dist.get(u, 1e18):
            continue
        for v, w in adj.get(u, []):
            if d + w < dist.get(v, 1e18):
                dist[v] = d + w
                hq.heappush(q, (d + w, v))
    return None


def check_connect_first(board, lay):
    """layout.yaml connect_first: each connection still runs in its own tracks, and
    no longer than its max_mm - the decoupling loop stays a loop (R3-1)."""
    bad = []
    for spec in lay.get("connect_first", []):
        pa, pb = (board.FindFootprintByReference(p.split(".")[0]).FindPadByNumber(p.split(".")[1]) for p in spec["pads"])
        d = track_path_mm(board, pa, pb)
        if d is None or d > spec["max_mm"]:
            bad.append(f"error: [connect] {spec['pads'][0]} to {spec['pads'][1]}: "
                       + ("no track path" if d is None else f"{d:.1f} mm of track") + f", layout.yaml connect_first allows "
                       f"{spec['max_mm']} ({spec.get('why', '')})")
    return bad


def check_cad(board, lay, geo):
    """The body CAD still agrees with the board: its outline and thickness, and every
    switch, standoff and the chain header where - and which way up - it puts them."""
    from shapely.geometry import MultiLineString
    bad = []
    # thickness: the board against the echo, and the echo against its own source
    body = yaml.safe_load(open(os.path.join(ROOT, "config", "body.yaml")))
    t_cfg = float(body["boards"]["key_board_t"]["value"])
    t_pcb = pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())
    if "thickness" not in geo:
        bad.append("error: [cad] pcb-geometry.echo has no board thickness for this cluster - run: python3 tools/cad.py build pcb-geometry")
    else:
        if abs(geo["thickness"] - t_cfg) > 1e-6:
            bad.append(f"error: [cad] pcb-geometry.echo says the board is {geo['thickness']:g} mm, config/body.yaml "
                       f"boards.key_board_t says {t_cfg:g} - run: python3 tools/cad.py build")
        if abs(t_pcb - geo["thickness"]) > 1e-6:
            bad.append(f"error: [cad] the board's stackup is {t_pcb:g} mm thick, the body CAD's key board "
                       f"{geo['thickness']:g} mm (boards.key_board_t) - Board Setup > Physical Stackup")
    # outline: every point of each within 0.05 mm of the other (the DXF's corner arcs are segments)
    dxf = os.path.join(ROOT, "mechanical", "export", f"key-board-{lay['suffix'].lower()}.dxf")
    ol = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(ol):
        bad.append("error: [cad] the Edge.Cuts outline is not one closed shape")
    else:
        cad = MultiLineString([(to_pcb(*a), to_pcb(*b)) for a, b in dxf_segments(dxf)])
        off = shapely_of(ol).boundary.hausdorff_distance(cad)
        if off > 0.05:
            bad.append(f"error: [cad] the Edge.Cuts outline is up to {off:.2f} mm from the body CAD's "
                       f"({os.path.relpath(dxf, ROOT)})")
    below_seat = float(body["switch"]["pcb_below_seat"]["value"])
    for key, (x, y, r) in geo["switches"].items():
        fp = board.FindFootprintByReference(f"SW-{key}")
        if fp is None:
            bad.append(f"error: [cad] SW-{key} is not on the board; the body CAD has a switch there")
            continue
        px, py = to_pcb(x, y)
        got = (pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y))
        if math.hypot(got[0] - px, got[1] - py) > 0.05:
            bad.append(f"error: [cad] SW-{key} is at {got}, the body CAD puts it at ({px:.2f}, {py:.2f})")
        # the KS-33's pins are asymmetric: a turned switch no longer fits its plate cutout
        want = (r + lay.get("switch_rot", 0)) % 360
        rot = fp.GetOrientationDegrees() % 360
        if min(abs(rot - want), 360 - abs(rot - want)) > 0.01 or fp.IsFlipped():
            bad.append(f"error: [cad] SW-{key} is turned {rot:g} deg{' on the bottom' if fp.IsFlipped() else ''}; "
                       f"the body CAD turns it {want:g} deg, on the top")
        models = fp.Models()
        for i in range(len(models)):      # by index: SWIG's iterator hands out copies
            if abs(models[i].m_Offset.z - below_seat) > 1e-6:
                bad.append(f"error: [cad] SW-{key}'s 3D model sits {models[i].m_Offset.z:g} mm up; "
                           f"config/body.yaml switch.pcb_below_seat is {below_seat:g}")
    for i, (x, y, *_) in enumerate(geo["standoffs"], 1):
        fp = board.FindFootprintByReference(f"H{i}")
        px, py = to_pcb(x, y)
        got = None if fp is None else (pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y))
        if got is None or math.hypot(got[0] - px, got[1] - py) > 0.05:
            bad.append(f"error: [cad] standoff hole H{i} is at {got}, the body CAD puts it at ({px:.2f}, {py:.2f})")
            continue
        hole_d, head, od = geo["standoffs"][i - 1][2:5]
        for pad in fp.Pads():
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH or abs(pcbnew.ToMM(pad.GetDrillSize().x) - hole_d) > 0.01:
                bad.append(f"error: [cad] H{i} must be an NPTH hole of {hole_d:g} mm (the body CAD's); it is "
                           f"{'plated' if pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH else 'unplated'}, {pcbnew.ToMM(pad.GetDrillSize().x):g} mm")
        # ADR 0020: no copper under what bears on the board on either face - a bond
        # to the grounded plate, and a short to any net routed there (R6-4)
        from shapely.geometry import Point as _P
        r = max(head, od) / 2 + float(lay["rules"]["clearance"])
        disc = _P(*got).buffer(r - 0.02)
        for L in (pcbnew.F_Cu, pcbnew.B_Cu):
            hits = []
            for t in board.GetTracks():
                if t.IsOnLayer(L) and item_shape(t, L).intersects(disc):
                    hits.append(f"{t.GetNetname()} {'via' if isinstance(t, pcbnew.PCB_VIA) else 'track'}")
            for z in board.Zones():
                if not z.GetIsRuleArea() and z.IsOnLayer(L) and z.GetFilledPolysList(L).OutlineCount() \
                        and shapely_of(z.GetFilledPolysList(L)).intersects(disc):
                    hits.append(f"{z.GetNetname()} pour")
            for f2 in board.GetFootprints():
                for pad in f2.Pads():
                    if f2.GetReference() != fp.GetReference() and pad.IsOnLayer(L) and item_shape(pad, L).intersects(disc):
                        hits.append(f"{f2.GetReference()} pad {pad.GetNumber()}")
            if hits:
                bad.append(f"error: [cad] copper within {r:.2f} mm of standoff hole H{i} on {board.GetLayerName(L)} "
                           f"({', '.join(sorted(set(hits)))}) - the washer and nut bear there (ADR 0020)")
    if geo["chain"]:
        fp = board.FindFootprintByReference("J-CHAIN")
        if fp is None:
            bad.append("error: [cad] J-CHAIN is not on the board; the body CAD has the chain header there")
        else:
            (tx, ty), d = chain_target(geo)
            got = pads_centre(fp)
            p1, p2 = fp.FindPadByNumber("1").GetPosition(), fp.FindPadByNumber("2").GetPosition()
            if math.hypot(got[0] - tx, got[1] - ty) > 0.05 or pcbnew.ToMM(p2.x - p1.x) * d <= 0:
                bad.append(f"error: [cad] J-CHAIN's pads centre at {got}, facing {'+' if p2.x > p1.x else '-'}x; the body CAD puts them at ({tx:.2f}, {ty:.2f}) facing {'+' if d > 0 else '-'}x")
            if not fp.IsFlipped():
                bad.append("error: [cad] J-CHAIN is on the top side; it belongs underneath, facing the main board")
    return bad


def cmd_check(bdir):
    """Every line is a failure, KiCad's DRC warnings included: the fab-limit tests (text
    height, hole to hole, silk at the edge) only ever warn (K3-2), and this board has none."""
    name = os.path.basename(bdir)
    pcb = os.path.join(bdir, name + ".kicad_pcb")
    lay = layout_yaml(bdir)
    if not os.path.exists(pcb):
        sys.exit(f"pcb: {os.path.relpath(pcb, ROOT)} does not exist - run: python3 tools/pcb.py layout {os.path.relpath(bdir, ROOT)}")
    d = drc(pcb)
    bad = []
    for v in d.get("violations", []):
        sev = "" if v["severity"] == "error" else f" (KiCad: {v['severity']})"
        bad.append(f"error: [{v['type']}]{sev} {v['description']} - " + "; ".join(i["description"] for i in v.get("items", [])))
    for v in d.get("unconnected_items", []):
        bad.append(f"error: [unconnected] " + "; ".join(i["description"] for i in v.get("items", [])))
    for v in d.get("schematic_parity", []):
        bad.append(f"error: [parity] {v['description']} - " + "; ".join(i["description"] for i in v.get("items", [])))
    board = pcbnew.LoadBoard(pcb)
    bad += check_rules(board, bdir, name, lay)
    if lay.get("fab"):
        bad += check_silk(board, lay["fab"])
    bad += check_tracks(board)
    bad += check_connect_first(board, lay)
    bad += check_cad(board, lay, cad_geometry(lay["cluster"]))
    print(f"pcb: {os.path.relpath(pcb, ROOT)}: {len(bad)} error(s)")
    for b in bad:
        print("  " + b)
    return 1 if bad else 0


def assembly_files(bdir, name, fab):
    """The assembly order, for JLCPCB (the owner's board house - docs: the board's
    README): a BOM of the machine-placed parts with their LCSC numbers, a
    placement (CPL) file of the same parts, and the list of parts fitted by hand.
    Part identity comes from the sheets' fields (Manufacturer, MPN, LCSC,
    Assembly = machine / hand / none); positions from KiCad's own placement
    export. Rotation is KiCad's, uncorrected - the guide's Method 1
    (datasheets/fab/JLCPCB-KICAD-BOM-CPL-GUIDE.pdf credits rotation fixes only
    to a plugin this flow does not use), so JLC's placement preview is where
    the part orientations are confirmed before the order. Returns the sheets read, so
    the ledger ties these files to them as well as to the board."""
    import csv
    import kicad
    root = os.path.join(bdir, name + ".kicad_sch")
    comps, _ = kicad.kicad_netlist(root)
    pos = {r["Ref"]: r for r in csv.DictReader(open(os.path.join(fab, name + "-pos.csv")))}
    machine, hand, none = {}, [], []
    for ref in sorted(comps):
        f = comps[ref]["fields"]
        how = f.get("Assembly", "")
        if how == "none":
            # nothing is bought for it - so it must be a part nothing is bought for: a test
            # pad, a fiducial, "Exclude from BOM" ticked. Otherwise `none` drops a real part
            # from the order and the hand list both, and every check passes (K7-3).
            if comps[ref]["in_bom"]:
                sys.exit(f"pcb: {ref} is Assembly = none but in the BOM - machine or hand, or tick "
                         f"'Exclude from BOM' on its symbol if nothing is bought for it")
            none.append(ref)
        if how == "machine":
            if ref not in pos:
                sys.exit(f"pcb: {ref} is machine-assembled but not in the placement export")
            if not f.get("LCSC"):
                sys.exit(f"pcb: {ref} is machine-assembled but has no LCSC field on its sheet")
            key = (comps[ref]["value"], comps[ref]["footprint"], f["LCSC"])
            machine.setdefault(key, []).append(ref)
        elif how == "hand":
            hand.append((ref, comps[ref]["value"], f.get("Manufacturer", ""), f.get("MPN", "")))
        elif how != "none" and not ref.startswith("#"):
            sys.exit(f"pcb: {ref} has no Assembly field (machine, hand or none) on its sheet")
    with open(os.path.join(fab, name + "-bom-jlc.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint", "JLCPCB Part #"])
        for (val, fp, lcsc), refs in sorted(machine.items()):
            w.writerow([val, ",".join(refs), fp.split(":")[-1], lcsc])
    with open(os.path.join(fab, name + "-cpl-jlc.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for refs in machine.values():
            for ref in sorted(refs):
                r = pos[ref]
                w.writerow([ref, r["PosX"], r["PosY"], "Bottom" if r["Side"] == "bottom" else "Top", r["Rot"]])
    with open(os.path.join(fab, name + "-hand-assembly.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Value", "Manufacturer", "MPN"])
        w.writerows(hand)
    if none:
        print(f"pcb: not in any order (Assembly = none, excluded from the BOM): {', '.join(none)}")
    subs = re.findall(r'\(property "Sheetfile" "([^"]+)"', open(root).read())
    return [root] + sorted({os.path.normpath(os.path.join(bdir, s)) for s in subs})


def cmd_render(bdir):
    """3D views of both sides, 2D copper plots, and the fabrication outputs - all recorded
    in hardware/SHEETS.csv against the .kicad_pcb, so tools/kicad.py check reports them
    stale when the board moves.

    Nothing is written until everything is: the board must pass `check` first, every 3D
    model it names must exist, and the outputs are made in a scratch directory and moved
    in at the end. A refusal half-way used to leave fab/ deleted and the renders
    rewritten with no ledger row, which kicad.py check then blamed on a hand edit (K7-7)."""
    import shutil
    import kicad
    name = os.path.basename(bdir)
    pcb = os.path.join(bdir, name + ".kicad_pcb")
    if cmd_check(bdir):
        sys.exit("pcb: not rendering a board that fails its check - nothing was written")
    env = kicad_env()
    missing = missing_models(pcbnew.LoadBoard(pcb), bdir, env)
    if missing:
        sys.exit("pcb: the 3D render would silently leave out every part whose model is missing - "
                 "run tools/setup-env.sh, or bank the model:\n  " + "\n  ".join(missing))
    t = tempfile.mkdtemp(prefix=".render-", dir=bdir)
    try:
        outs = []
        for side, rot in (("top", "-35,0,20"), ("bottom", "35,0,-20")):
            o = os.path.join(t, f"{name}.pcb-3d-{side}.png")
            subprocess.run(["kicad-cli", "pcb", "render", "--side", side, "--width", "1800", "--height", "1000",
                            "--quality", "high", "--perspective", "--rotate", rot, "-o", o, pcb],
                           capture_output=True, text=True, env=env, check=True)
            outs.append(o)
        for layers, tag, mirror in (("F.Cu,Edge.Cuts", "copper-top", False), ("B.Cu,Edge.Cuts,B.Fab", "copper-bottom", True)):
            svg = os.path.join(t, tag + ".svg")
            args = ["kicad-cli", "pcb", "export", "svg", "--layers", layers, "--page-size-mode", "2",
                    "--exclude-drawing-sheet", "-o", svg, pcb]
            if mirror:
                args.insert(4, "--mirror")
            subprocess.run(args, capture_output=True, text=True, env=env, check=True)
            o = os.path.join(t, f"{name}.pcb-{tag}.png")
            subprocess.run(["rsvg-convert", "-z", "7", "-b", "white", "-o", o, svg], check=True)
            outs.append(o)
        # fabrication: Gerbers, drill, pick-and-place, as a board house takes them. Plated
        # and unplated holes in separate drill files (<name>-PTH.drl, <name>-NPTH.drl), as
        # JLCPCB asks - the standoff holes must stay unplated (ADR 0020).
        fab = os.path.join(t, "fab")
        os.makedirs(fab)
        subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "--no-protel-ext", "--layers", "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts", "-o", fab + "/", pcb],
                       capture_output=True, text=True, env=env, check=True)
        subprocess.run(["kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "-o", fab + "/", pcb],
                       capture_output=True, text=True, env=env, check=True)
        subprocess.run(["kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
                        "-o", os.path.join(fab, name + "-pos.csv"), pcb], capture_output=True, text=True, env=env, check=True)
        sheets = assembly_files(bdir, name, fab)
        # everything made: now swap it in
        final = []
        for o in outs:
            final.append(os.path.join(bdir, os.path.basename(o)))
            os.replace(o, final[-1])
        dest, old = os.path.join(bdir, "fab"), os.path.join(t, "fab.old")
        if os.path.exists(dest):
            os.rename(dest, old)
        os.rename(fab, dest)
    finally:
        shutil.rmtree(t, ignore_errors=True)
    fabfiles = sorted(os.path.join(dest, f) for f in os.listdir(dest))
    kicad.ledger_set(bdir, final + fabfiles, [pcb] + sheets, kind="pcb")
    for o in final:
        print(f"pcb: rendered {os.path.relpath(o, ROOT)}")
    print(f"pcb: {len(fabfiles)} fabrication file(s) in {os.path.relpath(dest, ROOT)}/")


def missing_models(board, bdir, env):
    """Every 3D model a footprint names, resolved as KiCad would: kicad-cli renders a part
    whose model is missing as nothing at all, exits 0 and says nothing. A footprint that
    names no model (woody:IDC-Header_..._Samtec_SHF_Horizontal, the test pads, the
    standoff holes) is not asked for one."""
    out = {}
    for fp in board.GetFootprints():
        models = fp.Models()
        for i in range(len(models)):      # by index: SWIG's iterator hands out copies
            if not models[i].m_Show:
                continue
            f = models[i].m_Filename
            p = re.sub(r"\$\{(\w+)\}", lambda m: bdir if m.group(1) == "KIPRJMOD" else env.get(m.group(1), m.group(0)), f)
            p = p if os.path.isabs(p) else os.path.join(bdir, p)
            if not os.path.exists(p):
                out.setdefault(f"{f} -> {p}", []).append(fp.GetReference())
    return [f"{m} ({', '.join(sorted(refs))})" for m, refs in sorted(out.items())]


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] in ("layout", "check", "render"):
        d = os.path.join(ROOT, sys.argv[2].rstrip("/"))
        sys.exit({"layout": lambda: cmd_layout(d, "--force" in sys.argv), "check": lambda: cmd_check(d),
                  "render": lambda: cmd_render(d)}[sys.argv[1]]() or 0)
    print(__doc__)
    sys.exit(2)
