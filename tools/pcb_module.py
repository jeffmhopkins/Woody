"""The EURORACK MODULE's boards for tools/pcb.py - `kind: module` in a board's layout.yaml.

    hardware/boards/module-main   four layers: the etherCON, every IC, the trimmers, the power header
    hardware/boards/module-jack   two layers: the jacks, the pots, J-B2B-MOD

What they share with the controller's boards - the sheets' netlist, footprints, the
design rules, the stackup, planes and islands, the router, the silkscreen, the checks
- is tools/pcb.py's and tools/pcb_main.py's; what is only the module's is here: where
its fixed parts come from, and the checks that hold them there.

WHERE THINGS COME FROM (nothing is typed in twice):

  the netlist, footprints, references   the board's KiCad sheets (ADR 0019)
  the outline                           mechanical/module/export/<main|jack>-board.dxf, less
                                        each standoff's hole (its footprint drills it)
  the panel-mounted parts - jacks,      mechanical/module/export/pcb-geometry.echo, the
  pots, J-B2B-MOD, J-UMBILICAL,         board's own lines (the module CAD, config/module.yaml);
  J-LED-PANEL, J-PWR-EURO, the          FIXED: `check` fails any that moves
  standoffs, U-ISO, keep-outs, thickness
  everything else's place               layout.yaml parts:

COORDINATES. The module CAD's PANEL FRAME (config/module.yaml): x across the panel from
its left edge, y up from its bottom edge, seen from the front. A board's KiCad top view
is that view with y negated, so the controller's own transform serves: pcb x = x + OX,
pcb y = OY - y (pcb.to_pcb). A board's FRONT face (toward the panel) is KiCad's top,
F.Cu; its REAR face is B.Cu.
"""
import json
import math
import os
import sys

import pcbnew
import yaml
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

import pcb
import pcb_main

MM, V, to_pcb = pcb.MM, pcb.V, pcb.to_pcb
ROOT = pcb.ROOT
to_body, xy_mm = pcb_main.to_body, pcb_main.xy_mm
ECHO = os.path.join(ROOT, "mechanical", "module", "export", "pcb-geometry.echo")


# ------------------------------------------------------------------ the module CAD's lines

def geometry(cluster):
    """Every line of the module's pcb-geometry.echo for this board, by kind. Each line is
    OpenSCAD's echo of a list - strings, numbers and lists - so it reads as JSON."""
    g = {"jacks": {}, "pots": {}, "connectors": {}, "standoffs": [], "tall": [], "keepouts": [], "panel": {}}
    for line in open(ECHO):
        if not line.startswith("ECHO: "):
            continue
        v = json.loads("[" + line[len("ECHO: "):].strip() + "]")
        if v[0] != "PCB" or v[1] != cluster:
            continue
        kind, name, rest = v[2], v[3], v[4:]
        if kind == "board" and name == "thickness":
            g["thickness"] = rest[0]
        elif kind == "jack":
            # barrel x, y; the angle from the barrel to the sleeve pad; pins 3, 2, 1 along it
            g["jacks"][name] = (rest[0], rest[1], rest[2], rest[4])
        elif kind == "pot":
            g["pots"][name] = (rest[0], rest[1], rest[2], rest[4], rest[6])   # shaft x, y, rot, pins' dy, pitch
        elif kind == "connector":
            g["connectors"][name] = rest
        elif kind == "standoff":
            g["standoffs"].append((name, rest[0], rest[1], rest[2], rest[3]))  # name, x, y, hole, head
        elif kind == "tall":
            g["tall"].append((name, rest[0], rest[1]))
        elif kind == "keepout":
            g["keepouts"].append((name, rest))
        elif kind == "panel":
            g["panel"][name] = rest
    return g


# ------------------------------------------------------------------ placing by pads

def pads_frame(fp):
    """{pad number: (x, y)} in the panel frame."""
    return {p.GetNumber(): to_body(*xy_mm(p.GetPosition())) for p in fp.Pads() if p.GetNumber()}


def place_by_pads(board, fp, want, bottom=False):
    """The footprint on its face turned so the pads `want` names land on their panel-frame
    places ({number: (x, y)}): the turn is FOUND, as pcb.place_chain finds its own - on
    the rear face KiCad mirrors, and a guessed turn is how a header lands one column
    over. Exits if no quarter turn fits them all within 0.01 mm."""
    for rot in (0, 90, 180, 270):
        pcb.place(board, fp, 0, 0, rot, bottom)
        got = pads_frame(fp)
        n0 = next(iter(want))
        dx, dy = want[n0][0] - got[n0][0], want[n0][1] - got[n0][1]
        if all(math.hypot(got[n][0] + dx - x, got[n][1] + dy - y) < 0.01 for n, (x, y) in want.items()):
            fp.Move(V(dx, -dy))
            return rot
        board.Remove(fp)
        if fp.IsFlipped():
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    sys.exit(f"pcb: no turn on the {'rear' if bottom else 'front'} face puts {fp.GetReference()}'s pads "
             f"{', '.join(want)} where the module CAD does")


def fixed_pads(geo, lay, comps):
    """Every part the module CAD places, as (ref, {pad: (x, y)}, rear?, what): the pads'
    panel-frame places it implies. `check_cad` holds the same."""
    out = []
    for name, (x, y, ang, along) in geo["jacks"].items():
        # PJ398SM: pins 3, 2, 1 (T, TN, S) at `along` mm from the barrel in the direction `ang`
        refs = jack_refs(comps, lay, name)
        if len(refs) != 1:
            sys.exit(f"pcb: jacks: {name} - expected one J-CV whose tip is {lay['jacks'][name]}, found {refs or 'none'}")
        u = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        want = {pad: (x + d * u[0], y + d * u[1]) for pad, d in zip(("T", "TN", "S"), along)}
        out.append((refs[0], want, False, name))
    for name, (x, y, rot, dy, pitch) in geo["pots"].items():
        ref = pcb.ref_of(comps, name)
        want = {str(k + 1): (x + (k - 1) * pitch, y + dy) for k in range(3)}
        out.append((ref, want, False, name))
    for name, spec in (lay.get("connectors") or {}).items():
        c = geo["connectors"][name]
        ref = pcb.ref_of(comps, spec.get("row", name))
        x, y = c[0], c[1]
        if name == "J-B2B-MOD":
            # long axis along y, pin 1 at the top left, odd pins the left column
            rows, n, p = int(c[3]), int(c[4]), c[5]
            want = {str(2 * k + 1 + j): (x + (j - 0.5) * p, y + ((n - 1) / 2 - k) * p) for k in range(n) for j in range(rows)}
        elif name == "J-PWR-EURO":
            # long axis along y, pin 1 at the bottom; layout.yaml says which column is odd
            p, n, s = 2.54, 8, spec["odd_column"]
            want = {str(2 * k + 1 + j): (x + s * (0.5 - j) * p, y - ((n - 1) / 2 - k) * p) for k in range(n) for j in range(2)}
        elif name == "J-LED-PANEL":
            p = c[4]
            want = {"1": (x - p / 2, y), "2": (x + p / 2, y)}
        elif name == "J-UMBILICAL":
            # the footprint's origin is the connector's axis (its description); pads at
            # their footprint places, unturned, latch up
            fp = pcb.load_fp(comps[ref]["footprint"])
            want = {q.GetNumber(): (x + pcbnew.ToMM(q.GetPosition().x), y - pcbnew.ToMM(q.GetPosition().y))
                    for q in fp.Pads() if q.GetNumber() in ("1", "2", "8")}
        else:
            sys.exit(f"pcb: connectors: {name} - no rule for placing it")
        out.append((ref, want, spec.get("side") == "rear", name))
    for name, spec in (lay.get("cad_tall") or {}).items():
        # U-ISO: its pins at config/module.yaml iso.pins from iso.at, on the rear face
        ref = pcb.ref_of(comps, spec["row"])
        cfg = yaml.safe_load(open(os.path.join(ROOT, "config", "module.yaml")))
        at = next((t[1], t[2]) for t in geo["tall"] if t[0] == name)
        pins = cfg["iso"]["pins"]["value"]
        want = {n: (at[0] + dx, at[1] + dy) for n, (dx, dy) in zip(spec["pins"], pins)}
        out.append((ref, want, True, name))
    return out


def jack_refs(comps, lay, name):
    """The jack a CAD name is: layout.yaml jacks: maps each to its tip's net."""
    net = lay["jacks"][name].lstrip("/")
    return [r for r, c in comps.items() if c["row"] == "J-CV" and _net_of(comps, r, "T") == net]


_NETS = {}


def _net_of(comps, ref, pad):
    return _NETS.get((ref, pad))


def silk_off_others(board, gap):
    """A footprint's own silkscreen strokes that come nearer ANOTHER part's pad opening
    than the board house's silk-to-pad limit, or overlap another part's silk on the same
    face, removed and named: on a board this dense a connector's outline reaches over the
    parts beside it (pcb.fit_footprint_silk tests each footprint against its own pads)."""
    from shapely.strtree import STRtree
    faces = {pcbnew.F_SilkS: (pcbnew.F_Cu, pcbnew.F_Mask), pcbnew.B_SilkS: (pcbnew.B_Cu, pcbnew.B_Mask)}
    gone = {}
    for sl, (cu, mask) in faces.items():
        pads = [(f.GetReference(), pcb.item_shape(p, mask, p.GetSolderMaskExpansion(mask)))
                for f in board.GetFootprints() for p in f.Pads() if p.IsOnLayer(cu) or p.HasHole()]
        silk = [(f.GetReference(), it, pcb.item_shape(it, sl)) for f in board.GetFootprints()
                for it in f.GraphicalItems() if it.GetLayer() == sl and isinstance(it, pcbnew.PCB_SHAPE)]
        ptree = STRtree([g for _, g in pads])
        stree = STRtree([g for _, _, g in silk])
        for ref, it, g in silk:
            near = [pads[i][0] for i in ptree.query(g.buffer(gap)) if pads[i][0] != ref and g.distance(pads[i][1]) < gap]
            near += [silk[i][0] for i in stree.query(g.buffer(gap)) if silk[i][0] != ref and g.distance(silk[i][2]) < gap]
            if near:
                it.GetParentFootprint().Remove(it)
                gone.setdefault(ref, set()).update(near)
    for ref, by in sorted(gone.items()):
        print(f"pcb: silk adapted - {ref}: library silk near {', '.join(sorted(by))} removed")


def body_to_rear(fp):
    """A part placed on the front face for its PIN MAP whose BODY is on the rear (the
    jack board's J-B2B-MOD: its insulator is on the main board's side): its courtyard,
    fab and silk drawn on the rear layers, unmirrored, so the courtyard tests see the
    body where it is - not on the front among the jacks, where only its pins are."""
    swap = {pcbnew.F_CrtYd: pcbnew.B_CrtYd, pcbnew.F_Fab: pcbnew.B_Fab, pcbnew.F_SilkS: pcbnew.B_SilkS}
    for it in fp.GraphicalItems():
        if it.GetLayer() in swap:
            it.SetLayer(swap[it.GetLayer()])
            if hasattr(it, "SetMirrored"):
                it.SetMirrored(True)            # text on a rear layer reads from the rear
    fp.BuildCourtyardCaches()


def mount_holes(board, lay, geo):
    """The standoffs' pads: on the main board board-only footprints on NO net (metal
    standoffs, power-entry.md Grounding), on the jack board the sheet's own H1/H2 (on
    AGND_MOD), placed. Each with its head's keep-out: no other copper and no part."""
    m = lay["mounts"]
    placed = []
    for i, (name, x, y, hole, head) in enumerate(geo["standoffs"], 1):
        if m.get("on_sheet"):
            continue
        h = pcb.load_fp(m["footprint"])
        h.SetReference(f"H{i}")
        h.SetValue(name)
        h.SetBoardOnly(True)
        h.SetExcludedFromBOM(True)
        h.SetExcludedFromPosFiles(True)
        h.Reference().SetLayer(pcbnew.F_Fab)
        pcb.place(board, h, *to_pcb(x, y), 0, False)
        placed.append(h)
    return placed


# ------------------------------------------------------------------ building the board

def build(bdir, lay):
    name = os.path.basename(bdir)
    geo = geometry(lay["cluster"])
    comps, nets = pcb.sheet_netlist(os.path.join(bdir, name + ".kicad_sch"))
    _NETS.clear()
    _NETS.update({(r, p): n.lstrip("/") for n, nodes in nets for r, p in nodes})
    skip = lay.get("not_on_board") or {}
    for ref in skip:
        if ref not in comps:
            sys.exit(f"pcb: not_on_board: {ref} is not on the sheets")
    board = pcb.new_board(bdir, lay, {"thickness": geo["thickness"]})
    segs = outline_segments(lay, geo)
    pcb.add_outline(board, segs)
    outline = pcb_main.board_polygon(segs)
    netinfo, fps = pcb.load_parts(board, comps, nets, skip)
    placed = set()
    for ref, want, rear, what in fixed_pads(geo, lay, comps):
        place_by_pads(board, fps[ref], want, rear)
        placed.add(ref)
    for name, spec in (lay.get("connectors") or {}).items():
        if spec.get("body") == "rear":
            body_to_rear(fps[pcb.ref_of(comps, spec.get("row", name))])
    if lay["mounts"].get("on_sheet"):
        for i, (nm, x, y, hole, head) in enumerate(geo["standoffs"]):
            ref = lay["mounts"]["on_sheet"][i]
            pcb.place(board, fps[ref], *to_pcb(x, y), 0, False)
            placed.add(ref)
    else:
        mount_holes(board, lay, geo)
    for ref, v in (lay.get("parts") or {}).items():
        if ref not in fps:
            sys.exit(f"pcb: parts: {ref} is not a part on this board's sheets")
        if ref in placed:
            sys.exit(f"pcb: parts: {ref} is placed by the module CAD - take it out of parts:")
        x, y, r = v[:3]
        pcb.place(board, fps[ref], *to_pcb(x, y), r, len(v) > 3 and v[3] == "rear")
        placed.add(ref)
    missing = sorted(set(fps) - placed)
    if missing and not lay.get("_partial"):
        sys.exit(f"pcb: not placed (add them to layout.yaml parts): {', '.join(missing)}")
    for ref in missing:
        board.Remove(fps[ref])          # _partial: a placement study (not a layout)
    keepouts(board, lay, geo)
    if lay.get("fab"):
        silk_off_others(board, float(lay["fab"]["silk_to_pad"]))
    # planes, islands (pcb_main's, the same schema)
    isl = pcb_main.island_polys(lay)
    for pl in lay.get("planes") or []:
        region = outline
        for spec, p, moat in isl:
            if spec["layer"] == pl["layer"]:
                region = region.difference(moat)
        for cut in pl.get("cut") or []:
            region = region.difference(Polygon(cut))
        pcb_main.copper_zone(board, pl["net"], pl["layer"], region, 0, pl.get("name", pl["net"]))
    for spec, p, moat in isl:
        pcb_main.copper_zone(board, spec["net"], spec["layer"], p.intersection(outline), 1, spec["net"] + " island")
    for gd in lay.get("guards") or []:
        # a guard: copper at a node's own potential round a high-impedance node, on the
        # faces named, filled round the node's pads and track with the clearance - here
        # the LT3042's SET, at OUT's potential (power-entry.md, The DAC rail, Layout)
        for L in gd["layers"]:
            pcb_main.copper_zone(board, gd["net"], L, Polygon(gd["outline"]).intersection(outline), 3, gd["net"] + " guard")
    for po in lay.get("pours") or []:
        # an outer-layer pour over a region (the isolated return on the rear face)
        region = outline if po["outline"] == "board" else Polygon(po["outline"]).intersection(outline)
        pcb_main.copper_zone(board, po["net"], po["layer"], region, 2, po["net"] + " pour")
    return board, fps, netinfo, lay, comps, outline


def outline_segments(lay, geo):
    """The DXF's segments less each standoff's hole (its footprint drills it)."""
    segs = pcb.dxf_segments(os.path.join(ROOT, "mechanical", "module", "export", lay["outline"]))
    keep = []
    for a, b in segs:
        if any(math.hypot(a[0] - s[1], a[1] - s[2]) < s[3] / 2 + 0.3 and math.hypot(b[0] - s[1], b[1] - s[2]) < s[3] / 2 + 0.3
               for s in geo["standoffs"]):
            continue
        keep.append((a, b))
    return keep


def keepouts(board, lay, geo):
    """The CAD's keep-outs as KiCad rule areas: a jack's barrel (no copper, both faces);
    a standoff's head (no part, and no copper but its own pad, both faces); layout.yaml
    keepouts: (each a polygon with its reason) as given."""
    LAY = ["F.Cu", "B.Cu"] if int(lay.get("layers", 2)) == 2 else ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
    for name, rest in geo["keepouts"]:
        if name.startswith("barrel"):
            pcb_main.rule_area(board, Point(rest[0], rest[1]).buffer(rest[2] / 2, 32), name, LAY)
        elif name == "standoff head":
            # the mount's own pad stands in it. On no net (the main board) a rule area keeps
            # every track, via and pour off. On a net (the jack board's AGND_MOD) its own
            # net's pour must meet it, and a rule area cannot tell nets apart (nor exempt the
            # mount's own footprint): its courtyard keeps parts off, and check_cad holds
            # every other net's copper off the head
            if not lay["mounts"].get("net"):
                pcb_main.rule_area(board, Point(rest[0], rest[1]).buffer(rest[2] / 2, 32), name, LAY)
    for k in lay.get("keepouts") or []:
        pcb_main.rule_area(board, Polygon(k["outline"]), k["name"], k.get("layers", LAY),
                           footprints=k.get("footprints", False), copper=k.get("copper", True))


# ------------------------------------------------------------------ checking

def check_cad(board, lay, comps):
    """The module CAD still agrees with the board: thickness, outline, every part it
    places where it puts it (pad by pad, on its face), the standoffs' pads and the
    copper kept off their heads, and nothing taller than its room on either face."""
    bad = []
    geo = geometry(lay["cluster"])
    cfg = yaml.safe_load(open(os.path.join(ROOT, "config", "module.yaml")))
    t_cfg = float(cfg["boards"]["t"]["value"])
    t_pcb = pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())
    if abs(geo.get("thickness", -1) - t_cfg) > 1e-6:
        bad.append(f"error: [cad] pcb-geometry.echo says the board is {geo.get('thickness')} mm, config/module.yaml boards.t {t_cfg:g} - run: python3 tools/cad.py build")
    if abs(t_pcb - t_cfg) > 1e-6:
        bad.append(f"error: [cad] the board is {t_pcb:g} mm thick, the module CAD's {t_cfg:g} (boards.t)")
    ce = float(cfg["boards"]["copper_edge"]["value"])
    if float(lay["rules"]["edge_clearance"]) + 1e-6 < ce:
        bad.append(f"error: [cad] layout.yaml rules.edge_clearance {lay['rules']['edge_clearance']} is under the module CAD's "
                   f"copper-to-edge {ce:g} (config/module.yaml boards.copper_edge)")
    ol = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(ol):
        bad.append("error: [cad] the Edge.Cuts outline is not closed")
    else:
        from shapely.geometry import MultiLineString
        cad = MultiLineString([(to_pcb(*a), to_pcb(*b)) for a, b in outline_segments(lay, geo)])
        off = pcb.shapely_of(ol).boundary.hausdorff_distance(cad)
        if off > 0.05:
            bad.append(f"error: [cad] the Edge.Cuts outline is up to {off:.2f} mm from the module CAD's (mechanical/module/export/{lay['outline']})")
    fp_of = {f.GetReference(): f for f in board.GetFootprints()}
    _NETS.clear()
    _NETS.update({(f.GetReference(), p.GetNumber()): p.GetNetname().lstrip("/") for f in board.GetFootprints() for p in f.Pads()})
    for ref, want, rear, what in fixed_pads(geo, lay, comps):
        fp = fp_of.get(ref)
        if fp is None:
            bad.append(f"error: [cad] {what} ({ref}) is not on the board")
            continue
        got = pads_frame(fp)
        off = max(math.hypot(got[n][0] - x, got[n][1] - y) for n, (x, y) in want.items())
        if off > 0.05 or fp.IsFlipped() != rear:
            bad.append(f"error: [cad] {what} ({ref}): its pads are up to {off:.2f} mm from where the module CAD puts them"
                       f"{'' if fp.IsFlipped() == rear else ', on the wrong face'} ({'rear' if rear else 'front'}, "
                       f"pad {next(iter(want))} at {tuple(round(v, 2) for v in next(iter(want.values())))})")
    for i, (name, x, y, hole, head) in enumerate(geo["standoffs"], 1):
        ref = lay["mounts"]["on_sheet"][i - 1] if lay["mounts"].get("on_sheet") else f"H{i}"
        fp = fp_of.get(ref)
        got = None if fp is None else to_body(*xy_mm(fp.GetPosition()))
        if got is None or math.hypot(got[0] - x, got[1] - y) > 0.05:
            bad.append(f"error: [cad] {name}'s pad {ref} is at {got}; the module CAD puts it at ({x}, {y})")
            continue
        net = lay["mounts"].get("net")
        for p in fp.Pads():
            if p.GetDrillSize().x and abs(pcbnew.ToMM(p.GetDrillSize().x) - hole) > 0.01:
                bad.append(f"error: [cad] {ref}'s hole is {pcbnew.ToMM(p.GetDrillSize().x):g} mm; the module CAD's is {hole:g}")
            if (p.GetNetname().lstrip("/") or None) != net:
                bad.append(f"error: [cad] {ref}'s pad is on '{p.GetNetname()}', not {net or 'no net'} (power-entry.md Grounding)")
        disc = Point(*to_pcb(x, y)).buffer(head / 2 + float(lay["rules"]["clearance"]) - 0.02)
        for L in range(board.GetCopperLayerCount()):
            lid = pcbnew.F_Cu if L == 0 else (pcbnew.B_Cu if L == board.GetCopperLayerCount() - 1 else pcbnew.In1_Cu + (L - 1) * 2)
            hits = pcb_main.copper_near(board, disc, lid, net and ("/" + net if board.FindNet("/" + net) else net), ref)
            if hits:
                bad.append(f"error: [cad] {', '.join(hits)} under {name}'s head ({ref}) on {board.GetLayerName(lid)} - "
                           "the metal standoff bears there")
    bad += check_heights(board, lay, geo)
    bad += check_isolation(board, lay)
    return bad


def check_isolation(board, lay):
    """U-ISO's barrier (ADR 0027): on every copper layer, the converter's input side (the
    nets layout.yaml isolation: input names) and its output side (output:) keep `gap`
    apart - pads, tracks, vias and poured copper alike. The one part that bridges it by
    design (C-ISO-Y, `bridge:`) is left out, with the copper within `gap` of its body."""
    spec = lay.get("isolation")
    if not spec:
        return []
    gap = float(spec["gap"])
    norm = lambda n: n.lstrip("/").split("/")[-1]
    ins, outs = set(spec["input"]), set(spec["output"])
    skip = unary_union([pcb.shapely_of(f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)).buffer(gap)
                        for f in board.GetFootprints() if f.GetReference() in (spec.get("bridge") or [])]) \
        if spec.get("bridge") else None
    bad = []
    for lid in board.GetEnabledLayers().CuStack():
        side = {"in": [], "out": []}
        for t in board.GetTracks():
            n = norm(t.GetNetname())
            if t.IsOnLayer(lid) and (n in ins or n in outs):
                side["in" if n in ins else "out"].append(pcb.item_shape(t, lid))
        for f in board.GetFootprints():
            for q in f.Pads():
                n = norm(q.GetNetname())
                if q.IsOnLayer(lid) and (n in ins or n in outs) and f.GetReference() not in (spec.get("bridge") or []):
                    side["in" if n in ins else "out"].append(pcb.item_shape(q, lid))
        for z in board.Zones():
            n = norm(z.GetNetname())
            if not z.GetIsRuleArea() and z.IsOnLayer(lid) and (n in ins or n in outs) and z.GetFilledPolysList(lid).OutlineCount():
                side["in" if n in ins else "out"].append(pcb.shapely_of(z.GetFilledPolysList(lid)))
        if not side["in"] or not side["out"]:
            continue
        a, b = unary_union(side["in"]), unary_union(side["out"])
        if skip is not None:
            a, b = a.difference(skip), b.difference(skip)
        d = a.distance(b) if not (a.is_empty or b.is_empty) else 1e9
        if d + 1e-4 < gap:
            from shapely.ops import nearest_points
            pa, pb = nearest_points(a, b)
            bad.append(f"error: [isolation] on {board.GetLayerName(lid)} U-ISO's input and output sides come {d:.2f} mm apart at "
                       f"({pa.x:.2f}, {pa.y:.2f})-({pb.x:.2f}, {pb.y:.2f}); layout.yaml isolation: gap is {gap:g}")
    return bad


def check_heights(board, lay, geo):
    """Every part inside its height room on its face (layout.yaml heights:, by footprint
    name, each with its source): the module CAD's rooms (keep-outs with a height) on the
    face they name; the rest of a face is layout.yaml rooms: front/rear."""
    bad = []
    heights = lay.get("heights") or {}
    rooms = []
    for name, rest in geo["keepouts"]:
        face = "front" if name.startswith("front") else ("rear" if name.startswith("rear") else None)
        if face and len(rest) >= 5 and all(isinstance(v, (int, float)) for v in rest[:5]):
            rooms.append((face, box(*rest[:4]), rest[4], name))
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if fp.IsBoardOnly():
            continue
        fname = fp.GetFPID().GetLibItemName().wx_str()
        h = next((v for key, v in heights.items() if key in fname), None)
        if h is None:
            bad.append(f"error: [height] {ref} ({fname}) has no height in layout.yaml heights:")
            continue
        face = "rear" if fp.IsFlipped() else "front"
        cy = pcb_main.courtyard_body(fp)
        if cy.is_empty:
            continue
        room, where = (lay.get("rooms") or {}).get(face, 1e9), f"the {face} face"
        for f, rect, r, nm in rooms:
            if f == face and cy.intersects(rect) and cy.intersection(rect).area > 1e-3 and r < room:
                room, where = r, nm
        if h > room + 1e-6:
            bad.append(f"error: [height] {ref} stands {h:g} mm on the {face}; its room ({where}) is {room:g}")
    return bad


def check_b2b(board, bdir, lay):
    """J-B2B-MOD is one header soldered through both boards (A7-3): pin k is one straight
    conductor, so on this board and on the other each pad k must stand at the same
    panel-frame place, and carry the same net. Both boards place it on their TOP face,
    unmirrored; one placed on the rear lands every net one column over. Checked against
    the module CAD (fixed_pads, in check_cad) and here against the other board's
    .kicad_pcb, where it exists."""
    spec = lay.get("b2b") or {}
    if not spec:
        return []
    bad = []
    me = board.FindFootprintByReference(pcb.ref_of(pcb.sheet_netlist(os.path.join(bdir, os.path.basename(bdir) + ".kicad_sch"))[0], "J-B2B-MOD"))
    other = os.path.join(ROOT, spec["other"])
    path = os.path.join(other, os.path.basename(other) + ".kicad_pcb")
    if me.IsFlipped():
        bad.append(f"error: [b2b] J-B2B-MOD ({me.GetReference()}) is on the rear face: it mirrors, and every net lands one column over")
    if not os.path.exists(path):
        return bad + [f"note: [b2b] {os.path.relpath(path, ROOT)} not laid out yet - checked against the module CAD only"]
    ob = pcbnew.LoadBoard(path)
    ocomps, _ = pcb.sheet_netlist(os.path.join(other, os.path.basename(other) + ".kicad_sch"))
    them = ob.FindFootprintByReference(pcb.ref_of(ocomps, "J-B2B-MOD"))
    a = {p.GetNumber(): (to_body(*xy_mm(p.GetPosition())), p.GetNetname().lstrip("/")) for p in me.Pads()}
    b = {p.GetNumber(): (to_body(*xy_mm(p.GetPosition())), p.GetNetname().lstrip("/")) for p in them.Pads()}
    if set(a) != set(b):
        return bad + [f"error: [b2b] the two boards' J-B2B-MOD have different pads: {sorted(set(a) ^ set(b))}"]
    for n in sorted(a, key=int):
        (pa, na), (pb, nb) = a[n], b[n]
        if math.hypot(pa[0] - pb[0], pa[1] - pb[1]) > 0.01:
            bad.append(f"error: [b2b] pin {n} is at ({pa[0]:.2f}, {pa[1]:.2f}) here and ({pb[0]:.2f}, {pb[1]:.2f}) on {os.path.basename(other)} - the pins do not mate")
        if na != nb and not (na.startswith("unconnected") and nb.startswith("unconnected")):
            bad.append(f"error: [b2b] pin {n} is {na or 'no net'} here and {nb or 'no net'} on {os.path.basename(other)}")
    return bad
