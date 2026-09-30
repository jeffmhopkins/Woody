"""The MAIN BOARD kind for tools/pcb.py - `kind: main` in a board's layout.yaml.

A key board's layout (tools/pcb.py's own build) is two layers, its switches on
top and its parts underneath. The main board is four layers, its parts on top
and its thumb switches on the UNDERSIDE (they come in from below), and it
carries planes, an analog island and a net tie. What it shares with the key
boards - the sheets' netlist, footprints, the T of each key network, the design
rules, the stackup, the checks - is tools/pcb.py's; what is only the main
board's is here.

WHERE THINGS COME FROM (as for a key board, nothing is typed in twice):

  the netlist, footprints, references   the board's KiCad sheets (ADR 0019)
  the outline                           mechanical/export/main-board.dxf, less the
                                        mounts' holes (their footprints drill them);
                                        the U-bolt legs' holes and the sensor slot stay
                                        in Edge.Cuts: routed, unplated
  switches, J-CHAIN x2, J-MCU, J-UMB,   mechanical/export/pcb-geometry.echo, the
  U-BREATH, the LED row, mounts, U-bolt `main` entries
  legs, keep-outs, thickness
  everything else's place               layout.yaml parts:
  planes, the island, net classes       layout.yaml planes:, islands:, net_classes:

Coordinates are the key boards': body x along the body from the mouth, y across
it, seen from above; pcb x = body x + OX, pcb y = OY - body y (pcb.to_pcb).
"""
import math
import os
import re
import sys

import pcbnew
import yaml
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import polygonize, unary_union

import pcb

MM, V, to_pcb = pcb.MM, pcb.V, pcb.to_pcb
ROOT = pcb.ROOT
LAYER = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}


def to_body(px, py):
    return (px - pcb.OX, pcb.OY - py)


def xy_mm(v):
    return (pcbnew.ToMM(v.x), pcbnew.ToMM(v.y))


# ------------------------------------------------------------------ the body CAD's main-board lines

def geometry(cluster="main"):
    """Every `main` line of pcb-geometry.echo, by kind (mechanical/cad/woody_body.scad
    says what each field is, beside the echo that writes it)."""
    g = {"switches": {}, "chains": {}, "connectors": {}, "parts": {}, "leds": {}, "standoffs": [],
         "ubolts": [], "keepouts": {}}
    for line in open(os.path.join(ROOT, "mechanical", "export", "pcb-geometry.echo")):
        m = re.match(r'ECHO: "PCB", "(\w+)", "(\w+)", (.*)', line)
        if not m or m.group(1) != cluster:
            continue
        kind, rest = m.group(2), [t.strip().strip('"') for t in m.group(3).split(",")]
        f = [float(v) if re.match(r"^-?[\d.]+(e-?\d+)?$", v) else v for v in rest[1:]]
        if kind == "switch":
            g["switches"][rest[0]] = tuple(f[:3])
        elif kind == "chain":
            g["chains"][rest[0]] = tuple(f[:5])        # mouth x, centre y, facing (+1 tail), length, mouth to far row
        elif kind == "connector":
            g["connectors"][rest[0]] = f
        elif kind == "part":
            g["parts"][rest[0]] = f
        elif kind == "led":
            g["leds"][int(rest[0][3:])] = tuple(f[:6])  # x, y, rot, court along, across, height
        elif kind == "standoff":
            g["standoffs"].append(tuple(f[:6]))       # x, y, hole, top bearing, underside bearing, kind
        elif kind == "ubolt":
            g["ubolts"].append(tuple(f[:5]))          # x, y, hole, top bearing, underside bearing
        elif kind == "keepout":
            g["keepouts"][rest[0]] = f
        elif kind == "board":
            g["thickness"] = f[0]
    return g


def outline_segments(lay, geo):
    """The DXF's segments less each mount's hole (its footprint drills it; a hole
    in Edge.Cuts as well is a second, routed, hole)."""
    segs = pcb.dxf_segments(os.path.join(ROOT, "mechanical", "export", lay["outline"]))
    keep = []
    for a, b in segs:
        if any(math.hypot(a[0] - s[0], a[1] - s[1]) < s[2] / 2 + 0.3 and math.hypot(b[0] - s[0], b[1] - s[1]) < s[2] / 2 + 0.3
               for s in geo["standoffs"]):
            continue
        keep.append((a, b))
    return keep


def board_polygon(segs):
    """The board in BODY coordinates: the outer loop less every inner loop."""
    polys = sorted(polygonize([LineString([a, b]) for a, b in segs]), key=lambda p: -p.area)
    outer = polys[0]
    for p in polys[1:]:
        if outer.contains(p.representative_point()):
            outer = outer.difference(p)
    return outer


# ------------------------------------------------------------------ placing

def pad_body(p):
    return to_body(*xy_mm(p.GetPosition()))


def place_switch(board, fp, x, y, r):
    """A thumb switch hangs face down under the board, so seen from above it is the
    key-board footprint MIRRORED about the body's x axis through its centre, then
    turned by the body CAD's rotation. The KiCad rotation on the bottom that puts
    pins 1 and 2 there is FOUND, as place_chain finds its own."""
    px, py = to_pcb(x, y)
    pcb.place(board, fp, px, py, 0, False)
    own = {p.GetNumber(): pad_body(p) for p in fp.Pads() if p.GetNumber() in ("1", "2")}
    board.Remove(fp)
    a = math.radians(r)
    want = {}
    for n, (bx, by) in own.items():
        dx, dy = bx - x, -(by - y)
        want[n] = (x + dx * math.cos(a) - dy * math.sin(a), y + dx * math.sin(a) + dy * math.cos(a))
    for krot in (0, 90, 180, 270):
        pcb.place(board, fp, px, py, krot, True)
        got = {p.GetNumber(): pad_body(p) for p in fp.Pads() if p.GetNumber() in want}
        if all(math.hypot(got[n][0] - want[n][0], got[n][1] - want[n][1]) < 0.01 for n in want):
            return krot
        board.Remove(fp)
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    raise SystemExit(f"pcb: no bottom-side rotation puts {fp.GetReference()}'s pins where the body CAD's mirror does")


def place_connector(board, fp, spec, geo):
    """J-MCU, J-UMB: layout.yaml connectors: - the pad row farthest from the mouth
    (lowest body x; the mouth faces the tail) at `back_row_at` from the echo's
    `back_row_from` (x0, the insulator's mouth-end face, or x1, its tail-end face),
    the pads centred across the body on the echo's y."""
    c = geo["connectors"][spec["cad"]]
    x0, x1, y = c[0], c[1], c[2]
    pcb.place(board, fp, 0, 0, spec["rot"], spec.get("bottom", False))
    xs = [pad_body(p)[0] for p in fp.Pads()]
    ys = [pad_body(p)[1] for p in fp.Pads()]
    want_x = {"x0": x0, "x1": x1}[spec["back_row_from"]] + spec["back_row_at"]
    fp.Move(V(want_x - min(xs), -(y - (min(ys) + max(ys)) / 2)))
    return want_x, y


def led_chain(comps, nets, row="D-LED"):
    """The LED references in data order: LED1 takes its DI (pin 4) from the one net that
    reaches no other LED's DO (pin 3); each next one's DI is the last one's DO. The body
    CAD numbers its LED places the same way (LED1 at the tail, where the data arrives)."""
    leds = sorted(r for r, c in comps.items() if c["row"] == row)
    netof = {(r, p): n for n, nodes in nets for r, p in nodes}
    do = {netof.get((r, "3")): r for r in leds}
    first = [r for r in leds if netof.get((r, "4")) not in do]
    if len(first) != 1:
        sys.exit(f"pcb: the LED row's data chain has {len(first)} starts ({first}), not one")
    order = first
    while len(order) < len(leds):
        nxt = [r for r in leds if netof.get((r, "4")) == netof.get((order[-1], "3"))]
        if len(nxt) != 1:
            sys.exit(f"pcb: the LED row's data chain breaks after {order[-1]}")
        order += nxt
    return order


def fix_t_on_top(fps, comps, keys):
    """pcb.network_parts' rotations are measured on the BOTTOM face; on the top each
    part whose KEY pad is not the nearer of its two to the junction is turned 180."""
    for key in keys:
        refs = [pcb.ref_of(comps, row, key) for row in ("R-KEY-SER", "R-KEY-PU", "C-KEY")]
        s_, p_ = fps[refs[0]].GetPosition(), fps[refs[1]].GetPosition()
        jx, jy = (s_.x + p_.x) / 2, (s_.y + p_.y) / 2
        keynet = fps[refs[0]].FindPadByNumber("1").GetNetname()
        for r in refs:
            pads = sorted(fps[r].Pads(), key=lambda pd: math.hypot(pd.GetPosition().x - jx, pd.GetPosition().y - jy))
            if pads[0].GetNetname() != keynet:
                fps[r].SetOrientationDegrees(fps[r].GetOrientationDegrees() + 180)
        pads = sorted((pd for r in refs for pd in fps[r].Pads()), key=lambda pd: math.hypot(pd.GetPosition().x - jx, pd.GetPosition().y - jy))
        if len({pd.GetNetname() for pd in pads[:3]}) != 1:
            sys.exit(f"pcb: {key}'s network is not a T round its node")


def rule_area(board, poly_body, name, layers, footprints=False, copper=True):
    """A KiCad rule area (a keep-out) over a body-coordinate polygon: no tracks, vias or
    pour of any net where `copper`, no footprint courtyard where `footprints`."""
    for g in ([poly_body] if poly_body.geom_type == "Polygon" else list(poly_body.geoms)):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        ls = pcbnew.LSET()
        for L in layers:
            ls.AddLayer(LAYER[L])
        z.SetLayerSet(ls)
        z.SetZoneName(name)
        z.SetDoNotAllowTracks(copper)
        z.SetDoNotAllowVias(copper)
        z.SetDoNotAllowCopperPour(copper)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(footprints)
        outline_into(z.Outline(), g)
        board.Add(z)


def outline_into(ol, g):
    """A body-coordinate shapely polygon into a zone's outline, its holes kept."""
    ol.NewOutline()
    for (x, y) in list(g.exterior.coords)[:-1]:
        ol.Append(*[MM(v) for v in to_pcb(x, y)])
    for hole in g.interiors:
        hi = ol.NewHole()
        for (x, y) in list(hole.coords)[:-1]:
            ol.Append(MM(to_pcb(x, y)[0]), MM(to_pcb(x, y)[1]), 0, hi)


def copper_zone(board, net, layer, poly_body, priority=0, name=""):
    """A filled copper zone (a plane, an island, a pour) over a body polygon, holes kept."""
    for g in ([poly_body] if poly_body.geom_type == "Polygon" else list(poly_body.geoms)):
        z = pcbnew.ZONE(board)
        z.SetLayer(LAYER[layer])
        z.SetNet(board.FindNet(net))
        z.SetAssignedPriority(priority)
        z.SetZoneName(name or net)
        z.SetMinThickness(MM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
        z.SetThermalReliefGap(MM(0.3))
        z.SetThermalReliefSpokeWidth(MM(0.4))
        outline_into(z.Outline(), g)
        z.SetIsFilled(False)
        board.Add(z)


def island_polys(lay):
    """layout.yaml islands: each as (spec, the island in body coords, the island grown by
    its moat - the hole it leaves in its plane)."""
    out = []
    for isl in lay.get("islands") or []:
        p = Polygon(isl["outline"])
        if not p.is_valid:
            sys.exit(f"pcb: islands: {isl['net']}'s outline is not a simple polygon")
        out.append((isl, p, p.buffer(isl["moat"], join_style=2)))
    return out


# ------------------------------------------------------------------ building the board

def build(bdir, lay):
    name = os.path.basename(bdir)
    geo = geometry(lay["cluster"])
    comps, nets = pcb.sheet_netlist(os.path.join(bdir, name + ".kicad_sch"))
    skip = lay.get("not_on_board") or {}
    for ref in skip:
        if ref not in comps:
            sys.exit(f"pcb: not_on_board: {ref} is not on the sheets")
    board = pcb.new_board(bdir, lay, geo)
    segs = outline_segments(lay, geo)
    pcb.add_outline(board, segs)
    outline = board_polygon(segs)
    netinfo, fps = pcb.load_parts(board, comps, nets, skip)

    body = yaml.safe_load(open(os.path.join(ROOT, "config", "body.yaml")))
    below_seat = float(body["switch"]["thumb_pcb_below_seat"]["value"])
    placed = set()
    # the thumb switches: UNDERSIDE, where the body CAD puts them
    for key, (x, y, r) in geo["switches"].items():
        ref = pcb.ref_of(comps, "SW1-n", key)
        place_switch(board, fps[ref], x, y, r)
        models = fps[ref].Models()
        for i in range(len(models)):      # by index: SWIG's iterator hands out copies
            models[i].m_Offset.z = below_seat
        placed.add(ref)
    # the chain headers: TOP, their mouths along the body as the CAD faces them; each is
    # the header whose pin 10 carries its own side's chain 3V3 (V3V3_CHAIN_LH / _RH)
    for cname, ch in geo["chains"].items():
        side = cname.split("-")[-1]
        refs = [r for r, c in comps.items() if c["row"] == "J-CHAIN" and r in fps
                and fps[r].FindPadByNumber("10").GetNetname().endswith("_" + side)]
        if len(refs) != 1:
            sys.exit(f"pcb: expected one J-CHAIN on the {side} chain's 3V3, found {refs}")
        pcb.place_chain(board, fps[refs[0]], {"chain": ch}, bottom=False)
        placed.add(refs[0])
    for cad, spec in (lay.get("connectors") or {}).items():
        ref = pcb.ref_of(comps, spec["row"])
        place_connector(board, fps[ref], {**spec, "cad": cad}, geo)
        placed.add(ref)
    # U-BREATH: its pads centred on the echo's centre
    for cad, spec in (lay.get("cad_parts") or {}).items():
        ref = pcb.ref_of(comps, spec["row"])
        x, y = geo["parts"][cad][0], geo["parts"][cad][1]
        pcb.place(board, fps[ref], 0, 0, spec["rot"], spec.get("bottom", False))
        cx, cy = pcb.pads_centre(fps[ref])
        fps[ref].Move(V(to_pcb(x, y)[0] - cx, to_pcb(x, y)[1] - cy))
        placed.add(ref)
    # the LED row (ADR 0028): each LED where the body CAD puts it, in data order, and
    # its 100 nF at layout.yaml led_caps: offset from it
    lc = lay.get("led_caps") or {}
    if geo["leds"]:
        order = led_chain(comps, nets)
        caps = sorted((r for r, c in comps.items() if c["row"] == lc.get("row")), key=lambda r: int(re.sub(r"\D", "", r)))
        if len(order) != len(geo["leds"]) or len(caps) != len(order):
            sys.exit(f"pcb: {len(geo['leds'])} LED places in the body CAD, {len(order)} LEDs and {len(caps)} {lc.get('row')} on the sheets")
        for n, ref in enumerate(order, 1):
            x, y, r = geo["leds"][n][:3]
            pcb.place(board, fps[ref], *to_pcb(x, y), r, False)
            pcb.place(board, fps[caps[n - 1]], *to_pcb(x + lc["offset"][0], y + lc["offset"][1]), lc["rot"], False)
            placed |= {ref, caps[n - 1]}
    # the mounts: every one plated, on its net, pads on both faces (ADR 0022, ADR 0025).
    # On the TOP, the parts' face, so its courtyard keeps the parts off the column's
    # standoff or the end mount's nut; the underside is the switches', and each spacer
    # there sits clear of their housings by the body CAD's own rule (drc.echo "columns
    # vertical").
    mount = lay["mounts"]
    for i, (x, y, hole, top, under, kind) in enumerate(geo["standoffs"], 1):
        h = pcb.load_fp(mount["footprint"])
        h.SetReference(f"H{i}")
        h.SetValue(f"mount {kind}")
        h.SetBoardOnly(True)
        h.SetExcludedFromBOM(True)
        h.SetExcludedFromPosFiles(True)
        h.Reference().SetLayer(pcbnew.F_Fab)
        pcb.place(board, h, *to_pcb(x, y), 0, False)
        for pad in h.Pads():
            pad.SetNet(board.FindNet(mount["net"]))
        # what bears on each face: no part and no other copper there. Its own pad is
        # the mount's net, and a rule area keeps every track and via off (pcb.py
        # check_mounts holds the other nets off, pads included)
        clear = lay["rules"]["clearance"]
        rule_area(board, Point(x, y).buffer(top / 2 + clear, 32), f"H{i} top bearing", ["F.Cu"])
        rule_area(board, Point(x, y).buffer(under / 2 + clear, 32), f"H{i} underside bearing", ["B.Cu"])
    # the U-bolt legs: unplated holes in the outline, with the outer layers' copper
    # keep-out round the washer and nut above and the spacer below (drc.echo "main
    # board neck at the U-bolt station"); the planes run on past them
    ub = lay.get("ubolt") or {}
    for j, (x, y, hole, top, under) in enumerate(geo["ubolts"], 1):
        rule_area(board, Point(x, y).buffer(top / 2 + ub["copper_keepout"], 32), f"U-bolt leg {j} top", ["F.Cu"], footprints=True)
        rule_area(board, Point(x, y).buffer(under / 2 + ub["copper_keepout"], 32), f"U-bolt leg {j} underside", ["B.Cu"], footprints=True)
    # the key networks: the key boards' T, on the TOP face here
    nw = lay.get("networks") or {}
    net_parts = pcb.network_parts({"networks": {k: v for k, v in nw.items() if k != "spare"}}, {"switches": geo["switches"]}, comps)
    for key, spec in (nw.get("spare") or {}).items():
        net_parts.update(pcb.t_parts(comps, key, spec["at"][0], spec["at"][1], {**nw["pattern"], **spec}))
    for ref, (x, y, r) in net_parts.items():
        pcb.place(board, fps[ref], *to_pcb(x, y), r, False)
        placed.add(ref)
    fix_t_on_top(fps, comps, list(geo["switches"]) + list(nw.get("spare") or {}))
    # everything else: layout.yaml parts:, body coordinates, the top face unless it says bottom
    for ref, v in (lay.get("parts") or {}).items():
        if ref not in fps:
            sys.exit(f"pcb: parts: {ref} is not a part on this board's sheets")
        x, y, r = v[:3]
        pcb.place(board, fps[ref], *to_pcb(x, y), r, len(v) > 3 and v[3] == "bottom")
        placed.add(ref)
    missing = sorted(set(fps) - placed)
    if missing:
        sys.exit(f"pcb: not placed (add them to layout.yaml parts): {', '.join(missing)}")

    # keep-outs from the body CAD: nothing but its own header under each chain
    # ribbon's plug and fold; nothing but U-BUCK in the regulator block; parts under
    # the Matrix ribbon only as tall as its room (pcb.py check_heights)
    for kname, spec in (lay.get("keepouts") or {}).items():
        k = geo["keepouts"][kname] if kname in geo["keepouts"] else None
        if spec.get("part"):
            p = geo["parts"][spec["part"]]
            x0, y0, x1, y1 = p[0] - p[3] / 2, p[1] - p[4] / 2, p[0] + p[3] / 2, p[1] + p[4] / 2
        else:
            x0, y0, x1, y1 = k[:4]
        rect = box(x0, y0, x1, y1)
        # the parts the body CAD puts there itself (the ribbon's own header, U-BUCK) are cut out
        for ref, fp in fps.items():
            if comps[ref]["row"] in spec.get("except_rows", []) and not fp.IsFlipped():
                cy = courtyard_body(fp)
                if cy.intersects(rect):
                    rect = rect.difference(cy.buffer(0.05))
        rule_area(board, rect, kname, ["F.Cu"], footprints=True, copper=False)

    # planes, islands and pours (layout.yaml planes:, islands:)
    isl = island_polys(lay)
    for pl in lay.get("planes") or []:
        region = outline
        for spec, p, moat in isl:
            if spec["layer"] == pl["layer"]:
                region = region.difference(moat)
        copper_zone(board, pl["net"], pl["layer"], region, 0, pl.get("name", pl["net"]))
    for spec, p, moat in isl:
        copper_zone(board, spec["net"], spec["layer"], p.intersection(outline), 1, spec["net"] + " island")
    return board, fps, netinfo, lay, comps, outline


def courtyard_body(fp):
    layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    c = fp.GetCourtyard(layer)
    return unary_union([Polygon([to_body(*xy_mm(c.Outline(i).CPoint(j))) for j in range(c.Outline(i).PointCount())])
                        for i in range(c.OutlineCount())])


# ------------------------------------------------------------------ checking

def copper_near(board, disc_pcb, layer, but_net=None, skip_ref=None):
    """Every piece of copper on `layer` within a PCB-mm shapely region, as 'what' strings:
    tracks, vias, pads (not `skip_ref`'s) and filled zones, other than `but_net`'s."""
    hits = set()
    for t in board.GetTracks():
        if t.IsOnLayer(layer) and t.GetNetname() != but_net and pcb.item_shape(t, layer).intersects(disc_pcb):
            hits.add(f"{t.GetNetname()} {'via' if isinstance(t, pcbnew.PCB_VIA) else 'track'}")
    for f in board.GetFootprints():
        if f.GetReference() == skip_ref:
            continue
        for p in f.Pads():
            if p.IsOnLayer(layer) and p.GetNetname() != but_net and pcb.item_shape(p, layer).intersects(disc_pcb):
                hits.add(f"{f.GetReference()} pad {p.GetNumber()}")
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.IsOnLayer(layer) and z.GetNetname() != but_net and z.GetFilledPolysList(layer).OutlineCount() \
                and pcb.shapely_of(z.GetFilledPolysList(layer)).intersects(disc_pcb):
            hits.add(f"{z.GetNetname()} pour")
    return sorted(hits)


def check_cad(board, lay, comps):
    """The body CAD still agrees with the main board: thickness, outline, and every
    switch, chain header, connector, the sensor, LED, mount and U-bolt leg where - and
    which way up - it puts them; no copper where the mounts' and legs' hardware bears;
    every top-face part inside its height room."""
    bad = []
    geo = geometry(lay["cluster"])
    body = yaml.safe_load(open(os.path.join(ROOT, "config", "body.yaml")))
    t_cfg = float(body["switch"]["pcb_t"]["value"])
    t_pcb = pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())
    if abs(geo.get("thickness", -1) - t_cfg) > 1e-6:
        bad.append(f"error: [cad] pcb-geometry.echo says the main board is {geo.get('thickness')} mm, config/body.yaml switch.pcb_t {t_cfg:g} - run: python3 tools/cad.py build")
    if abs(t_pcb - t_cfg) > 1e-6:
        bad.append(f"error: [cad] the board is {t_pcb:g} mm thick, the body CAD's main board {t_cfg:g} (switch.pcb_t)")
    ol = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(ol):
        bad.append("error: [cad] the Edge.Cuts outline is not closed")
    else:
        from shapely.geometry import MultiLineString
        cad = MultiLineString([(to_pcb(*a), to_pcb(*b)) for a, b in outline_segments(lay, geo)])
        off = pcb.shapely_of(ol).boundary.hausdorff_distance(cad)
        if off > 0.05:
            bad.append(f"error: [cad] the Edge.Cuts outline is up to {off:.2f} mm from the body CAD's (mechanical/export/{lay['outline']}, less the mounts' holes)")
    fp_of = {f.GetReference(): f for f in board.GetFootprints()}
    below = float(body["switch"]["thumb_pcb_below_seat"]["value"])
    for key, (x, y, r) in geo["switches"].items():
        ref = pcb.ref_of(comps, "SW1-n", key)
        fp = fp_of.get(ref)
        if fp is None:
            bad.append(f"error: [cad] {key}'s switch {ref} is not on the board")
            continue
        got = to_body(*xy_mm(fp.GetPosition()))
        if math.hypot(got[0] - x, got[1] - y) > 0.05 or not fp.IsFlipped():
            bad.append(f"error: [cad] {ref} ({key}) is at body {tuple(round(v, 2) for v in got)}{'' if fp.IsFlipped() else ' on the TOP'}; "
                       f"the body CAD puts it at ({x}, {y}), underneath")
        # its pins where the CAD's mirrored switch has them: a copy placed afresh
        probe = pcbnew.BOARD()
        cp = pcb.load_fp(fp.GetFPID().GetLibNickname().wx_str() + ":" + fp.GetFPID().GetLibItemName().wx_str())
        place_switch(probe, cp, x, y, r)
        want = {p.GetNumber(): pad_body(p) for p in cp.Pads() if p.GetNumber()}
        have = {p.GetNumber(): pad_body(p) for p in fp.Pads() if p.GetNumber()}
        if any(math.hypot(have[n][0] - want[n][0], have[n][1] - want[n][1]) > 0.05 for n in want):
            bad.append(f"error: [cad] {ref} ({key})'s pins are not where the body CAD's switch, turned {r:g} deg and hanging face down, has them")
        models = fp.Models()
        for i in range(len(models)):
            if abs(models[i].m_Offset.z - below) > 1e-6:
                bad.append(f"error: [cad] {ref}'s 3D model sits {models[i].m_Offset.z:g} mm off; config/body.yaml switch.thumb_pcb_below_seat is {below:g}")
    for cname, ch in geo["chains"].items():
        side = cname.split("-")[-1]
        refs = [r for r, c in comps.items() if c["row"] == "J-CHAIN" and r in fp_of
                and fp_of[r].FindPadByNumber("10").GetNetname().endswith("_" + side)]
        if len(refs) != 1:
            bad.append(f"error: [cad] {cname}: expected one J-CHAIN on the {side} chain's 3V3, found {refs}")
            continue
        fp = fp_of[refs[0]]
        (tx, ty), d = pcb.chain_target({"chain": ch})
        got = pcb.pads_centre(fp)
        p1, p2 = fp.FindPadByNumber("1").GetPosition(), fp.FindPadByNumber("2").GetPosition()
        if math.hypot(got[0] - tx, got[1] - ty) > 0.05 or pcbnew.ToMM(p2.x - p1.x) * d <= 0 or fp.IsFlipped():
            bad.append(f"error: [cad] {refs[0]} ({cname})'s pads centre at {tuple(round(v, 2) for v in got)}{' on the bottom' if fp.IsFlipped() else ''}; "
                       f"the body CAD puts them at ({tx:.2f}, {ty:.2f}) facing {'+' if d > 0 else '-'}x, on top")
    for cad, spec in (lay.get("connectors") or {}).items():
        ref = pcb.ref_of(comps, spec["row"])
        fp = fp_of[ref]
        c = geo["connectors"][cad]
        xs = [pad_body(p)[0] for p in fp.Pads()]
        ys = [pad_body(p)[1] for p in fp.Pads()]
        want_x = {"x0": c[0], "x1": c[1]}[spec["back_row_from"]] + spec["back_row_at"]
        if abs(min(xs) - want_x) > 0.05 or abs((min(ys) + max(ys)) / 2 - c[2]) > 0.05:
            bad.append(f"error: [cad] {ref} ({cad})'s back pad row is at x {min(xs):.2f}, centred y {(min(ys) + max(ys)) / 2:.2f}; "
                       f"the body CAD and layout.yaml connectors: put it at x {want_x:.2f}, y {c[2]}")
    for cad, spec in (lay.get("cad_parts") or {}).items():
        ref = pcb.ref_of(comps, spec["row"])
        cx, cy = to_body(*pcb.pads_centre(fp_of[ref]))
        x, y = geo["parts"][cad][:2]
        if math.hypot(cx - x, cy - y) > 0.05:
            bad.append(f"error: [cad] {ref} ({cad})'s pads centre at ({cx:.2f}, {cy:.2f}); the body CAD puts it at ({x}, {y})")
    if geo["leds"]:
        order = led_chain(comps, _nets_of(board))
        for n, ref in enumerate(order, 1):
            x, y, r = geo["leds"][n][:3]
            fp = fp_of[ref]
            got = to_body(*xy_mm(fp.GetPosition()))
            if math.hypot(got[0] - x, got[1] - y) > 0.05 or abs((fp.GetOrientationDegrees() - r) % 360) > 0.01 or fp.IsFlipped():
                bad.append(f"error: [cad] {ref} (LED{n} along the data chain) is at {tuple(round(v, 2) for v in got)} turned "
                           f"{fp.GetOrientationDegrees():g}; the body CAD puts LED{n} at ({x}, {y}) turned {r:g}, on top")
    clear = float(lay["rules"]["clearance"])
    mount = lay["mounts"]
    for i, (x, y, hole, top, under, kind) in enumerate(geo["standoffs"], 1):
        fp = fp_of.get(f"H{i}")
        got = None if fp is None else to_body(*xy_mm(fp.GetPosition()))
        if got is None or math.hypot(got[0] - x, got[1] - y) > 0.05:
            bad.append(f"error: [cad] mount H{i} ({kind}) is at {got}; the body CAD puts it at ({x}, {y})")
            continue
        drilled = [p for p in fp.Pads() if p.GetDrillSize().x > 0]
        if not drilled or any(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or abs(pcbnew.ToMM(p.GetDrillSize().x) - hole) > 0.01 for p in drilled):
            bad.append(f"error: [cad] H{i} must be a plated {hole:g} mm hole (ADR 0025)")
        for p in fp.Pads():
            if p.GetNetname() != mount["net"]:
                bad.append(f"error: [cad] H{i} pad on '{p.GetNetname()}', not {mount['net']} - every mount grounds the plates")
        px, py = to_pcb(x, y)
        for L, dia in ((pcbnew.F_Cu, top), (pcbnew.B_Cu, under)):
            hits = copper_near(board, Point(px, py).buffer(dia / 2 + clear - 0.02), L, mount["net"], f"H{i}")
            if hits:
                bad.append(f"error: [cad] {', '.join(hits)} under mount H{i}'s {'standoff or nut' if L == pcbnew.F_Cu else 'spacer'} on "
                           f"{board.GetLayerName(L)} - the hardware bonds {mount['net']} there")
    ub = lay.get("ubolt") or {}
    for j, (x, y, hole, top, under) in enumerate(geo["ubolts"], 1):
        px, py = to_pcb(x, y)
        for L, dia in ((pcbnew.F_Cu, top), (pcbnew.B_Cu, under)):
            hits = copper_near(board, Point(px, py).buffer(dia / 2 + ub["copper_keepout"] - 0.02), L)
            if hits:
                bad.append(f"error: [cad] {', '.join(hits)} within the U-bolt leg {j}'s {'washer and nut' if L == pcbnew.F_Cu else 'spacer'} "
                           f"keep-out on {board.GetLayerName(L)} (the leg is outside metal on the strap)")
    bad += check_heights(board, lay, geo)
    return bad


def _nets_of(board):
    """(net, [(ref, pad)]) from the board itself, for checks that need the sheets' nets."""
    out = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            out.setdefault(p.GetNetname(), []).append((f.GetReference(), p.GetNumber()))
    return list(out.items())


def check_heights(board, lay, geo):
    """Every top-face part inside its height room: under a key board, where none is
    overhead, and under the Matrix ribbon's level run (pcb-geometry.echo keep-outs),
    each part's height from layout.yaml heights: by footprint name."""
    bad = []
    k = geo["keepouts"]
    rooms = [(box(*v[:4]), v[4], name) for name, v in k.items() if name.startswith("under key board") or name == "Matrix ribbon"]
    else_room = k["elsewhere"][4]
    heights = lay.get("heights") or {}
    for fp in board.GetFootprints():
        if fp.IsFlipped() or fp.GetReference().startswith("H"):
            continue
        name = fp.GetFPID().GetLibItemName().wx_str()
        h = next((v for key, v in heights.items() if key in name), None)
        if h is None:
            bad.append(f"error: [height] {fp.GetReference()} ({name}) has no height in layout.yaml heights:")
            continue
        cy = courtyard_body(fp)
        if cy.is_empty:
            continue
        room, where = else_room, "where no key board is overhead"
        for rect, r, nm in rooms:
            if cy.intersects(rect) and cy.intersection(rect).area > 1e-3 and r < room:
                if nm == "Matrix ribbon" and fp.GetReference() == "J1":
                    continue
                room, where = r, nm
        if h > room + 1e-6:
            bad.append(f"error: [height] {fp.GetReference()} stands {h:g} mm; its room ({where}) is {room:g}")
    return bad


def check_planes(board, lay):
    """The planes and the island as layout.yaml says: each plane and island zone on its
    layer and net; every pad of an island's net on the island (but its off_island: ones),
    every via of it inside the island and every other plane net's via outside the moat;
    ONE tie between the island and its plane, the named net tie; and no signal track on
    an outer layer crossing a split in its reference plane (layer 1 over layer 2, layer 4
    over layer 3) - except across a moat at its tie's window, or a pair where it crosses."""
    bad = []
    zones = [z for z in board.Zones() if not z.GetIsRuleArea()]
    for pl in lay.get("planes") or []:
        if not any(z.GetLayerName() == pl["layer"] and z.GetNetname() == pl["net"] for z in zones):
            bad.append(f"error: [planes] no {pl['net']} plane on {pl['layer']}")
    pair_nets = {n for pr in lay.get("pairs") or [] for n in pr["nets"]}
    plane_nets = {pl["net"] for pl in lay.get("planes") or []} | {s["net"] for s in lay.get("islands") or []}
    isl = island_polys(lay)
    for spec, p, moat in isl:
        P = Polygon([to_pcb(x, y) for x, y in p.exterior.coords])
        M = Polygon([to_pcb(x, y) for x, y in moat.exterior.coords])
        if not any(z.GetLayerName() == spec["layer"] and z.GetNetname() == spec["net"] for z in zones):
            bad.append(f"error: [island] no {spec['net']} island on {spec['layer']}")
        for f in board.GetFootprints():
            for pad in f.Pads():
                name = f"{f.GetReference()}.{pad.GetNumber()}"
                c = Point(*xy_mm(pad.GetPosition()))
                if pad.GetNetname() == spec["net"] and name not in spec.get("off_island", []) and not P.contains(c):
                    bad.append(f"error: [island] {name} is {spec['net']} but off its island - it would return through the plane")
                if pad.GetNetname() in plane_nets - {spec["net"]} and pad.GetNetname() != "UMBILICAL_POS12" and P.contains(c) \
                        and f.GetReference() != spec["tie"]:
                    bad.append(f"error: [island] {name} ({pad.GetNetname()}) stands on the {spec['net']} island")
        for v in board.GetTracks():
            if not isinstance(v, pcbnew.PCB_VIA):
                continue
            c = Point(*xy_mm(v.GetPosition()))
            if v.GetNetname() == spec["net"] and not P.contains(c):
                bad.append(f"error: [island] a {spec['net']} via at ({c.x:.2f}, {c.y:.2f}) is off the island")
            if v.GetNetname() in plane_nets - {spec["net"], "UMBILICAL_POS12"} and M.contains(c):
                bad.append(f"error: [island] a {v.GetNetname()} via at ({c.x:.2f}, {c.y:.2f}) is on the island or its moat")
        # the ties: every net-tie footprint joining the island's net to another
        ties = [f.GetReference() for f in board.GetFootprints() if f.IsNetTie()
                and spec["net"] in {pd.GetNetname() for pd in f.Pads()} and len({pd.GetNetname() for pd in f.Pads()}) > 1]
        if ties != [spec["tie"]]:
            bad.append(f"error: [island] {spec['net']} is tied to its plane by {ties or 'nothing'}; layout.yaml says one tie, {spec['tie']}")
    # splits: each reference layer's fill, its antipads (holes under a few mm2) closed
    ref_of_layer = {pcbnew.F_Cu: "In1.Cu", pcbnew.B_Cu: "In2.Cu"}
    fills = {}
    for L, ref in ref_of_layer.items():
        polys = []
        for z in zones:
            if z.GetLayerName() == ref and z.GetFilledPolysList(z.GetLayer()).OutlineCount():
                g = pcb.shapely_of(z.GetFilledPolysList(z.GetLayer()))
                for part in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
                    polys.append(Polygon(part.exterior.coords, [h.coords for h in part.interiors if Polygon(h).area > 4.0]))
        fills[L] = polys
    windows, moats = [], []
    for spec, p, moat in isl:
        moats.append(Polygon([to_pcb(x, y) for x, y in moat.exterior.coords]).difference(
            Polygon([to_pcb(x, y) for x, y in p.exterior.coords]).buffer(-0.05)))
        tie = board.FindFootprintByReference(spec["tie"])
        if tie:
            windows.append(Point(*xy_mm(tie.GetPosition())).buffer(spec["tie_window"]))
    crossings = {}
    for t in board.GetTracks():
        if type(t) is not pcbnew.PCB_TRACK or t.GetLayer() not in fills or t.GetNetname() in plane_nets - pair_nets:
            continue
        g = pcb.item_shape(t, t.GetLayer())
        if any(g.within(pl) for pl in fills[t.GetLayer()]):
            continue
        if any(g.within(w) for w in windows) or (t.GetNetname() in pair_nets and any(g.intersects(m) for m in moats)):
            continue
        c = g.centroid
        crossings.setdefault((t.GetNetname(), board.GetLayerName(t.GetLayer())), []).append(f"({c.x:.1f}, {c.y:.1f})")
    for (net, layer), where in sorted(crossings.items()):
        bad.append(f"error: [split] {net} on {layer} crosses a split in its reference plane ({ref_of_layer[board.GetLayerID(layer)]}) "
                   f"at {', '.join(where[:4])}{' ...' if len(where) > 4 else ''}")
    return bad
