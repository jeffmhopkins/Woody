#!/usr/bin/env python3
"""A board's first PCB: placed from the body CAD and the KiCad sheets, routed, checked.

    python3 tools/pcb.py layout hardware/boards/key-board-lh   # write <board>.kicad_pcb (refuses if it exists; --force)
    python3 tools/pcb.py check  hardware/boards/key-board-lh   # DRC + schematic parity + fab limits + CAD agreement
    python3 tools/pcb.py render hardware/boards/key-board-lh   # 3D top/bottom and 2D copper PNGs, fab/ (refuses a board that fails check)
    python3 tools/pcb.py stackup hardware/boards/key-board-lh  # mask/silk colours and finish rewritten from layout.yaml fab:
    python3 tools/pcb.py finish hardware/boards/main-board     # a routed board's missing connections tried again, with rip-up
    python3 tools/pcb.py route hardware/boards/module-main     # a placed board (layout --no-route) routed in place, resumably
    python3 tools/pcb.py update-footprints hardware/boards/main-board LED_WS2815B-V1_PLCC6_5.4x5.0mm_P1.6mm   # placed footprints from the library, same place and nets

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
import shutil
import subprocess
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sch import parse, find, kicad_env  # noqa: E402

import pcbnew  # noqa: E402

sys.modules.setdefault("pcb", sys.modules[__name__])    # pcb_main imports this module by name

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPDIRS = {"woody": os.path.join(ROOT, "hardware", "lib", "woody.pretty")}
SYS_FP = "/usr/share/kicad/footprints"
JLC_ROTATION = os.path.join(ROOT, "hardware", "lib", "jlc-rotation.csv")   # per-LCSC-part CPL offsets
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
            if len(rest) > 3 and rest[2] == "smt_height_max":
                geo["smt_height_max"] = float(rest[3])
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
        fields = {find(f, "name")[0][1]: f[2] for fs in find(c, "fields") for f in find(fs, "field") if len(f) > 2}
        names = find(find(c, "sheetpath")[0], "names")[0][1].strip("/")
        comps[ref] = {"value": find(c, "value")[0][1], "footprint": fp[0][1] if fp else "",
                      "path": sp + (tst[0][1] if tst else ""),
                      # what a numeric reference is looked up by: its BOM row and the
                      # hierarchical sheet it sits on (a key's network is on sheet "LH1")
                      "row": fields.get("Row", ref), "sheet": names.rsplit("/", 1)[-1] if names else "",
                      "probe": fields.get("Probe", ""),
                      # the symbol's own "Exclude from BOM" and "Do not populate": the footprint carries both
                      "exclude_from_bom": "exclude_from_bom" in flags, "dnp": "dnp" in flags}
    nets = []
    for n in find(find(tree, "nets")[0], "net"):
        nets.append((find(n, "name")[0][1], [(find(x, "ref")[0][1], find(x, "pin")[0][1]) for x in find(n, "node")]))
    return comps, nets


def ref_of(comps, row, sheet=None):
    """The one reference on the board with this BOM row (and on this sheet, if given):
    references are plain numbers (R1, C6), so the tools find a part by what it is."""
    got = [r for r, c in comps.items() if c["row"] == row and (sheet is None or c["sheet"] == sheet)]
    if len(got) != 1:
        sys.exit(f"pcb: expected one {row}{' on sheet ' + sheet if sheet else ''}, found {got or 'none'}")
    return got[0]


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
    board.SetCopperLayerCount(int(lay.get("layers", 2)))
    # a plane layer is a POWER layer: KiCad's DSN export tells a router not to run
    # tracks on it, and the stackup names it so
    for pl in lay.get("planes") or []:
        board.SetLayerType(board.GetLayerID(pl["layer"]), pcbnew.LT_POWER)
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


def place_chain(board, fp, geo, bottom=True):
    """The chain header on the bottom, its mouth facing along the body the way
    the body CAD says: the rotation is FOUND, not assumed - on the bottom KiCad
    mirrors rotation, and the footprint's own frame puts the mouth at +x from
    pin 1's row (pads 1 -> 2 point at the mouth)."""
    (tx, ty), d = chain_target(geo)
    for rot in (0, 90, 180, 270):
        place(board, fp, 0, 0, rot, bottom)
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


def network_parts(lay, geo, comps):
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
                sys.exit(f"pcb: networks: pattern is written for switches at 0 deg; {key}'s switch is at {sr} - "
                         "give it an except: entry with its own `at`")
            x, y = sx + spec["offset"][0], sy + spec["offset"][1]
        out.update(t_parts(comps, key, x, y, spec))
    return out


def t_parts(comps, key, x, y, spec):
    """One key's T, its junction at body (x, y): the three parts' places, as network_parts
    describes (and a main board's spare positions, which have no switch, take directly)."""
    out = {}
    d, c = spec["leg"], spec["c"]
    if spec["axis"] == "x":
        rot = 0 if d > 0 else 180         # S's pad 1 (KEY) and P's pad 2 (KEY) toward the junction
        out[ref_of(comps, "R-KEY-SER", key)] = [x + d * NET_PITCH, y, rot]
        out[ref_of(comps, "R-KEY-PU", key)] = [x - d * NET_PITCH, y, rot]
        out[ref_of(comps, "C-KEY", key)] = [x, y + c * NET_PITCH, 270 if c > 0 else 90]
    else:
        rot = 90 if d > 0 else 270        # pad 1 faces -y at 90 and +y at 270 (measured through place())
        out[ref_of(comps, "R-KEY-SER", key)] = [x, y + d * NET_PITCH, rot]
        out[ref_of(comps, "R-KEY-PU", key)] = [x, y - d * NET_PITCH, rot]
        out[ref_of(comps, "C-KEY", key)] = [x + c * NET_PITCH, y, 0 if c > 0 else 180]
    return out


SILK_H, SILK_W = 1.0, 0.18     # silkscreen text height and stroke, mm: JLC's 1.0 minimum height, and a stroke over its 0.15 minimum near its preferred 1:6 (R3-8)


_TW, _TWB = {}, [None]


def text_w(text, h=SILK_H):
    """A silkscreen label's real width in mm, stroke included, measured on KiCad's own
    font: the per-character guess it replaces ran 15-35 % short on short labels, so
    labels checked as clear printed touching (3V3SH/LDSCK). Measured on the board being
    built (add_silk sets it): a new pcbnew.BOARD() makes KiCad's default project the
    current one, and the board then saves with default design rules."""
    if (text, h) not in _TW:
        t = pcbnew.PCB_TEXT(_TWB[0])
        t.SetText(text)
        t.SetTextSize(V(h, h))
        t.SetTextThickness(MM(SILK_W))
        _TW[(text, h)] = pcbnew.ToMM(t.GetBoundingBox().GetWidth())
    return _TW[(text, h)]


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
    # and a stroke nearer the board's edge than the silk clearance, or off it (a
    # connector whose body overhangs the edge on purpose: the main board's J-UMB)
    ol = pcbnew.SHAPE_POLY_SET()
    inside = shapely_of(ol).buffer(-gap) if board.GetBoardPolygonOutlines(ol) else None
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
            if any(p.IsOnLayer(side) and g.distance(pg) - pcbnew.ToMM(item.GetWidth()) / 2 < gap for p, pg in pads) \
                    or (inside is not None and not inside.contains(g.buffer(pcbnew.ToMM(item.GetWidth()) / 2))):
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


def add_silk(board, lay, comps):
    """The parts-side silkscreen, so the board can be assembled and probed by
    hand: every part's reference (R1, C1, U1, J1, TP1), each OFF every part body
    and pad on this side, so it can still be read with the parts fitted
    (check_silk holds that). Each key's network carries its three references the
    same way round the T, and the key's name beside it; each test pad its
    reference and what it probes (its Probe field)."""
    _TWB[0] = board
    def box(fp):
        b = fp.GetCourtyard(pcbnew.B_CrtYd).BBox()
        return pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom())
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

    def put(text, x, y, justify=0, angle=0):
        """Every label goes through here, so each later one keeps off it."""
        w = text_w(text)
        if angle % 180:
            placed_txt.append((x - SILK_H / 2, y - w / 2, x + SILK_H / 2, y + w / 2))
        else:
            a0 = x - w / 2 if justify == 0 else (x - w if justify == 1 else x)
            placed_txt.append((a0, y - SILK_H / 2, a0 + w, y + SILK_H / 2))
        silk_text(board, text, x, y, justify=justify, angle=angle)

    def free(a0, b0, a1, b1, m=0.25):
        """clear(), and off every label already placed by m: the board house's silk-to-silk
        clearance, with room for the stroke font's glyphs running wider than the estimate."""
        return clear(a0, b0, a1, b1) and not any(a0 < t[2] + m and a1 > t[0] - m and b0 < t[3] + m and b1 > t[1] - m for t in placed_txt)

    def beside(x0, y0, x1, y1, text, under_first=False):
        """A short label over the part, else under it, else to either side:
        the first place off every courtyard and every label already placed."""
        w, h = text_w(text) / 2, SILK_H / 2
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        spots = [(cx, y0 - SILK_H * 0.75), (cx, y1 + SILK_H * 0.75), (x0 - 0.4 - w, cy), (x1 + 0.4 + w, cy)]
        if under_first:
            spots[0], spots[1] = spots[1], spots[0]
        for px, py in spots:
            if free(px - w, py - h, px + w, py + h):
                return px, py, 0, 0
        # then reading along the part: at either side of it, or over or under it
        for px, py in ((x0 - 0.4 - h, cy), (x1 + 0.4 + h, cy), (cx, y0 - 0.3 - w), (cx, y1 + 0.3 + w)):
            if free(px - h, py - w, px + h, py + w):
                return px, py, 0, 90
        near_ = [tuple(round(v, 1) for v in c) for c in crt + placed_txt
                 if c[0] < x1 + 4 and c[2] > x0 - 4 and c[1] < y1 + 4 and c[3] > y0 - 4]
        sys.exit(f"pcb: no clear place for the silkscreen label {text!r} at ({cx:.1f}, {cy:.1f}), part box "
                 f"{tuple(round(v, 1) for v in (x0, y0, x1, y1))}; nearby: {near_} - move parts in layout.yaml")
    above_or_below = beside
    def fixed(text, x, y, angle=0):
        w, h = text_w(text) / 2, SILK_H / 2
        if angle % 180:
            w, h = h, w
        if not free(x - w, y - h, x + w, y + h):
            a0, b0, a1, b1 = x - w, y - h, x + w, y + h
            hit = [c for c in crt if a0 < c[2] and a1 > c[0] and b0 < c[3] and b1 > c[1]] + \
                  [t for t in placed_txt if a0 < t[2] + 0.25 and a1 > t[0] - 0.25 and b0 < t[3] + 0.25 and b1 > t[1] - 0.25]
            outside = not (a0 >= ex0 and b0 >= ey0 and a1 <= ex1 and b1 <= ey1)
            sys.exit(f"pcb: the label {text!r} at ({x:.1f}, {y:.1f}) is not clear "
                     f"({'off the board edge; ' if outside else ''}in the way: {[tuple(round(v, 1) for v in h) for h in hit]}) - every key's labels sit "
                     "the same way round its network; move the part in the way, or the pattern (layout.yaml networks:)")
        put(text, x, y, angle=angle)
    def near(fp, text, d, angle=0):
        """A point beside fp's courtyard in direction d (a unit axis vector), with the
        text's own half-size and a 0.3 mm gap between them."""
        x0, y0, x1, y1 = box(fp)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        w, h = text_w(text) / 2, SILK_H / 2
        if angle % 180:
            w, h = h, w
        if abs(d[0]) > abs(d[1]):
            return (x1 + 0.3 + w if d[0] > 0 else x0 - 0.3 - w), cy
        return cx, (y1 + 0.3 + h if d[1] > 0 else y0 - 0.3 - h)

    def unit(dx, dy):
        n = math.hypot(dx, dy)
        return dx / n, dy / n

    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    keys = sorted({c["sheet"] for c in comps.values() if c["row"] == "SW1-n"})
    for key in keys:
        # A T (network_parts): every key's labels the same way round it. S's and P's
        # references outside the column, away from C; C's on the S side of C, the
        # key's name on the P side of it.
        f = {row: fps[ref_of(comps, row, key)] for row in ("R-KEY-SER", "R-KEY-PU", "C-KEY")}
        xy = {k: (pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y)) for k, v in f.items()}
        jx, jy = (xy["R-KEY-SER"][0] + xy["R-KEY-PU"][0]) / 2, (xy["R-KEY-SER"][1] + xy["R-KEY-PU"][1]) / 2
        u = unit(xy["C-KEY"][0] - jx, xy["C-KEY"][1] - jy)          # junction -> C
        a = unit(xy["R-KEY-PU"][0] - jx, xy["R-KEY-PU"][1] - jy)    # junction -> P
        # S's and P's references read along the parts, beside the column: across
        # it they would reach the switch's pins
        ang = 90 if abs(a[1]) > abs(a[0]) else 0
        for row in ("R-KEY-SER", "R-KEY-PU"):
            fixed(f[row].GetReference(), *near(f[row], f[row].GetReference(), (-u[0], -u[1]), ang), angle=ang)
        fixed(f["C-KEY"].GetReference(), *near(f["C-KEY"], f["C-KEY"].GetReference(), (-a[0], -a[1])))
        fixed(key, *near(f["C-KEY"], key, a))
    # fixed-place marks first - the test pads' labels, J-CHAIN's dot and arrow - so
    # every searched label keeps off them
    order = lambda fp: (comps.get(fp.GetReference(), {}).get("row") != "TP-CHAIN", comps.get(fp.GetReference(), {}).get("row") != "J-CHAIN")
    tp_row = [f.GetReference() for f in sorted((f for f in board.GetFootprints() if comps.get(f.GetReference(), {}).get("row") == "TP-CHAIN"),
                                                key=lambda f: f.GetPosition().x)]
    for fp in sorted(board.GetFootprints(), key=order):
        ref = fp.GetReference()
        c = comps.get(ref)
        if c is None or c["row"] in ("R-KEY-SER", "C-KEY", "SW1-n") or (c["row"] == "R-KEY-PU" and c["sheet"] in keys):
            continue                                   # mounting holes; the key networks, labelled above; switches (top)
        x0, y0, x1, y1 = box(fp) if fp.GetCourtyard(pcbnew.B_CrtYd).OutlineCount() else (0, 0, 0, 0)
        if c["row"] == "TP-CHAIN":
            # test pads sit in a row: each one's reference under it and over it by
            # turns, so side by side on either side they are two pads apart; what each
            # probes is in the legend (below)
            cx = (x0 + x1) / 2
            fixed(ref, cx, (y1 + SILK_H * 0.75) if tp_row.index(ref) % 2 == 0 else (y0 - SILK_H * 0.75))
        elif c["row"] == "J-CHAIN":
            p1 = fp.FindPadByNumber("1").GetPosition()
            p2 = fp.FindPadByNumber("2").GetPosition()
            # pin 1's dot outside the pad array, away from the mouth
            dx = pcbnew.ToMM(p1.x - p2.x)
            # from pad 1's copper edge, not its hole: the pads are lengthened outward
            pb = fp.FindPadByNumber("1").GetBoundingBox()
            dxd = pcbnew.ToMM(pb.GetRight()) + 0.765 if dx > 0 else pcbnew.ToMM(pb.GetLeft()) - 0.765
            silk_dot(board, dxd, pcbnew.ToMM(p1.y))   # its edge 0.39 off the pad: fab silk_to_pad
            placed_txt.append((dxd - 0.6, pcbnew.ToMM(p1.y) - 0.6, dxd + 0.6, pcbnew.ToMM(p1.y) + 0.6))
            put(ref, *above_or_below(x0, y0, x1, y1, ref))
            # which way its mouth faces: pads 1 -> 2 point at it (place_chain); a
            # header soldered backward puts 3V3 on a ground pin (key-chain-loom.md)
            mx = pcbnew.ToMM(p2.x - p1.x) > 0
            ax = x1 + 1.2 if mx else x0 - 1.2
            silk_arrow(board, ax, (y0 + y1) / 2, 1 if mx else -1)
            placed_txt.append((ax - 0.9, (y0 + y1) / 2 - 0.9, ax + 0.9, (y0 + y1) / 2 + 0.9))
        else:
            # everything else: its reference, with DNP where it is not fitted
            text = ref + (" DNP" if fp.IsDNP() else "")
            # a DNP part's label under it: over it, it reads as J-CHAIN's, whose pads are beside
            put(text, *beside(x0, y0, x1, y1, text, under_first=fp.IsDNP()))
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
        if t.get("legend_at") and tp_row:
            # what each test pad probes, by reference, three to a line
            items = [f"{r} {comps[r]['probe'] or '?'}" for r in sorted(tp_row, key=lambda r: int(re.sub(r'\D', '', r) or 0))]
            x, y = to_pcb(*t["legend_at"])
            for i in range(0, len(items), 3):
                line = "  ".join(items[i:i + 3])
                yy = y + (i // 3) * SILK_H * 1.8
                if not free(x - 0.2, yy - SILK_H / 2, x + text_w(line) + 0.2, yy + SILK_H / 2):
                    sys.exit(f"pcb: the test pads' legend at layout.yaml silk.legend_at is not clear: {line!r}")
                put(line, x, yy, justify=-1)


def add_top_silk(board, lay, comps):
    """The switch side's silkscreen. J-CHAIN is soldered from this side and the
    board is lowered onto the switch pins top first, so it carries each key's name
    and reference beside its switch (off its body), J-CHAIN's reference, pin 1 and the way its mouth faces, the MOUTH end,
    and the board's title and revision. Not mirrored: it reads from above."""
    _TWB[0] = board
    for fp in board.GetFootprints():
        fp.BuildCourtyardCaches()   # read below; LoadBoard leaves them empty on some 9.0.x (#9 G2, G9)
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
        w = text_w(text)
        placed.append((x - w / 2, y - SILK_H / 2, x + w / 2, y + SILK_H / 2))
        silk_text(board, text, x, y, top=True)

    def beside(x0, y0, x1, y1, text):
        w, h = text_w(text) / 2, SILK_H / 2
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for px, py in ((cx, y0 - SILK_H * 0.75), (cx, y1 + SILK_H * 0.75), (x0 - 0.4 - w, cy), (x1 + 0.4 + w, cy)):
            if free(px - w, py - h, px + w, py + h):
                return px, py
        sys.exit(f"pcb: no clear place on the top silkscreen for {text!r} at ({cx:.1f}, {cy:.1f}) - move parts in layout.yaml")
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        row = comps.get(ref, {}).get("row")
        if row == "SW1-n":
            b = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            text = f"{ref} {comps[ref]['sheet']}"          # SW1 LH1: the reference, and the key it is
            put(text, *beside(pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom()), text))
        elif row == "J-CHAIN":
            p1, p2 = fp.FindPadByNumber("1").GetPosition(), fp.FindPadByNumber("2").GetPosition()
            dx = pcbnew.ToMM(p1.x - p2.x)
            # measured from the pads' copper, not their holes: the pads are lengthened outward
            pb = fp.FindPadByNumber("1").GetBoundingBox()
            silk_dot(board, pcbnew.ToMM(pb.GetRight()) + 0.765 if dx > 0 else pcbnew.ToMM(pb.GetLeft()) - 0.765, pcbnew.ToMM(p1.y), top=True)
            bb = [p.GetBoundingBox() for p in fp.Pads()]
            x0, x1 = min(pcbnew.ToMM(b.GetLeft()) for b in bb) - 0.265, max(pcbnew.ToMM(b.GetRight()) for b in bb) + 0.265
            y0, y1 = min(pcbnew.ToMM(b.GetTop()) for b in bb) - 0.265, max(pcbnew.ToMM(b.GetBottom()) for b in bb) + 0.265
            put(ref, *beside(x0, y0, x1, y1, ref))
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
            w = text_w(line)
            if not free(x, y + i * SILK_H * 1.8 - SILK_H / 2, x + w, y + i * SILK_H * 1.8 + SILK_H / 2):
                sys.exit(f"pcb: the top silkscreen title at layout.yaml silk.top_at is not clear: {line!r}")
            placed.append((x, y + i * SILK_H * 1.8 - SILK_H / 2, x + w, y + i * SILK_H * 1.8 + SILK_H / 2))
            silk_text(board, line, x, y + i * SILK_H * 1.8, top=True, justify=-1)


def add_silk_generic(board, lay, comps):
    """A board's silkscreen without a key board's fixed patterns (the main board): every
    part's reference beside it on its own face - over it, under it, then to either side,
    then reading along it - off every courtyard, pad and hole on that face and 0.25 mm off
    every other label; a switch's with the key it is (SW1 LT1); the title block at
    layout.yaml silk: `at` on the parts' face. A reference with no clear place is left
    off and named (not fatal: the fab layer still carries it), so a crowded corner is
    visible rather than silently unlabelled."""
    _TWB[0] = board
    for fp in board.GetFootprints():
        fp.BuildCourtyardCaches()   # read below; LoadBoard leaves them empty on some 9.0.x (#9 G2, G9)
    edge = board.GetBoardEdgesBoundingBox()
    ol = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(ol)
    inside = shapely_of(ol).buffer(-0.5)
    from shapely.geometry import box as _box
    from shapely.strtree import STRtree
    keep = {True: [], False: []}          # top face?, boxes
    for fp in board.GetFootprints():
        for it in fp.GraphicalItems():
            if it.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                b = it.GetBoundingBox()
                keep[it.GetLayer() == pcbnew.F_SilkS].append(_box(pcbnew.ToMM(b.GetLeft()) - 0.3, pcbnew.ToMM(b.GetTop()) - 0.3,
                                                                   pcbnew.ToMM(b.GetRight()) + 0.3, pcbnew.ToMM(b.GetBottom()) + 0.3))
        for top, cl in ((True, pcbnew.F_CrtYd), (False, pcbnew.B_CrtYd)):
            cy = fp.GetCourtyard(cl)
            if cy.OutlineCount():
                b = cy.BBox()
                keep[top].append(_box(pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom())))
        for p in fp.Pads():
            b, m = p.GetBoundingBox(), 0.3
            g = _box(pcbnew.ToMM(b.GetLeft()) - m, pcbnew.ToMM(b.GetTop()) - m, pcbnew.ToMM(b.GetRight()) + m, pcbnew.ToMM(b.GetBottom()) + m)
            for top, L in ((True, pcbnew.F_Cu), (False, pcbnew.B_Cu)):
                if p.IsOnLayer(L) or p.HasHole():
                    keep[top].append(g)
    # the vias, where the board is routed: silk on one prints onto its tent
    for v in board.GetTracks():
        if isinstance(v, pcbnew.PCB_VIA):
            c, r = v.GetPosition(), pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)) / 2 + 0.1
            for top in (True, False):
                keep[top].append(_box(pcbnew.ToMM(c.x) - r, pcbnew.ToMM(c.y) - r, pcbnew.ToMM(c.x) + r, pcbnew.ToMM(c.y) + r))
    trees = {t: STRtree(v) for t, v in keep.items()}
    placed = {True: [], False: []}
    skipped = []

    def free(top, g):
        if not inside.contains(g):
            return False
        if any(g.intersects(keep[top][i]) for i in trees[top].query(g)):
            return False
        return not any(g.distance(t) < 0.25 for t in placed[top])

    def put(top, text, x, y, angle=0, justify=0):
        silk_text(board, text, x, y, top=top, angle=angle, justify=justify)

    # the title block first, where layout.yaml puts it; the references then keep off it
    t = lay.get("silk", {})
    if t:
        tb = board.GetTitleBlock()
        tb.SetTitle(t["title"])
        tb.SetRevision(t["rev"])
        tb.SetDate(t["date"])
        board.SetTitleBlock(tb)
        # silk.at: one place, or a list of places tried in turn (the first clear one)
        ats = t["at"] if isinstance(t["at"][0], (list, tuple)) else [t["at"]]
        lines = [t["title"], f"rev {t['rev']}  {t['date']}"]
        for at in ats:
            x, y = to_pcb(*at)
            boxes = [_box(x, y + i * SILK_H * 1.8 - SILK_H / 2, x + text_w(line), y + i * SILK_H * 1.8 + SILK_H / 2) for i, line in enumerate(lines)]
            if all(free(True, g) for g in boxes):
                break
        else:
            if not t.get("search"):
                sys.exit(f"pcb: the silkscreen title at layout.yaml silk.at is not clear: {lines[0]!r}")
            # silk.search: the first clear place on a 0.5 mm scan of the board, top down
            bb = board.GetBoardEdgesBoundingBox()
            found = None
            for face in (True, False):          # the top face first, then the rear
                yy = pcbnew.ToMM(bb.GetTop()) + 1.0
                while found is None and yy < pcbnew.ToMM(bb.GetBottom()) - 3:
                    xx = pcbnew.ToMM(bb.GetLeft()) + 1.0
                    while xx < pcbnew.ToMM(bb.GetRight()) - 5:
                        # on the rear the text is mirrored: it runs leftward from its anchor
                        boxes = [_box(xx, yy + i * SILK_H * 1.8 - SILK_H / 2, xx + text_w(line), yy + i * SILK_H * 1.8 + SILK_H / 2) for i, line in enumerate(lines)]
                        if all(free(face, g) for g in boxes):
                            found = (xx, yy, face)
                            break
                        xx += 0.5
                    yy += 0.5
                if found:
                    break
            if found is None:
                sys.exit(f"pcb: no clear place on either silkscreen for the title {lines[0]!r}")
            x, y, tface = found
            print(f"pcb: silk - the title placed at the first clear place on the {'top' if tface else 'rear'}")
            for i, (line, g) in enumerate(zip(lines, boxes)):
                put(tface, line, x + (0 if tface else text_w(line)), y + i * SILK_H * 1.8, justify=-1)
                placed[tface].append(g)
            lines = []
        for i, (line, g) in enumerate(zip(lines, boxes)):
            put(True, line, x, y + i * SILK_H * 1.8, justify=-1)
            placed[True].append(g)
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        c = comps.get(ref)
        if c is None:
            continue                                    # the mounts: board-only, no symbol
        top = not fp.IsFlipped()
        text = f"{ref} {c['sheet']}" if c["row"] == "SW1-n" else ref + (" DNP" if fp.IsDNP() else "")
        cy = fp.GetCourtyard(pcbnew.F_CrtYd if top else pcbnew.B_CrtYd)
        b = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False, False)
        x0, y0, x1, y1 = pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom())
        w, h = text_w(text) / 2, SILK_H / 2
        cx, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
        spots = [(cx, y0 - 0.2 - h, 0), (cx, y1 + 0.2 + h, 0), (x0 - 0.3 - w, cy_, 0), (x1 + 0.3 + w, cy_, 0),
                 (x0 - 0.3 - h, cy_, 90), (x1 + 0.3 + h, cy_, 90), (cx, y0 - 0.3 - w, 90), (cx, y1 + 0.3 + w, 90)]
        for px, py, ang in spots:
            g = _box(px - w, py - h, px + w, py + h) if not ang else _box(px - h, py - w, px + h, py + w)
            if free(top, g):
                put(top, text, px, py, ang)
                placed[top].append(g)
                break
        else:
            skipped.append(ref)
    # every label placed, proved as check_silk will judge it - its real stroked shape,
    # not its box, off every courtyard on its face and the board house's silk clearance
    # off every footprint's own silk; one that fails comes off and is named with the rest
    bodies = {True: [], False: []}
    fsilk = {True: [], False: []}
    for fp in board.GetFootprints():
        for top, cl in ((True, pcbnew.F_CrtYd), (False, pcbnew.B_CrtYd)):
            if fp.GetCourtyard(cl).OutlineCount():
                bodies[top].append(shapely_of(fp.GetCourtyard(cl)))
        for it in fp.GraphicalItems():
            if it.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                fsilk[it.GetLayer() == pcbnew.F_SilkS].append(item_shape(it, it.GetLayer()))
    gap = float((lay.get("fab") or {}).get("silk_to_pad", 0.15))
    for d in list(board.GetDrawings()):
        if not isinstance(d, pcbnew.PCB_TEXT) or d.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        top = d.GetLayer() == pcbnew.F_SilkS
        g = item_shape(d, d.GetLayer())
        if any(g.intersects(b_) and g.intersection(b_).area > 1e-4 for b_ in bodies[top]) \
                or any(g.distance(f_) < gap for f_ in fsilk[top]):
            skipped.append(d.GetText().split(" ")[0])
            board.Delete(d)
    if skipped:
        print(f"pcb: silk - no clear place for {len(skipped)} reference(s), left on the fab layer only: {', '.join(sorted(skipped))}")


def post_route(path, bdir):
    """A routed multi-layer board (route: freerouting), saved at `path` with its zones
    filled: the tracks tidied (pcb_route.tidy); every connection KiCad still counts
    missing tried once more (pcb_route.complete); then its silkscreen - after routing, so
    every label keeps off every via, which the autorouter cannot see - and any stroke of
    a footprint's own silk on a via removed, named."""
    import pcb_route
    name = os.path.basename(bdir)
    lay = layout_yaml(bdir)
    comps, _ = sheet_netlist(os.path.join(bdir, name + ".kicad_sch"))
    board = pcbnew.LoadBoard(path)
    orphans = pcb_route.plane_orphans(board, lay)
    if orphans:
        # a plane pad its plane's fill cannot reach (antipads all round it): its own via
        pcb_route.fanout(board, lay, pcb_route.Obstacles(board, lay), only=orphans)
    pcb_route.tidy(board, lay)
    pcbnew.SaveBoard(path, board)
    # the shortest connections first: they have the fewest ways round (a long run they
    # wall in gets through by complete's rip-up, layout.yaml rip_up:)
    miss = sorted(unconnected_of(path), key=lambda m: math.dist(m[1], m[2]))
    board = pcbnew.LoadBoard(path)
    failed = pcb_route.complete(board, lay, miss)
    print(f"route: complete - {len(miss) - len(failed)} of {len(miss)} connection(s) the autorouter left, routed")
    # tidy on the board as saved, loaded afresh: run in the process that just laid the
    # tracks it took hundreds of them for dangling and left a board KiCad's filler crashed on
    pcbnew.SaveBoard(path, board)
    board = pcbnew.LoadBoard(path)
    pcb_route.tidy(board, lay)
    if failed and not lay.get("rip_up"):
        # what complete could not route: rip-up, kept only where DRC counts fewer problems
        # (a board with complete's own rip-up, layout.yaml rip_up:, has had its chance)
        pcbnew.SaveBoard(path, board)
        _fill(path)
        print(f"route: rescue - {rescue(path, bdir)} kept")
        board = pcbnew.LoadBoard(path)
        pcb_route.tidy(board, lay)
    add_silk_generic(board, lay, comps)
    silk_off_vias(board)
    pcbnew.SaveBoard(path, board)


def silk_off_vias(board):
    """Any stroke of a footprint's own silkscreen over a via, removed and named: the
    legend would print onto a tented hole."""
    from shapely.geometry import Point as _P
    vias = [_P(pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y)).buffer(pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)) / 2)
            for v in board.GetTracks() if isinstance(v, pcbnew.PCB_VIA)]
    gone = {}
    for fp in board.GetFootprints():
        try:
            items = list(fp.GraphicalItems())
        except TypeError:
            continue        # a footprint with no drawings left: KiCad 9's SWIG hands back a bare object
        for it in items:
            if it.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and isinstance(it, pcbnew.PCB_SHAPE):
                try:
                    g = item_shape(it, it.GetLayer())
                except AttributeError:
                    continue        # a stroke KiCad 9's SWIG cannot hand back as a polygon
                if any(g.intersects(v) for v in vias):
                    fp.Remove(it)
                    gone.setdefault(fp.GetReference(), 0)
                    gone[fp.GetReference()] += 1
    if gone:
        print("pcb: silk adapted - library silk on a via removed: " + ", ".join(f"{r} ({n})" for r, n in sorted(gone.items())))


def cmd_update_footprints(bdir, only, resized=False):
    """`update-footprints <board> <ref or footprint name>...`: each named footprint on the
    board replaced by the library's current one, in the same place, side and turn, with
    its reference, value, sheet path, BOM and DNP flags, its fields' placing and its pads'
    nets - KiCad's "update footprint from library" for a board that is the source now.
    Refused where the new footprint's pads differ in number, place or size (the copper
    would no longer meet them: re-route instead). Then the board house's silk fitting and
    silk off every via again. Copper and tracks are not touched."""
    name = os.path.basename(bdir)
    path = os.path.join(bdir, name + ".kicad_pcb")
    lay = layout_yaml(bdir)
    board = pcbnew.LoadBoard(path)
    done = []
    for fp in list(board.GetFootprints()):
        lib = fp.GetFPID().GetLibNickname().wx_str()
        item = fp.GetFPID().GetLibItemName().wx_str()
        if fp.GetReference() not in only and item not in only:
            continue
        new = load_fp(f"{lib}:{item}")
        board.Add(new)
        pos = fp.GetPosition()
        new.SetPosition(pos)
        if fp.IsFlipped():
            new.Flip(pos, pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        new.SetOrientation(fp.GetOrientation())
        geo = lambda f: sorted((p.GetNumber(), p.GetPosition().x, p.GetPosition().y) + (() if resized else
                               (p.GetSize(p.GetPrincipalLayer()).x, p.GetSize(p.GetPrincipalLayer()).y)) for p in f.Pads())
        if geo(new) != geo(fp):
            board.Delete(new)
            sys.exit(f"pcb: {fp.GetReference()}'s library footprint {lib}:{item} has moved or resized pads - "
                     f"re-route it (pcb.py layout), an update would leave its copper short; pads only resized "
                     f"in place: --pads-resized, then check (a track now too near a bigger pad is a DRC error)")
        new.SetReference(fp.GetReference())
        new.SetValue(fp.GetValue())
        for a, b in ((fp.Reference(), new.Reference()), (fp.Value(), new.Value())):
            b.SetLayer(a.GetLayer())
            b.SetTextSize(a.GetTextSize())
            b.SetTextThickness(a.GetTextThickness())
            b.SetPosition(a.GetPosition())
            b.SetTextAngle(a.GetTextAngle())
            b.SetVisible(a.IsVisible())
        new.SetPath(fp.GetPath())
        new.SetExcludedFromBOM(fp.IsExcludedFromBOM())
        new.SetDNP(fp.IsDNP())
        new.SetExcludedFromPosFiles(fp.IsExcludedFromPosFiles())
        new.SetLocked(fp.IsLocked())
        nets = {p.GetNumber(): p.GetNet() for p in fp.Pads()}
        for p in new.Pads():
            if p.GetNumber() in nets:
                p.SetNet(nets[p.GetNumber()])
        # a model's board-specific lift (the thumb switches') stays; its file and turn are the library's
        old_m, new_m = fp.Models(), new.Models()
        for i in range(min(len(old_m), len(new_m))):
            if old_m[i].m_Filename == new_m[i].m_Filename:
                new_m[i].m_Offset = old_m[i].m_Offset
        board.Delete(fp)
        done.append(new.GetReference())
    if not done:
        sys.exit(f"pcb: no footprint on {name} is {', '.join(only)}")
    if lay.get("fab"):
        fit_footprint_silk(board, lay["fab"])
    silk_off_vias(board)
    pcbnew.SaveBoard(path, board)
    print(f"pcb: {len(done)} footprint(s) updated from the library: {', '.join(sorted(done))}")


def unconnected_of(path):
    """KiCad's own list of what is missing on a saved board: (net, (x, y), (x, y)), the
    two copper items' positions from its DRC."""
    miss = []
    for v in drc(path).get("unconnected_items", []):
        it = v.get("items", [])
        m = re.search(r"\[([^\]]+)\]", it[0]["description"]) if len(it) == 2 else None
        if m:
            miss.append((m.group(1), (it[0]["pos"]["x"], it[0]["pos"]["y"]), (it[1]["pos"]["x"], it[1]["pos"]["y"])))
    return miss


def _fill(path):
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {here!r}); "
                    f"import pcb_route; pcb_route.fill_zones({path!r})"], check=True)


def rescue(path, bdir, radii=(1.5, 3.0, 5.0)):
    """Rip-up for what pcb_route.complete could not route, on a saved, filled board: for
    each connection still missing, the unlocked tracks and vias of OTHER nets within
    `radii` of it (never a plane net's, never locked copper: the pair and the fanout) are
    taken up, the missing connection routed first, then everything that left missing
    routed again (complete) and tidied. The result is kept only if KiCad's DRC then
    counts fewer problems - unconnected items and violations together - than before;
    otherwise the board is left as it was. Returns how many were kept."""
    import pcb_route
    from shapely.geometry import Point, box
    lay = layout_yaml(bdir)
    planes = set(lay.get("fanout") or []) | {pl["net"] for pl in lay.get("planes") or []}
    score = lambda p: (lambda d: len(d.get("unconnected_items", [])) + len(d.get("violations", [])))(drc(p))
    base, kept, tried = score(path), 0, set()
    # the trial board beside its own project file, so DRC reads the same rules
    tdir = tempfile.mkdtemp(prefix=".rescue-", dir=os.path.dirname(path))
    tmp = os.path.join(tdir, os.path.basename(path))
    for f in (path[:-len(".kicad_pcb")] + ".kicad_pro", os.path.join(bdir, "fp-lib-table"), os.path.join(bdir, "sym-lib-table")):
        if os.path.exists(f):
            shutil.copy(f, tdir)
    try:
        progress = True
        while progress:
            progress = False
            for net, pa, pb in unconnected_of(path):
                key = (net, round(pa[0], 1), round(pa[1], 1), round(pb[0], 1), round(pb[1], 1))
                if key in tried:
                    continue
                tried.add(key)
                for r in radii:
                    board = pcbnew.LoadBoard(path)
                    # round its two ends - where a connection is walled in - and, for a short
                    # hop, the ground between them
                    region = Point(pa).buffer(r).union(Point(pb).buffer(r))
                    if math.dist(pa, pb) < 10:
                        region = region.union(box(min(pa[0], pb[0]), min(pa[1], pb[1]), max(pa[0], pb[0]), max(pa[1], pb[1])).buffer(r))
                    victims = []
                    for t in board.GetTracks():
                        if t.IsLocked() or t.GetNetname() in planes or t.GetNetname() == net:
                            continue
                        bb = t.GetBoundingBox()
                        if region.intersects(box(bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6)):
                            victims.append(t)
                    if not victims:
                        continue
                    hit, nv = {t.GetNetname() for t in victims}, len(victims)
                    for t in victims:
                        board.Delete(t)
                    if pcb_route.complete(board, lay, [(net, pa, pb)]):
                        continue
                    try:
                        pcbnew.SaveBoard(tmp, board)
                        _fill(tmp)
                        b2 = pcbnew.LoadBoard(tmp)
                        pcb_route.complete(b2, lay, [m for m in unconnected_of(tmp) if m[0] in hit])
                        pcb_route.tidy(b2, lay)
                        pcbnew.SaveBoard(tmp, b2)
                        _fill(tmp)
                    except subprocess.CalledProcessError:
                        continue        # a trial the filler crashed on (KiCad 9 can segfault) is dropped
                    s2 = score(tmp)
                    if s2 < base:
                        print(f"route: rescue - {net} ({pa[0]:.1f}, {pa[1]:.1f}): {nv} item(s) taken up within {r} mm "
                              f"and routed again; problems {base} -> {s2}", flush=True)
                        os.replace(tmp, path)
                        base, kept, progress = s2, kept + 1, True
                        break
                if progress:
                    break           # the list moved: read it again
    finally:
        shutil.rmtree(tdir, ignore_errors=True)
    return kept


def cmd_route(bdir, chunk=30):
    """`route <board>`: route a placed board IN PLACE, in steps that each save the board,
    so a run that is killed (a container restart) resumes where it stopped: run it again.
    For a board laid out with `layout --no-route`. In order, each done once: the pairs,
    moat keep-outs, plane fanout and connect_first (pcb_route.prepare); then every
    connection KiCad still counts missing, shortest first, by pcb_route.complete in
    chunks, the zones filled and the board saved after each; then tidy, rip-up rescue
    of what is left, the silkscreen (clear of every via) and the stackup. Prints what is
    still unconnected; check fails on each."""
    import json
    import pcb_route
    name = os.path.basename(bdir)
    path = os.path.join(bdir, name + ".kicad_pcb")
    lay = layout_yaml(bdir)
    comps, _ = sheet_netlist(os.path.join(bdir, name + ".kicad_sch"))
    board = pcbnew.LoadBoard(path)
    if not any(type(t) is pcbnew.PCB_TRACK for t in board.GetTracks()):     # a guard's locked via is not routing
        pcb_route.prepare(board, lay)
        pcbnew.SaveBoard(path, board)
        print("route: prepared (pairs, fanout, connect_first) - saved", flush=True)
    if lay.get("escape"):
        board = pcbnew.LoadBoard(path)
        pcb_route.escape(board, lay)        # idempotent: a pad already left is skipped
        pcbnew.SaveBoard(path, board)
    _fill(path)
    tried = set()
    while True:
        # route_first: nets a crowded corner needs before its neighbours take the room
        first = {n.lstrip("/") for n in lay.get("route_first") or []}
        miss = sorted((m for m in unconnected_of(path) if (m[0], round(m[1][0], 1), round(m[1][1], 1), round(m[2][0], 1), round(m[2][1], 1)) not in tried),
                      key=lambda m: (m[0].lstrip("/") not in first, math.dist(m[1], m[2])))
        if not miss:
            break
        batch = miss[:chunk]
        for m in batch:
            tried.add((m[0], round(m[1][0], 1), round(m[1][1], 1), round(m[2][0], 1), round(m[2][1], 1)))
        board = pcbnew.LoadBoard(path)
        failed = pcb_route.complete(board, lay, batch)
        pcbnew.SaveBoard(path, board)
        board = pcbnew.LoadBoard(path)          # tidy on a fresh load (post_route says why)
        pcb_route.tidy(board, lay)
        pcbnew.SaveBoard(path, board)
        _fill(path)
        print(f"route: {len(batch) - len(failed)} of {len(batch)} routed this step; saved", flush=True)
    left = unconnected_of(path)
    if left and not lay.get("no_rescue"):
        print(f"route: rescue - {rescue(path, bdir)} kept", flush=True)
    board = pcbnew.LoadBoard(path)
    pcb_route.tidy(board, lay)
    for d in list(board.GetDrawings()):
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            board.Delete(d)                     # the labels again, clear of the vias as they now stand
    add_silk_generic(board, lay, comps)
    silk_off_vias(board)
    pcbnew.SaveBoard(path, board)
    _fill(path)
    if lay.get("fab"):
        set_stackup(path, lay["fab"], pcbnew.LoadBoard(path).GetDesignSettings().GetBoardThickness() / 1e6, lay.get("stackup"))
    left = sorted({"; ".join(i["description"] for i in v.get("items", [])) for v in drc(path).get("unconnected_items", [])})
    print(f"pcb: {len(left)} connection(s) left for hand routing" + (":" if left else ""))
    for u in left:
        print("  " + u)
    print(f"pcb: wrote {os.path.relpath(path, ROOT)}")


def cmd_finish(bdir):
    """A routed board's missing connections tried again, in place: tidy, complete, then
    rescue (rip-up), zones refilled. For a re-run after hand edits, or after a layout
    left connections for hand routing; it never adds or moves a part."""
    import pcb_route
    name = os.path.basename(bdir)
    path = os.path.join(bdir, name + ".kicad_pcb")
    lay = layout_yaml(bdir)
    t = tempfile.mkdtemp(prefix=".finish-", dir=bdir)
    try:
        tmp = os.path.join(t, name + ".kicad_pcb")
        shutil.copy(path, tmp)
        shutil.copy(os.path.join(bdir, name + ".kicad_pro"), os.path.join(t, name + ".kicad_pro"))
        for f in ("fp-lib-table", "sym-lib-table"):
            if os.path.exists(os.path.join(bdir, f)):
                shutil.copy(os.path.join(bdir, f), os.path.join(t, f))
        board = pcbnew.LoadBoard(tmp)
        orphans = pcb_route.plane_orphans(board, lay)
        if orphans:
            pcb_route.fanout(board, lay, pcb_route.Obstacles(board, lay), only=orphans)
        new = pcb_route.unfanned(board, lay)
        if new:
            # a plane pad moved or added since the layout: its own via, as the fanout gives
            pcb_route.fanout(board, lay, pcb_route.Obstacles(board, lay), only=new)
        pcb_route.tidy(board, lay)
        pcbnew.SaveBoard(tmp, board)
        _fill(tmp)
        miss = unconnected_of(tmp)
        board = pcbnew.LoadBoard(tmp)
        failed = pcb_route.complete(board, lay, miss)
        print(f"route: complete - {len(miss) - len(failed)} of {len(miss)} connection(s) routed")
        pcbnew.SaveBoard(tmp, board)
        board = pcbnew.LoadBoard(tmp)        # tidy on a fresh load (post_route says why)
        pcb_route.tidy(board, lay)
        pcbnew.SaveBoard(tmp, board)
        _fill(tmp)
        if not lay.get("rip_up"):
            print(f"route: rescue - {rescue(tmp, bdir)} kept")
        left = sorted({"; ".join(i["description"] for i in v.get("items", [])) for v in drc(tmp).get("unconnected_items", [])})
        os.replace(tmp, path)
    finally:
        shutil.rmtree(t, ignore_errors=True)
    print(f"pcb: {len(left)} connection(s) left for hand routing" + (":" if left else ""))
    for u in left:
        print("  " + u)
    print(f"pcb: wrote {os.path.relpath(path, ROOT)}")


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


def load_parts(board, comps, nets, skip=()):
    """Every net, and every part on the sheets as its footprint, pads on their nets -
    not yet placed. `skip`: references the board does not carry (layout.yaml
    not_on_board:, each with its reason)."""
    netinfo = {}
    for nname, _ in nets:
        ni = pcbnew.NETINFO_ITEM(board, nname)
        board.Add(ni)
        netinfo[nname] = ni
    padnet = {(r, p): n for n, nodes in nets for r, p in nodes}

    fps = {}
    for ref, c in sorted(comps.items()):
        if ref.startswith("#") or ref in skip:
            continue
        if not c["footprint"]:
            sys.exit(f"pcb: {ref} has no footprint on its sheet - set its Footprint field")
        fp = load_fp(c["footprint"])
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH(c["path"]))
        # the symbol's "Exclude from BOM", both ways: a library footprint may carry its own
        # (KiCad's net ties do), and schematic parity compares the two
        fp.SetExcludedFromBOM(c["exclude_from_bom"])
        if c["dnp"]:
            fp.SetDNP(True)
            fp.SetExcludedFromPosFiles(True)
        # The reference's own field goes on the fabrication layer; the silkscreen
        # labels are placed by add_silk, which keeps each off every part body.
        fp.Reference().SetLayer(pcbnew.F_Fab)
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.5), MM(0.5)))
        fp.Reference().SetTextThickness(MM(0.08))
        for pad in fp.Pads():
            n = padnet.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(netinfo[n])
        fps[ref] = fp
    return netinfo, fps


def build(bdir):
    name = os.path.basename(bdir)
    lay = yaml.safe_load(open(os.path.join(bdir, "layout.yaml")))
    if lay.get("kind") in ("main", "module"):
        import pcb_main
        import pcb_module
        board, fps, netinfo, lay, comps, _ = (pcb_main if lay["kind"] == "main" else pcb_module).build(bdir, lay)
        if lay.get("fab"):
            fit_footprint_silk(board, lay["fab"])
        if not lay.get("route"):
            add_silk_generic(board, lay, comps)       # else after routing (post_route), clear of the vias
        return board, fps, netinfo, lay
    cluster, suffix = lay["cluster"], lay["suffix"]
    geo = cad_geometry(cluster)
    comps, nets = sheet_netlist(os.path.join(bdir, name + ".kicad_sch"))
    board = new_board(bdir, lay, geo)
    add_outline(board, dxf_segments(os.path.join(ROOT, "mechanical", "export", f"key-board-{suffix.lower()}.dxf")))
    netinfo, fps = load_parts(board, comps, nets)

    # The switch's 3D model has its origin at the plate seat (docs/reference/ks33-geometry.md);
    # the PCB top sits switch.pcb_below_seat below it (config/body.yaml), so lift the model by that.
    body = yaml.safe_load(open(os.path.join(ROOT, "config", "body.yaml")))
    below_seat = float(body["switch"]["pcb_below_seat"]["value"])
    for ref, fp in fps.items():
        if comps[ref]["row"] == "SW1-n":
            models = fp.Models()
            for i in range(len(models)):      # by index: SWIG's iterator hands out copies
                models[i].m_Offset.z = below_seat

    placed = set()
    # switches: top side, exactly where the body CAD puts them
    for key, (x, y, r) in geo["switches"].items():
        ref = ref_of(comps, "SW1-n", key)
        px, py = to_pcb(x, y)
        place(board, fps[ref], px, py, r + lay.get("switch_rot", 0), False)
        placed.add(ref)
    # the chain header: bottom side, where the body CAD stacks it over the
    # main board's, its mouth facing along the body toward the ribbon's fold
    jref = ref_of(comps, "J-CHAIN")
    place_chain(board, fps[jref], geo)
    placed.add(jref)
    # the corner mounts' holes (ADR 0020): board-only footprints, no symbol - the
    # stud, spacer and nut are mechanical, in hardware/unplaced.csv. On the
    # BOTTOM, so their courtyard keeps the underside parts off the nuts.
    bond = lay.get("bond_mount") or {}
    for i, (x, y, hole, head, od) in enumerate(geo["standoffs"], 1):
        bonded = bond.get("index") == i
        h = load_fp(bond["footprint"] if bonded else lay["standoff_footprint"])
        h.SetReference(f"H{i}")
        h.SetValue("mount")
        h.SetBoardOnly(True)
        h.SetExcludedFromBOM(True)
        h.SetExcludedFromPosFiles(True)
        h.Reference().SetLayer(pcbnew.F_Fab)
        px, py = to_pcb(x, y)
        place(board, h, px, py, 0, True)
        if bonded:
            # THE ONE MOUNT THAT GROUNDS THE PLATE (layout.yaml bond_mount): plated,
            # its pads on the board's ground, the spacer and nut bearing on them.
            # No keep-out here: the ground pour is meant to meet it.
            net = board.FindNet(bond["net"])
            for pad in h.Pads():
                pad.SetNet(net)
            continue
        # The mount's spacer presses on the top copper and its nut on the
        # bottom, and both are on the stud that the plate grounds through its own bond:
        # no copper under either, or the board gets a second ground bond and
        # every net routed there a short. A rule area on both layers, which the
        # router also treats as an obstacle.
        keepout(board, px, py, max(head, od) / 2 + lay["rules"]["clearance"])
    # everything else: layout.yaml, in body coordinates, bottom side
    for ref, (x, y, r) in {**network_parts(lay, geo, comps), **lay["parts"]}.items():
        px, py = to_pcb(x, y)
        place(board, fps[ref], px, py, r, True)
        placed.add(ref)
    # every key's T must have its node's three pads nearest the junction, or the
    # pattern turned a part the wrong way round (R6-3)
    for key in (lay.get("networks") or {}).get("pattern") and geo["switches"] or []:
        refs = [ref_of(comps, row, key) for row in ("R-KEY-SER", "R-KEY-PU", "C-KEY")]
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
    add_silk(board, lay, comps)
    add_top_silk(board, lay, comps)
    return board, fps, netinfo, lay


def save(board, path):
    board.BuildConnectivity()
    pcbnew.SaveBoard(path, board)


MASK_T = 0.01      # solder mask thickness in the stackup: KiCad's own default; it only splits the board's thickness


def set_stackup(path, fab, thickness, stackup=None):
    """KiCad's Python API does not reach the stackup, which the Gerber job file
    reports to the board house - finish, mask colour, copper weight: write it
    into the saved file, after the last save (the zone fill re-saves the board).
    Two layers: the core is what is left of the board's thickness. More: layout.yaml
    stackup: gives the board house's named stack (copper, prepreg, core), and the
    mask takes what is left of the thickness."""
    L = lambda name, typ, extra="": f'\t\t\t(layer "{name}"\n\t\t\t\t(type "{typ}"){extra}\n\t\t\t)\n'
    diel = lambda n, typ, d: L(f"dielectric {n}", typ, f'\n\t\t\t\t(thickness {d["thickness"]})\n\t\t\t\t(material "{d["material"]}")'
                                                         f'\n\t\t\t\t(epsilon_r {d["epsilon_r"]})\n\t\t\t\t(loss_tangent 0.02)')
    if stackup:
        cu, icu = stackup["outer_cu"], stackup["inner_cu"]
        pp, core = stackup["prepreg"], stackup["core"]
        mask_t = round((thickness - 2 * cu - 2 * icu - 2 * pp["thickness"] - core["thickness"]) / 2, 4)
        if mask_t < 0:
            sys.exit(f"pcb: layout.yaml stackup: is thicker than the board ({thickness:g} mm)")
        copper = (L("F.Cu", "copper", f"\n\t\t\t\t(thickness {cu})") + diel(1, "prepreg", pp)
                  + L("In1.Cu", "copper", f"\n\t\t\t\t(thickness {icu})") + diel(2, "core", core)
                  + L("In2.Cu", "copper", f"\n\t\t\t\t(thickness {icu})") + diel(3, "prepreg", pp)
                  + L("B.Cu", "copper", f"\n\t\t\t\t(thickness {cu})"))
    else:
        cu = fab["copper_oz"] * 0.035
        mask_t = MASK_T
        core = thickness - 2 * cu - 2 * MASK_T
        copper = (L("F.Cu", "copper", f"\n\t\t\t\t(thickness {cu:.3f})")
                  + L("dielectric 1", "core", f'\n\t\t\t\t(thickness {core:.3f})\n\t\t\t\t(material "FR4")\n\t\t\t\t(epsilon_r 4.5)\n\t\t\t\t(loss_tangent 0.02)')
                  + L("B.Cu", "copper", f"\n\t\t\t\t(thickness {cu:.3f})"))
    mask = f'\n\t\t\t\t(color "{fab["mask"]}")\n\t\t\t\t(thickness {mask_t})'
    silk = f'\n\t\t\t\t(color "{fab["silk"]}")'
    block = ("\t\t(stackup\n" + L("F.SilkS", "Top Silk Screen", silk) + L("F.Paste", "Top Solder Paste")
             + L("F.Mask", "Top Solder Mask", mask) + copper + L("B.Mask", "Bottom Solder Mask", mask)
             + L("B.Paste", "Bottom Solder Paste") + L("B.SilkS", "Bottom Silk Screen", silk)
             + f'\t\t\t(copper_finish "{fab["finish"]}")\n\t\t\t(dielectric_constraints no)\n\t\t)\n')
    t = open(path).read()
    t2, n = re.subn(r"\t\t\(stackup\n.*?\n\t\t\)\n", lambda m: block, t, count=1, flags=re.S)
    if not n:
        t2 = t.replace("\t(setup\n", "\t(setup\n" + block, 1)
        if t2 == t:
            sys.exit("pcb: could not write the stackup - no (setup) section found")
    open(path, "w").write(t2)


def set_net_classes(j, lay):
    """layout.yaml net_classes: into the project (a .kicad_pro's JSON), each a class with
    its track width - clearance and vias the Default's - and one exact-name pattern per net."""
    ns = j.setdefault("net_settings", {})
    default = next(c for c in ns["classes"] if c["name"] == "Default")
    ns["classes"] = [default] + [{**default, "name": name, "track_width": spec["track"], "priority": i}
                                 for i, (name, spec) in enumerate(lay["net_classes"].items())]
    ns["netclass_patterns"] = [{"netclass": name, "pattern": net}
                               for name, spec in lay["net_classes"].items() for net in spec["nets"]]


def cmd_layout(bdir, force=False, route=True):
    name = os.path.basename(bdir)
    out = os.path.join(bdir, name + ".kicad_pcb")
    if os.path.exists(out) and not force:
        sys.exit(f"pcb: {os.path.relpath(out, ROOT)} exists and is the source now; --force overwrites it")
    layout_yaml(bdir)      # a clear message, not build()'s traceback, when there is none
    board, fps, netinfo, lay = build(bdir)
    route = route and lay.get("route", True)
    if route is True:
        import pcb_route
        failed = pcb_route.route(board, lay)
        if failed:
            # the existing board, if any, is the source: a half-routed one does not replace it
            print(f"pcb: could not route {', '.join(failed)} - move parts in layout.yaml and re-run; "
                  f"{os.path.relpath(out, ROOT)} {'left as it was' if os.path.exists(out) else 'not written'}")
            return 1
    elif route in ("freerouting", "astar"):
        # what is not left to the autorouter: each plane net's pad to its plane (fanout),
        # and the breath pair side by side (route_pair) - both then fixed for it
        import pcb_route
        pcb_route.prepare(board, lay)
    unrouted = []
    # Written in a scratch directory beside the board and moved in only when complete.
    # SaveBoard writes <name>.kicad_pro beside the .kicad_pcb, from the board (the design
    # rules are in it), so the scratch copy keeps the board's own name and both move.
    import shutil
    import json
    t = tempfile.mkdtemp(prefix=".layout-", dir=bdir)
    try:
        tmp = os.path.join(t, name + ".kicad_pcb")
        save(board, tmp)
        pro = os.path.join(t, name + ".kicad_pro")
        j = json.load(open(pro))
        if lay.get("net_classes"):
            set_net_classes(j, lay)
            json.dump(j, open(pro, "w"), indent=2)
        here = os.path.dirname(os.path.abspath(__file__))
        if route == "freerouting":
            # in a fresh process, which loads the board with the net classes just written
            r = subprocess.run([sys.executable, "-c", f"import sys, json; sys.path.insert(0, {here!r}); "
                                f"import pcb_freeroute; print('UNROUTED=' + json.dumps(pcb_freeroute.route({tmp!r}, {float(lay['rules']['edge_clearance'])!r}, {lay.get('directions')!r})))"],
                               capture_output=True, text=True)
            print(r.stdout.rstrip())
            if r.returncode or "UNROUTED=" not in r.stdout:
                sys.exit(f"pcb: the Freerouting round trip failed:\n{r.stderr[-3000:]}")
        if route in ("freerouting", "astar"):
            # the planes filled, so KiCad's count of what is missing is right; then what
            # the autorouter left (`astar`: every signal connection), routed by
            # pcb_route.complete, tidied and tried again, and the silkscreen (post_route)
            for step in (f"import pcb_route; pcb_route.fill_zones({tmp!r})", f"import pcb; pcb.post_route({tmp!r}, {bdir!r})"):
                r = subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {here!r}); " + step],
                                   capture_output=True, text=True)
                print("\n".join(l for l in r.stdout.splitlines() if not l.startswith("route: WARNING")))
                if r.returncode:
                    sys.exit(f"pcb: {step.split(';')[1].strip()} failed:\n{r.stderr[-3000:]}")
        if route:
            # zones are filled in a fresh process: an in-process fill of a just-built board crashes
            subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {here!r}); "
                            f"import pcb_route; pcb_route.fill_zones({tmp!r})"], check=True)
        if route in ("freerouting", "astar"):
            # what is still unconnected once the planes are filled: KiCad's own count
            unrouted = sorted({"; ".join(i["description"] for i in v.get("items", []))
                               for v in drc(tmp).get("unconnected_items", [])})
        if lay.get("fab"):
            set_stackup(tmp, lay["fab"], board.GetDesignSettings().GetBoardThickness() / 1e6, lay.get("stackup"))
            # fit_footprint_silk adapts the library footprints' silkscreen to the board
            # house on purpose, so "does not match the library copy" is expected, not a finding
            j = json.load(open(pro))
            j["board"]["design_settings"]["rule_severities"]["lib_footprint_mismatch"] = "ignore"
            json.dump(j, open(pro, "w"), indent=2)
        os.replace(pro, os.path.join(bdir, name + ".kicad_pro"))
        os.replace(tmp, out)
    finally:
        shutil.rmtree(t, ignore_errors=True)
    if unrouted:
        print(f"pcb: {len(unrouted)} connection(s) left for hand routing (check fails on each until routed):")
        for u in unrouted:
            print("  " + u)
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
    bad += check_stackup(os.path.join(bdir, name + ".kicad_pcb"), lay.get("fab") or {})
    pro = os.path.join(bdir, name + ".kicad_pro")
    sev = json.load(open(pro))["board"]["design_settings"].get("rule_severities", {}) if os.path.exists(pro) else {}
    for test, level in sorted(sev.items()):
        if level == "ignore" and test not in IGNORE_OK:
            why = "it enforces a board-house limit" if test in FAB_TESTS else "an ignored test drops out of the report, and a check with nothing to say reads as a pass"
            bad.append(f"error: [rules] DRC test {test} is set to ignore in {name}.kicad_pro - {why}; "
                       f"set it back, or add it to tools/pcb.py IGNORE_OK with the reason")
    return bad


def check_stackup(path, fab):
    """The stackup's mask and silk colours and finish - what the Gerber job file tells
    the board house - still those of layout.yaml fab:. set_stackup writes them only at
    `layout`, so a fab: change made after that reached the order only by hand (the key
    boards' 2026-10-02 move to white mask): `pcb.py stackup <board>` rewrites them."""
    if not fab:
        return []
    m = re.search(r"\t\t\(stackup\n(.*?)\n\t\t\)\n", open(path).read(), re.S)
    fix = "run: python3 tools/pcb.py stackup <board>"
    if not m:
        return [f"error: [stackup] the board has no stackup - {fix}"]
    s, bad = m.group(1), []
    for layer, want in (("F.Mask", fab["mask"]), ("B.Mask", fab["mask"]), ("F.SilkS", fab["silk"]), ("B.SilkS", fab["silk"])):
        blk = re.search(rf'\(layer "{re.escape(layer)}"\n(.*?)\n\t\t\t\)', s, re.S)
        c = re.search(r'\(color "([^"]*)"\)', blk.group(1)) if blk else None
        have = c.group(1) if c else None
        if have != want:
            bad.append(f"error: [stackup] {layer} colour is {have!r}, layout.yaml fab: says {want!r} - {fix}")
    fin = re.search(r'\(copper_finish "([^"]*)"\)', s)
    if (fin.group(1) if fin else None) != fab["finish"]:
        bad.append(f"error: [stackup] copper finish is {fin.group(1) if fin else None!r}, layout.yaml fab.finish says {fab['finish']!r} - {fix}")
    return bad


def cmd_stackup(bdir):
    """Rewrite the stackup (mask and silk colours, finish, copper) from layout.yaml fab:
    and stackup:, at the board's own thickness. Nothing else in the board is touched."""
    name = os.path.basename(bdir)
    pcb = os.path.join(bdir, name + ".kicad_pcb")
    lay = layout_yaml(bdir)
    t = pcbnew.ToMM(pcbnew.LoadBoard(pcb).GetDesignSettings().GetBoardThickness())
    set_stackup(pcb, lay["fab"], t, lay.get("stackup"))
    print(f"pcb: stackup of {os.path.relpath(pcb, ROOT)} written from layout.yaml fab: (mask {lay['fab']['mask']}, silk {lay['fab']['silk']})")


def check_courtyards(board, lay):
    """EVERY FOOTPRINT'S COURTYARD INSIDE THE BOARD (owner, 2026-10-02: "everything needs
    to fit within the footprint of the boards"): each part's courtyard, on whichever face,
    within the Edge.Cuts outline, its cut-outs and holes counted as outside. KiCad's DRC
    does not test this - its courtyard tests are part against part, and its edge test is
    copper only - so a part could hang off the side of a board and pass. A part that is
    MEANT to overhang (a connector whose body reaches through a panel) is named in
    layout.yaml `courtyard_overhang:` with the reason and the source that says so; an
    entry naming a part that does not overhang is an error too, so the list cannot go
    stale. A footprint with no courtyard (a net tie, a board-only mount) is not tested."""
    bad = []
    allow = lay.get("courtyard_overhang") or {}
    for ref, why in allow.items():
        if not isinstance(why, dict) or not why.get("reason") or not why.get("source"):
            bad.append(f"error: [courtyard] layout.yaml courtyard_overhang: {ref} needs a reason: and a source:")
    ol = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(ol):
        return bad + ["error: [courtyard] the Edge.Cuts outline is not one closed shape, so courtyards cannot be checked against it"]
    outline = shapely_of(ol).buffer(1e-3)
    over = set()
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        for cl in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            cy = fp.GetCourtyard(cl)
            if not cy.OutlineCount():
                continue
            out = shapely_of(cy).difference(outline)
            if out.is_empty or out.area < 1e-4:
                continue
            over.add(ref)
            if ref in allow:
                continue
            x0, y0, x1, y1 = out.bounds
            bad.append(f"error: [courtyard] {ref} ({fp.GetFPID().GetLibItemName().wx_str()}): {out.area:.2f} mm2 of its "
                       f"{'front' if cl == pcbnew.F_CrtYd else 'rear'} courtyard lies outside the board outline, over "
                       f"({x0:.2f}, {y0:.2f})-({x1:.2f}, {y1:.2f}) - move it inside, or name it in layout.yaml "
                       f"courtyard_overhang: with the reason it is meant to overhang and the source")
    for ref in sorted(set(allow) - over):
        bad.append(f"error: [courtyard] layout.yaml courtyard_overhang: {ref} lies wholly inside the board - take it off the list")
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
    # every part body on each side: a label under one cannot be read once the part
    # is fitted, and nothing else checks it (owner, 2026-09-27)
    crt_layer = {pcbnew.F_SilkS: pcbnew.F_CrtYd, pcbnew.B_SilkS: pcbnew.B_CrtYd}
    bodies = {s: [] for s in silk}
    for fp in board.GetFootprints():
        for s_, cl in crt_layer.items():
            cy = fp.GetCourtyard(cl)
            if cy.OutlineCount():
                bodies[s_].append((fp.GetReference(), shapely_of(cy)))
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
        if who == "board":
            # the placed labels, dots and arrows (a footprint's own outline is drawn round its body)
            for bref, body in bodies[layer]:
                if shape.intersects(body) and shape.intersection(body).area > 1e-4:
                    bad.append(f"error: [silk] {what} at {where} lies under {bref}'s body (its courtyard) - "
                               "it cannot be read with the part fitted")
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


def check_cad(board, lay, geo, comps):
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
        sw = [ref for ref, c in comps.items() if c["row"] == "SW1-n" and c["sheet"] == key]
        fp = board.FindFootprintByReference(sw[0]) if len(sw) == 1 else None
        if fp is None:
            bad.append(f"error: [cad] {key}'s switch is not on the board (its sheet has {sw or 'none'}); the body CAD has a switch there")
            continue
        px, py = to_pcb(x, y)
        got = (pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y))
        if math.hypot(got[0] - px, got[1] - py) > 0.05:
            bad.append(f"error: [cad] {sw[0]} ({key}) is at {got}, the body CAD puts it at ({px:.2f}, {py:.2f})")
        # the KS-33's pins are asymmetric: a turned switch no longer fits its plate cutout
        want = (r + lay.get("switch_rot", 0)) % 360
        rot = fp.GetOrientationDegrees() % 360
        if min(abs(rot - want), 360 - abs(rot - want)) > 0.01 or fp.IsFlipped():
            bad.append(f"error: [cad] {sw[0]} ({key}) is turned {rot:g} deg{' on the bottom' if fp.IsFlipped() else ''}; "
                       f"the body CAD turns it {want:g} deg, on the top")
        models = fp.Models()
        for i in range(len(models)):      # by index: SWIG's iterator hands out copies
            if abs(models[i].m_Offset.z - below_seat) > 1e-6:
                bad.append(f"error: [cad] {sw[0]} ({key})'s 3D model sits {models[i].m_Offset.z:g} mm up; "
                           f"config/body.yaml switch.pcb_below_seat is {below_seat:g}")
    for i, (x, y, *_) in enumerate(geo["standoffs"], 1):
        fp = board.FindFootprintByReference(f"H{i}")
        px, py = to_pcb(x, y)
        got = None if fp is None else (pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y))
        if got is None or math.hypot(got[0] - px, got[1] - py) > 0.05:
            bad.append(f"error: [cad] standoff hole H{i} is at {got}, the body CAD puts it at ({px:.2f}, {py:.2f})")
            continue
        hole_d, head, od = geo["standoffs"][i - 1][2:5]
        bond = lay.get("bond_mount") or {}
        if bond.get("index") == i:
            # the plate's one ground bond: plated, every pad on the ground net, and
            # nothing but that net where the spacer and nut bear
            drilled = [p for p in fp.Pads() if p.GetDrillSize().x > 0 and abs(pcbnew.ToMM(p.GetDrillSize().x) - hole_d) <= 0.01]
            if not drilled or any(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH for p in drilled):
                bad.append(f"error: [cad] H{i} is the plate's ground bond (layout.yaml bond_mount): it must be a plated {hole_d:g} mm hole")
            for pad in fp.Pads():
                if pad.GetNetname() != bond["net"]:
                    bad.append(f"error: [cad] H{i} pad on '{pad.GetNetname()}', not {bond['net']} - the bond is to ground")
            from shapely.geometry import Point as _P
            disc = _P(*got).buffer(max(head, od) / 2 + float(lay["rules"]["clearance"]) - 0.02)
            for L in (pcbnew.F_Cu, pcbnew.B_Cu):
                hits = {t.GetNetname() for t in board.GetTracks() if t.IsOnLayer(L) and item_shape(t, L).intersects(disc)}
                hits |= {pad.GetNetname() for f2 in board.GetFootprints() for pad in f2.Pads()
                         if f2.GetReference() != fp.GetReference() and pad.IsOnLayer(L) and item_shape(pad, L).intersects(disc)}
                hits -= {bond["net"]}
                if hits:
                    bad.append(f"error: [cad] {', '.join(sorted(hits))} under the grounded mount H{i} on {board.GetLayerName(L)} - its spacer and nut would short them to the plate")
            continue
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
                           f"({', '.join(sorted(set(hits)))}) - the spacer and nut bear there (ADR 0020)")
    if geo["chain"]:
        js = [ref for ref, c in comps.items() if c["row"] == "J-CHAIN"]
        fp = board.FindFootprintByReference(js[0]) if len(js) == 1 else None
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
    bad += check_key_faces(board, lay, geo, comps)
    return bad


def check_key_faces(board, lay, geo, comps):
    """A key board's two faces against the body CAD (issue #19 F2): its top is pressed
    against the switches under the plate, with only the housings' height between them
    (drc.echo "key-board mount gap"), so it carries nothing but the switches; each part
    underneath stands no taller than the echo's smt_height_max, J-CHAIN excepted (its own
    ribbon keep-out). Heights from layout.yaml heights:, by footprint name, the first key
    a name contains (as the main board's, pcb_main.check_heights). A board whose
    layout.yaml has no heights: gets a note that its underside was not checked, never
    silence."""
    bad = []
    heights = lay.get("heights")
    smax = geo.get("smt_height_max")
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        row = comps.get(ref, {}).get("row")
        if ref.startswith("H") or row in ("SW1-n", "J-CHAIN"):
            continue
        name = fp.GetFPID().GetLibItemName().wx_str()
        if not fp.IsFlipped():
            bad.append(f"error: [height] {ref} ({name}) is on the switch side, pressed against the switch housings - "
                       f"only the switches go there (drc.echo 'key-board mount gap')")
            continue
        if heights is None or smax is None:
            continue
        h = next((v for k, v in heights.items() if k in name), None)
        if h is None:
            bad.append(f"error: [height] {ref} ({name}) has no height in layout.yaml heights:")
        elif h > smax + 1e-6:
            bad.append(f"error: [height] {ref} ({name}) stands {h:g} mm under the board; the body CAD's room is {smax:g} "
                       f"(pcb-geometry.echo smt_height_max)")
    if heights is None:
        bad.append("note: [height] layout.yaml has no heights:, so the underside parts' heights were not checked")
    return bad


def cad_export_problems(lay):
    """The body CAD's exports this board is checked against must be current (issue #9, G8).
    check_cad and pcb_main.check_cad read the outline DXF and pcb-geometry.echo as
    committed; at a STALE export they compare the board with a body that may no longer
    exist, and pass. Asks tools/cad.py's own ledger test, for those files only."""
    import cad
    if lay.get("kind") == "module":     # the module's own CAD and its exports
        want = {"mechanical/module/export/pcb-geometry.echo", "mechanical/module/export/" + lay["outline"]}
    else:
        want = {"mechanical/export/pcb-geometry.echo",
                "mechanical/export/" + (lay["outline"] if lay.get("kind") == "main"
                                        else f"key-board-{lay['suffix'].lower()}.dxf")}
    outs = {o["out"]: o for o in cad.load_spec() if o["out"] in want}
    ledger = cad.load_ledger()
    behind = [p for p, _ in cad.params_problems()]
    bad = [f"error: [cad-export] {p}: no tools/cad.py spec builds it, so its currency cannot be checked"
           for p in sorted(want - set(outs))]
    for p, o in sorted(outs.items()):
        msgs = cad.problems_for(o, ledger.get(o["name"]))
        if not msgs and any(b in cad.output_inputs(o) for b in behind):
            msgs = [f"{o['name']}: built from generated params that are behind config/"]
        bad += [f"error: [cad-export] {m} - this board is checked against {p}; run: "
                f"python3 tools/cad.py build {o['name']}" for m in msgs]
    return bad


def jlc_rotation_problems(bdir, name, board=None):
    """A machine-placed part whose LCSC number has no row in hardware/lib/jlc-rotation.csv
    is placed at offset 0 - right for a 2-pad passive, wrong for a part whose package JLC
    draws turned (SOIC -90, SOT-23 180 against KiCad's). That was a printed warning,
    with 7 main-board parts placed rotated (issue #9, G4). Now it is an error for a part
    with polarity (D, Q, U, LED references; an electrolytic) or with more than two pads
    (counted on `board`, when given); a 2-pad non-polar part still only warns, at render."""
    import csv
    import kicad
    comps, _ = kicad.kicad_netlist(os.path.join(bdir, name + ".kicad_sch"))
    elsewhere = yaml.safe_load(open(os.path.join(bdir, "layout.yaml"))).get("not_on_board") or {}
    have = {r["lcsc"] for r in csv.DictReader(open(JLC_ROTATION))}
    pads = {fp.GetReference(): fp.GetPadCount() for fp in board.GetFootprints()} if board else {}
    bad = []
    for ref in sorted(comps):
        f = comps[ref]["fields"]
        if ref in elsewhere or f.get("Assembly") != "machine" or not f.get("LCSC") or f["LCSC"] in have:
            continue
        fp = comps[ref]["footprint"]
        polar = re.match(r"(D|Q|U|LED)\d", ref) or ":CP_" in fp
        if polar or pads.get(ref, 0) > 2:
            bad.append(f"error: [jlc-rotation] {ref} ({f['LCSC']}, {fp.split(':')[-1]}) has no row in "
                       f"{os.path.relpath(JLC_ROTATION, ROOT)} - a {'polarised' if polar else 'multi-pin'} part "
                       f"at offset 0 may be fitted turned; add its offset with the evidence (JLC's EasyEDA "
                       f"footprint, banked)")
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
    # a part layout.yaml not_on_board: names (with its reason) is a note, not a failure;
    # a missing footprint it does not name is still an error
    skip = lay.get("not_on_board") or {}
    notes = []
    for v in d.get("schematic_parity", []):
        m = re.match(r"Missing footprint (\S+)", v["description"])
        if m and m.group(1) in skip:
            notes.append(f"note: {m.group(1)} is on the sheets, not on this board - {skip[m.group(1)]}")
            continue
        bad.append(f"error: [parity] {v['description']} - " + "; ".join(i["description"] for i in v.get("items", [])))
    board = pcbnew.LoadBoard(pcb)
    for fp in board.GetFootprints():
        fp.BuildCourtyardCaches()   # LoadBoard leaves them empty on some 9.0.x (issue #9, G2)
    bad += cad_export_problems(lay)
    bad += jlc_rotation_problems(bdir, name, board)
    bad += check_rules(board, bdir, name, lay)
    bad += check_courtyards(board, lay)
    if lay.get("fab"):
        bad += check_silk(board, lay["fab"])
    bad += check_tracks(board)
    bad += check_holes(board, lay)
    bad += check_connect_first(board, lay)
    comps, _ = sheet_netlist(os.path.join(bdir, name + ".kicad_sch"))
    if lay.get("kind") == "main":
        import pcb_main
        bad += pcb_main.check_cad(board, lay, comps)
    elif lay.get("kind") == "module":
        import pcb_module
        bad += pcb_module.check_cad(board, lay, comps)
        for b in pcb_module.check_b2b(board, bdir, lay):
            (notes if b.startswith("note:") else bad).append(b)
    else:
        bad += check_cad(board, lay, cad_geometry(lay["cluster"]), comps)
    if lay.get("planes") or lay.get("islands"):
        import pcb_main
        bad += pcb_main.check_planes(board, lay)
    notes += [b for b in bad if b.startswith("note:")]        # a check's note is not a failure
    bad = [b for b in bad if not b.startswith("note:")]
    print(f"pcb: {os.path.relpath(pcb, ROOT)}: {len(bad)} error(s)")
    for b in notes + bad:
        print("  " + b)
    return 1 if bad else 0


def check_holes(board, lay):
    """No copper within the hole clearance of an unplated hole (a switch's centre hole, a
    mount's clearance hole) or of an Edge.Cuts cut-out, on ANY copper layer - tracks,
    arcs, vias, other parts' pads and filled zones alike. KiCad's DRC sees most of this as
    hole_clearance, but a drawn path laid through KS-33's centre hole went unchecked
    (2026-10-04), and this does not depend on which DRC tests a board leaves on."""
    import pcb_route
    from shapely.geometry import Point, Polygon
    hc = float((lay.get("fab") or {}).get("hole_clearance", (lay.get("rules") or {}).get("clearance", 0.2)))
    holes = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and p.GetDrillSize().x > 0:
                c = p.GetPosition()
                holes.append((f"{f.GetReference()}'s unplated hole",
                              Point(pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)).buffer(pcbnew.ToMM(p.GetDrillSize().x) / 2, 32), f))
    outline = pcb_route.board_outline_with_holes(board)
    for g in getattr(outline, "geoms", [outline]):
        for ring in g.interiors:
            holes.append(("an Edge.Cuts cut-out", Polygon(ring), None))
    if not holes:
        return []
    cu = [L for L in board.GetEnabledLayers().CuStack()]
    bad = []
    for name, h, owner in holes:
        zone = h.buffer(hc - 1e-3)
        hits = set()
        for t in board.GetTracks():
            for L in cu:
                if t.IsOnLayer(L) and item_shape(t, L).intersects(zone):
                    hits.add(f"{t.GetNetname()} {'via' if isinstance(t, pcbnew.PCB_VIA) else 'track'} on {board.GetLayerName(L)}")
        for f in board.GetFootprints():
            for p in f.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or (owner is not None and f is owner):
                    continue
                for L in cu:
                    if p.IsOnLayer(L) and item_shape(p, L).intersects(zone):
                        hits.add(f"{f.GetReference()} pad {p.GetNumber()} on {board.GetLayerName(L)}")
        for z in board.Zones():
            if z.GetIsRuleArea():
                continue
            for L in cu:
                if z.IsOnLayer(L) and z.GetFilledPolysList(L).OutlineCount() and shapely_of(z.GetFilledPolysList(L)).intersects(zone):
                    hits.add(f"{z.GetNetname()} zone on {board.GetLayerName(L)}")
        c = h.centroid
        for w in sorted(hits):
            bad.append(f"error: [hole] {w} within {hc} mm of {name} at ({c.x:.2f}, {c.y:.2f})")
    return bad


def assembly_files(bdir, name, fab):
    """The assembly order, for JLCPCB (the owner's board house - docs: the board's
    README): a BOM of the machine-placed parts with their LCSC numbers, a
    placement (CPL) file of the same parts, and the list of parts fitted by hand.
    Part identity comes from the sheets' fields (Manufacturer, MPN, LCSC,
    Assembly = machine / hand / none); positions from KiCad's own placement
    export. Rotation is translated to JLC's convention: a bottom part's angle is
    mirrored, 180 - KiCad's (JLC reads it looking at the bottom; KiBot's
    rot_footprint `mirror_bottom`, and kicad-jlcpcb-tools' fix_rotation), and
    each LCSC part's offset between KiCad's footprint and JLC's own (its
    EasyEDA footprint) is added from hardware/lib/jlc-rotation.csv. A machine
    part with no row there is placed uncorrected and named on stdout, and JLC's
    placement preview stays the final check either way. Returns the sheets
    read (and the offset table), so the ledger ties these files to them as
    well as to the board."""
    import csv
    import kicad
    root = os.path.join(bdir, name + ".kicad_sch")
    comps, _ = kicad.kicad_netlist(root)
    pos = {r["Ref"]: r for r in csv.DictReader(open(os.path.join(fab, name + "-pos.csv")))}
    machine, hand, none = {}, [], []
    # a part the sheets carry and this board does not (layout.yaml not_on_board:, with
    # its reason) is neither ordered nor fitted here
    elsewhere = yaml.safe_load(open(os.path.join(bdir, "layout.yaml"))).get("not_on_board") or {}
    for ref in sorted(comps):
        if ref in elsewhere:
            continue
        f = comps[ref]["fields"]
        how = f.get("Assembly", "")
        if how == "none":
            # nothing is bought for it - so it must be a part nothing is bought for: a test
            # pad, a fiducial, "Exclude from BOM" ticked. Otherwise `none` drops a real part
            # from the order and the hand list both, and every check passes (K7-3).
            # a net tie is copper drawn in the board: its BOM row records the tie, nothing is bought
            if comps[ref]["in_bom"] and not comps[ref]["footprint"].startswith("NetTie:"):
                sys.exit(f"pcb: {ref} is Assembly = none but in the BOM - machine or hand, or tick "
                         f"'Exclude from BOM' on its symbol if nothing is bought for it")
            none.append(ref)
        if how == "machine":
            if ref not in pos:
                sys.exit(f"pcb: {ref} is machine-assembled but not in the placement export")
            if not f.get("LCSC"):
                sys.exit(f"pcb: {ref} is machine-assembled but has no LCSC field on its sheet")
            # one row per bought part - its LCSC number on its footprint - however the sheets'
            # Value strings differ ("10k" and "10k 1%" were two rows for C17414: issue #17 D5);
            # its Comment is the bought part's MPN, which every row of it shares (#8-12: the
            # values' "or equivalent" read oddly on the order)
            m = machine.setdefault((comps[ref]["footprint"], f["LCSC"]), {"refs": [], "comment": set()})
            m["refs"].append(ref)
            m["comment"].add(f.get("MPN") or comps[ref]["value"])
        elif how == "hand":
            hand.append((ref, comps[ref]["value"], f.get("Manufacturer", ""), f.get("MPN", "")))
        elif how != "none" and not ref.startswith("#"):
            sys.exit(f"pcb: {ref} has no Assembly field (machine, hand or none) on its sheet")
    with open(os.path.join(fab, name + "-bom-jlc.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint", "JLCPCB Part #"])
        for (fp, lcsc), m in sorted(machine.items(), key=lambda kv: (min(kv[1]["comment"]), kv[0])):
            if len(m["comment"]) > 1:
                sys.exit(f"pcb: {lcsc} is bought for {','.join(sorted(m['refs']))} under {len(m['comment'])} MPNs "
                         f"({', '.join(sorted(m['comment']))}) - one LCSC number is one part")
            w.writerow([min(m["comment"]), ",".join(sorted(m["refs"], key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0)))), fp.split(":")[-1], lcsc])
    offsets = {r["lcsc"]: r for r in csv.DictReader(open(JLC_ROTATION))}
    unchecked = []
    with open(os.path.join(fab, name + "-cpl-jlc.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for (fp, lcsc), m in machine.items():
            refs = m["refs"]
            o = offsets.get(lcsc)
            if o and o["footprint"] != fp.split(":")[-1]:
                sys.exit(f"pcb: {lcsc}'s rotation offset in {os.path.relpath(JLC_ROTATION, ROOT)} is for "
                         f"{o['footprint']}, but {','.join(refs)} use {fp.split(':')[-1]}")
            if not o:
                unchecked += refs
            for ref in sorted(refs):
                r = pos[ref]
                rot = float(r["Rot"])
                if r["Side"] == "bottom":
                    rot = 180.0 - rot
                rot = (rot + (float(o["rotation"]) if o else 0.0)) % 360.0
                w.writerow([ref, r["PosX"], r["PosY"], "Bottom" if r["Side"] == "bottom" else "Top", f"{rot:.6f}"])
    if unchecked:
        print(f"pcb: no JLC rotation offset for {', '.join(sorted(unchecked))} - confirm them in JLC's preview")
    # layout.yaml hand_trim: a hand part's tails, cut after soldering to at most a length
    # below the board's bottom face, computed from the config/body.yaml figures the layout
    # names (issue #8-11). Only a board that has one gets the Fit column, and then the
    # layout and body.yaml are inputs of these files, so the length follows its figures.
    trims = yaml.safe_load(open(os.path.join(bdir, "layout.yaml"))).get("hand_trim") or {}
    fit = {}
    if trims:
        body = yaml.safe_load(open(os.path.join(ROOT, "config", "body.yaml")))
        for ref, t in trims.items():
            vals = []
            for sign, key in re.findall(r"([+-]?)\s*([a-z_]+\.[a-z_0-9]+)", t["max"]):
                sect, k = key.split(".")
                v = float(body[sect][k]["value"])
                vals.append((-v if sign == "-" else v, key))
            mm = round(sum(v for v, _ in vals), 3)
            calc = " ".join(f"{'-' if v < 0 else '+'} {key} {abs(v):g}" for v, key in vals)[2:]
            fit[ref] = f"cut its tails and their solder to at most {mm:g} mm below the board's bottom face [calc: {calc}]: {t['why']}"
        missing = sorted(set(fit) - {h[0] for h in hand})
        if missing:
            sys.exit(f"pcb: layout.yaml hand_trim: names {', '.join(missing)}, not a hand part on this board")
    with open(os.path.join(fab, name + "-hand-assembly.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Value", "Manufacturer", "MPN"] + (["Fit"] if fit else []))
        w.writerows([list(h) + ([fit.get(h[0], "")] if fit else []) for h in hand])
    if none:
        print(f"pcb: not in any order (Assembly = none: excluded from the BOM, or a net tie drawn in copper): {', '.join(none)}")
    subs = re.findall(r'\(property "Sheetfile" "([^"]+)"', open(root).read())
    extra = [os.path.join(bdir, "layout.yaml"), os.path.join(ROOT, "config", "body.yaml")] if fit else []
    return [root] + sorted({os.path.normpath(os.path.join(bdir, s)) for s in subs}) + [JLC_ROTATION] + extra


def cmd_render(bdir, preview=None):
    """3D views of both sides, 2D copper plots, and the fabrication outputs - all recorded
    in hardware/SHEETS.csv against the .kicad_pcb, so tools/kicad.py check reports them
    stale when the board moves.

    Nothing is written until everything is: the board must pass `check` first, every 3D
    model it names must exist, and the outputs are made in a scratch directory and moved
    in at the end. A refusal half-way used to leave fab/ deleted and the renders
    rewritten with no ledger row, which kicad.py check then blamed on a hand edit (K7-7).

    `--preview <dir>`: the same renders and fab files into <dir> OUTSIDE the repository,
    for a board that does not pass yet - the board is not asked to pass, nothing goes
    into the board's directory or the ledger, and the output says it is a preview."""
    import shutil
    import kicad
    name = os.path.basename(bdir)
    pcb = os.path.join(bdir, name + ".kicad_pcb")
    if preview:
        preview = os.path.abspath(preview)
        if preview.startswith(ROOT + os.sep):
            sys.exit("pcb: a --preview directory must be outside the repository: its files are not ledgered")
        if cmd_check(bdir):
            print("pcb: PREVIEW of a board that FAILS its check (above) - not for ordering")
    elif cmd_check(bdir):
        sys.exit("pcb: not rendering a board that fails its check - nothing was written")
    env = kicad_env()
    missing = missing_models(pcbnew.LoadBoard(pcb), bdir, env)
    if missing and preview:
        print("pcb: PREVIEW - these parts have no 3D model and render as nothing:\n  " + "\n  ".join(missing))
    elif missing:
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
        # and straight down on each side: the view a builder has, where every
        # silkscreen label reads clear of the parts (the angled ones hide those
        # behind a tall switch)
        for side in ("top", "bottom"):
            o = os.path.join(t, f"{name}.pcb-plan-{side}.png")
            subprocess.run(["kicad-cli", "pcb", "render", "--side", side, "--width", "1800", "--height", "1000",
                            "--quality", "high", "--zoom", "1.6", "-o", o, pcb],
                           capture_output=True, text=True, env=env, check=True)
            outs.append(o)
        # every copper layer: a key board's two, a four-layer board's inner planes between
        # (seen from above, as the top is)
        inner = [f"In{k}.Cu" for k in range(1, pcbnew.LoadBoard(pcb).GetCopperLayerCount() - 1)]
        plots = [("F.Cu,Edge.Cuts", "copper-top", False)] + [(f"{L},Edge.Cuts", f"copper-in{k}", False) for k, L in enumerate(inner, 1)] \
            + [("B.Cu,Edge.Cuts,B.Fab", "copper-bottom", True)]
        for layers, tag, mirror in plots:
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
        # JLCPCB asks - the standoff holes stay unplated (ADR 0020) except a bond_mount.
        fab = os.path.join(t, "fab")
        os.makedirs(fab)
        subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "--no-protel-ext", "--layers", ",".join(["F.Cu"] + inner + ["B.Cu", "F.Paste", "B.Paste", "F.Silkscreen", "B.Silkscreen", "F.Mask", "B.Mask", "Edge.Cuts"]), "-o", fab + "/", pcb],
                       capture_output=True, text=True, env=env, check=True)
        subprocess.run(["kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "-o", fab + "/", pcb],
                       capture_output=True, text=True, env=env, check=True)
        subprocess.run(["kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
                        "-o", os.path.join(fab, name + "-pos.csv"), pcb], capture_output=True, text=True, env=env, check=True)
        sheets = assembly_files(bdir, name, fab)
        if preview:
            os.makedirs(preview, exist_ok=True)
            for o in outs:
                shutil.copy(o, preview)
            shutil.copytree(fab, os.path.join(preview, "fab"), dirs_exist_ok=True)
            print(f"pcb: PREVIEW written to {preview} (not in the repository, not ledgered)")
            return
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
    if len(sys.argv) >= 4 and sys.argv[1] == "update-footprints":
        sys.exit(cmd_update_footprints(os.path.join(ROOT, sys.argv[2].rstrip("/")),
                                       [a for a in sys.argv[3:] if not a.startswith("--")], "--pads-resized" in sys.argv) or 0)
    if len(sys.argv) >= 3 and sys.argv[1] in ("layout", "check", "render", "finish", "route", "stackup"):
        d = os.path.join(ROOT, sys.argv[2].rstrip("/"))
        sys.exit({"layout": lambda: cmd_layout(d, "--force" in sys.argv, "--no-route" not in sys.argv), "check": lambda: cmd_check(d),
                  "finish": lambda: cmd_finish(d), "route": lambda: cmd_route(d), "stackup": lambda: cmd_stackup(d),
                  "render": lambda: cmd_render(d, sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None)}[sys.argv[1]]() or 0)
    print(__doc__)
    sys.exit(2)
