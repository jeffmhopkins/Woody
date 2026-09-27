#!/usr/bin/env python3
"""A board's first PCB: placed from the body CAD and the KiCad sheets, routed, checked.

    python3 tools/pcb.py layout hardware/boards/key-board-lh   # write <board>.kicad_pcb (refuses if it exists; --force)
    python3 tools/pcb.py check  hardware/boards/key-board-lh   # DRC + schematic parity + CAD agreement
    python3 tools/pcb.py render hardware/boards/key-board-lh   # 3D top/bottom and 2D copper PNGs

WHERE THINGS COME FROM - nothing on this board is typed in by hand twice:

  the netlist, footprints, references   the board's KiCad sheets (ADR 0019), via kicad-cli
  the board outline                     mechanical/export/key-board-<lh|rh>.dxf (the body CAD)
  switch and ribbon-connector places    mechanical/export/pcb-geometry.echo (the body CAD)
  everything else's place               layout.yaml beside the board: the underside parts,
                                        each beside what it serves, and the routing rules

`layout` writes the PCB ONCE. From then on the .kicad_pcb is the source, like
the sheets: open it in KiCad 9, move and re-route by hand. `check` is what
keeps it honest whoever edits it: KiCad's DRC with schematic parity (every
footprint and net agrees with the sheets), zero unrouted connections, and
every switch and the ribbon connector still where the body CAD puts them.

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
    geo = {"switches": {}, "ffc": None, "standoffs": []}
    for line in open(os.path.join(ROOT, "mechanical", "export", "pcb-geometry.echo")):
        m = re.match(r'ECHO: "PCB", "(\w+)", "(\w+)", (.*)', line)
        if not m or m.group(1) != cluster:
            continue
        kind, rest = m.group(2), [t.strip().strip('"') for t in m.group(3).split(",")]
        if kind == "switch":
            geo["switches"][rest[0]] = (float(rest[1]), float(rest[2]), float(rest[3]))
        elif kind == "ffc":
            geo["ffc"] = tuple(float(v) for v in rest[1:6])
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
        comps[ref] = {"value": find(c, "value")[0][1], "footprint": fp[0][1] if fp else "",
                      "path": sp + (tst[0][1] if tst else "")}
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
    ds.SetBoardThickness(MM(geo.get("thickness", 1.6)))
    ds.m_TrackMinWidth = MM(rules["track_min"])
    ds.m_MinClearance = MM(rules["clearance"])
    ds.m_ViasMinSize = MM(rules["via_min"])
    ds.m_MinThroughDrill = MM(rules["drill_min"])
    ds.m_CopperEdgeClearance = MM(rules["edge_clearance"])
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


def place(board, fp, x, y, rot, bottom):
    board.Add(fp)
    fp.SetPosition(V(x, y))
    if bottom:
        fp.Flip(V(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot)


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
    # the ribbon connector: bottom side, its cable entry at the board edge the CAD's ribbon leaves by
    fx, fy, _, fl, fw = geo["ffc"]
    edge_y = to_pcb(0, fy + fw / 2)[1]          # the far edge of the CAD envelope, in pcb y
    j = lay["connector"]
    place(board, fps["J-CHAIN"], to_pcb(fx, 0)[0], edge_y + j["origin_from_edge"], j["rot"], True)
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
    for ref, (x, y, r) in lay["parts"].items():
        px, py = to_pcb(x, y)
        place(board, fps[ref], px, py, r, True)
        placed.add(ref)
    missing = sorted(set(fps) - placed)
    if missing:
        sys.exit(f"pcb: not placed (add them to layout.yaml parts): {', '.join(missing)}")
    return board, fps, netinfo, lay


def save(board, path):
    board.BuildConnectivity()
    pcbnew.SaveBoard(path, board)


def cmd_layout(bdir, force=False):
    name = os.path.basename(bdir)
    out = os.path.join(bdir, name + ".kicad_pcb")
    if os.path.exists(out) and not force:
        sys.exit(f"pcb: {os.path.relpath(out, ROOT)} exists and is the source now; --force overwrites it")
    board, fps, netinfo, lay = build(bdir)
    if lay.get("route", True):
        import pcb_route
        failed = pcb_route.route(board, lay)
        if failed:
            print(f"pcb: could not route {', '.join(failed)} - move parts in layout.yaml and re-run")
    save(board, out)
    if lay.get("route", True):
        # zones are filled in a fresh process: an in-process fill of a just-built board crashes
        subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {os.path.dirname(os.path.abspath(__file__))!r}); "
                        f"import pcb_route; pcb_route.fill_zones({out!r})"], check=True)
    print(f"pcb: wrote {os.path.relpath(out, ROOT)}")


def drc(pcb):
    import json
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "drc.json")
        subprocess.run(["kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all",
                        "--format", "json", "-o", out, pcb], capture_output=True, text=True, env=kicad_env())
        return json.load(open(out))


def cmd_check(bdir):
    name = os.path.basename(bdir)
    pcb = os.path.join(bdir, name + ".kicad_pcb")
    d = drc(pcb)
    bad = []
    for v in d.get("violations", []):
        bad.append(f"{v['severity']}: [{v['type']}] {v['description']} - " + "; ".join(i["description"] for i in v.get("items", [])))
    for v in d.get("unconnected_items", []):
        bad.append(f"error: [unconnected] " + "; ".join(i["description"] for i in v.get("items", [])))
    for v in d.get("schematic_parity", []):
        bad.append(f"error: [parity] {v['description']} - " + "; ".join(i["description"] for i in v.get("items", [])))
    # the body CAD still agrees: switches and connector where it says
    lay = yaml.safe_load(open(os.path.join(bdir, "layout.yaml")))
    geo = cad_geometry(lay["cluster"])
    board = pcbnew.LoadBoard(pcb)
    for key, (x, y, r) in geo["switches"].items():
        fp = board.FindFootprintByReference(f"SW-{key}")
        px, py = to_pcb(x, y)
        got = (pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y))
        if math.hypot(got[0] - px, got[1] - py) > 0.05:
            bad.append(f"error: [cad] SW-{key} is at {got}, the body CAD puts it at ({px:.2f}, {py:.2f})")
    for i, (x, y, *_) in enumerate(geo["standoffs"], 1):
        fp = board.FindFootprintByReference(f"H{i}")
        px, py = to_pcb(x, y)
        got = None if fp is None else (pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y))
        if got is None or math.hypot(got[0] - px, got[1] - py) > 0.05:
            bad.append(f"error: [cad] standoff hole H{i} is at {got}, the body CAD puts it at ({px:.2f}, {py:.2f})")
    errs = [b for b in bad if b.startswith("error")]
    print(f"pcb: {os.path.relpath(pcb, ROOT)}: {len(errs)} error(s), {len(bad) - len(errs)} warning(s)")
    for b in bad:
        print("  " + b)
    return 1 if errs else 0


def cmd_render(bdir):
    """3D views of both sides, 2D copper plots, and the fabrication outputs - all recorded
    in hardware/SHEETS.csv against the .kicad_pcb, so tools/kicad.py check reports them
    stale when the board moves."""
    import shutil
    import kicad
    name = os.path.basename(bdir)
    pcb = os.path.join(bdir, name + ".kicad_pcb")
    env = kicad_env()
    outs = []
    for side, rot in (("top", "-35,0,20"), ("bottom", "35,0,-20")):
        o = os.path.join(bdir, f"{name}.pcb-3d-{side}.png")
        subprocess.run(["kicad-cli", "pcb", "render", "--side", side, "--width", "1800", "--height", "1000",
                        "--quality", "high", "--perspective", "--rotate", rot, "-o", o, pcb],
                       capture_output=True, text=True, env=env, check=True)
        outs.append(o)
    with tempfile.TemporaryDirectory() as t:
        for layers, tag, mirror in (("F.Cu,Edge.Cuts", "copper-top", False), ("B.Cu,Edge.Cuts,B.Fab", "copper-bottom", True)):
            svg = os.path.join(t, tag + ".svg")
            args = ["kicad-cli", "pcb", "export", "svg", "--layers", layers, "--page-size-mode", "2",
                    "--exclude-drawing-sheet", "-o", svg, pcb]
            if mirror:
                args.insert(4, "--mirror")
            subprocess.run(args, capture_output=True, text=True, env=env, check=True)
            o = os.path.join(bdir, f"{name}.pcb-{tag}.png")
            subprocess.run(["rsvg-convert", "-z", "7", "-b", "white", "-o", o, svg], check=True)
            outs.append(o)
    # fabrication: Gerbers, drill, pick-and-place, as a board house takes them
    fab = os.path.join(bdir, "fab")
    shutil.rmtree(fab, ignore_errors=True)
    os.makedirs(fab)
    subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "--no-protel-ext", "--layers", "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts", "-o", fab + "/", pcb],
                   capture_output=True, text=True, env=env, check=True)
    subprocess.run(["kicad-cli", "pcb", "export", "drill", "--format", "excellon", "-o", fab + "/", pcb],
                   capture_output=True, text=True, env=env, check=True)
    subprocess.run(["kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
                    "-o", os.path.join(fab, name + "-pos.csv"), pcb], capture_output=True, text=True, env=env, check=True)
    fabfiles = sorted(os.path.join(fab, f) for f in os.listdir(fab))
    kicad.ledger_set(bdir, outs + fabfiles, [pcb], kind="pcb")
    for o in outs:
        print(f"pcb: rendered {os.path.relpath(o, ROOT)}")
    print(f"pcb: {len(fabfiles)} fabrication file(s) in {os.path.relpath(fab, ROOT)}/")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] in ("layout", "check", "render"):
        d = os.path.join(ROOT, sys.argv[2].rstrip("/"))
        sys.exit({"layout": lambda: cmd_layout(d, "--force" in sys.argv), "check": lambda: cmd_check(d),
                  "render": lambda: cmd_render(d)}[sys.argv[1]]() or 0)
    print(__doc__)
    sys.exit(2)
