"""The main board placed COLD and routed in FAMILIES by the new tools (issue #46): the cluster
packer (tools/pcb_pack.py) seats every part that is not fixed, the centreline router
(tools/pcb_route2.py, Router.stage) routes one family of nets at a time, each reviewed -
its detours routed again, the liquid pass over it - and locked before the next is let near
it. It READS main-board.kicad_pcb and WRITES main-board.cold.kicad_pcb beside it (and one
checkpoint per family, main-board.cold.<k>-<family>.kicad_pcb, in --out): a trial, not the
source.

    python3 hardware/boards/main-board/cold_trial.py [--place-only] [--out DIR] [--plot DIR]

FIXED (the owner, 2026-10-10: "Body CAD + analog block"): every part the body CAD places
(the switches, the mounts, the connectors, U-BREATH, the LED row and each LED's cap by
its rule, U-BUCK and the one part the regulator block lets in beside it) and the analog
block - every part on the AGND_INST island, its tie, and the breath pair's far ends with
their clamps, which the pair's locked copper reaches. Everything else starts unplaced and
is seated by pcb_pack's cold planner: one key network stamped at every switch, then each
IC round the placed part it shares most nets with, then the passives round theirs - under
the body CAD's height rooms, the iron room and the island rule.

COPPER: every unlocked track and via goes; a locked one stays only if every pad its copper
reaches is a fixed part's (the pair and its guards, the analog block's hand routes, the
fixed parts' plane vias). The zones stay, emptied for a refill.

FAMILIES (the pcb-routing skill's order): power and rails, the analog block's own nets,
the key chain, the keys, the SPI and the Matrix's lines, MIDI, then the rest. The plane
fanout comes first, as it always does.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import pcbnew       # noqa: E402
import yaml         # noqa: E402
from shapely.geometry import LineString, Point, Polygon, box   # noqa: E402
from shapely.strtree import STRtree                            # noqa: E402
import pcb          # noqa: E402
import pcb_main     # noqa: E402
import pcb_pack     # noqa: E402
import pcb_route2   # noqa: E402

SRC = os.path.join(HERE, "main-board.kicad_pcb")
OUT = os.path.join(HERE, "main-board.cold.kicad_pcb")

# the families, in order, each with why it is there (the pcb-routing skill, "The order")
FAMILIES = [
    # power and rails: the layer-limited power classes cannot hop a signal via, so they go
    # before anything can wall them in (layout.yaml route_first: says the same)
    {"name": "power", "nets": ["INST_5V_A", "BUCK_IN", "/power-entry-instrument/*", "UMBILICAL_POS12", "DEV_3V3",
                               "/V3V3_CHAIN_*"]},
    # the analog block's own nets, over their island (the pair is already laid and locked)
    {"name": "analog", "nets": ["/SENSOR_RAW", "/breath-adc/*", "/breath-excitation-reference/*", "REF_VIN", "VS",
                                "BREATH_SENSE", "AGND_SENSE", "*BREATH*"]},
    # the key chain: SCK, SH/LD and the hops run the board's length together
    {"name": "chain", "nets": ["/CHAIN_*", "/HOP_*"]},
    # each key's T into its register
    {"name": "keys", "nets": ["/KEY_*", "*/SWITCH_LEG"]},
    # the Matrix's lines from J-MCU: SPI, the LED data, the service UART
    {"name": "mcu", "nets": ["/IO*", "/SPI*", "*TXD*", "*RXD*", "/led-strip-drive/*", "/LED_*"]},
    {"name": "midi", "nets": ["*MIDI*"]},
]


def comps_of():
    comps, _ = pcb.sheet_netlist(os.path.join(HERE, "main-board.kicad_sch"))
    return comps


def to_pcb_poly(pts):
    return Polygon([pcb.to_pcb(x, y) for x, y in pts])


def fixed_parts(board, lay, comps):
    """The parts that stay where the source has them, each with why."""
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    why = {}
    rows = {r: comps.get(r, {}).get("row", r) for r in fps}
    for r in fps:
        if r.startswith(("SW", "H")):
            why[r] = "body CAD (switch / mount)"
    for r in ("J1", "J2", "J4", "J5", "J6", "J7"):
        why[r] = "body CAD (connector)"
    for r in fps:
        if rows[r] in ("D-LED", lay["led_caps"]["row"]):
            why[r] = "body CAD (LED row and each LED's cap by its rule, ADR 0028)"
        if rows[r] in [v["row"] for v in (lay.get("cad_parts") or {}).values()]:
            why[r] = "body CAD (cad_parts:)"
    for k in (lay.get("keepouts") or {}).values():
        for row in k.get("except_rows") or []:
            for r in fps:
                if rows[r] == row and r not in why:
                    why[r] = "the regulator block's own (keepouts: except_rows)"
    # the analog block: every part whose courtyard is on the In1 island, and its tie
    isl = next(i for i in lay["islands"] if i.get("layer") == "In1.Cu")
    ip = to_pcb_poly(isl["outline"]).buffer(0.3)
    for r, f in fps.items():
        cy = pcb_pack.courtyard_of(f, pcbnew)
        if r not in why and cy.intersection(ip).area > 0.5 * cy.area:
            why[r] = "analog block (on the AGND_INST island)"
    why[isl["tie"]] = "analog block (the island's tie)"
    # the breath pair's far ends, and the clamps on the nets past them
    for pr in lay.get("pairs") or []:
        for end in pr["to"]:
            ref = end.split(".")[0]
            why[ref] = "analog block (the breath pair's end)"
            other = {p.GetNetname() for p in fps[ref].Pads()} - set(pr["nets"])
            for r, f in fps.items():
                if r not in why and not r.startswith("J") and other & {p.GetNetname() for p in f.Pads()}:
                    why[r] = "analog block (a clamp on the breath pair's far side)"
    return why


def strip(board, fixed):
    """Every unlocked track and via goes; locked copper goes unless every pad it reaches
    belongs to a fixed part. Connectivity is per net and per layer, a via joining all."""
    tracks = list(board.GetTracks())
    gone = [t for t in tracks if not t.IsLocked()]
    locked = [t for t in tracks if t.IsLocked()]
    L = lambda v: pcbnew.ToMM(v)

    def shape(t):
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition()
            return Point(L(c.x), L(c.y)).buffer(L(t.GetWidth(pcbnew.F_Cu)) / 2), None
        a, b = t.GetStart(), t.GetEnd()
        return LineString([(L(a.x), L(a.y)), (L(b.x), L(b.y))]).buffer(L(t.GetWidth()) / 2), t.GetLayer()
    items = [(t, *shape(t)) for t in locked]
    pads = []
    for f in board.GetFootprints():
        for p in f.Pads():
            for lid in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
                if p.IsOnLayer(lid) and p.GetNetname():
                    pads.append((f.GetReference(), p.GetNetname(), lid, pcb_route2._poly_of(p.GetEffectivePolygon(lid))))
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    tree = STRtree([g for _, g, _ in items])
    for i, (t, g, lay_) in enumerate(items):
        for j in tree.query(g):
            j = int(j)
            if j <= i:
                continue
            u, gu, lu = items[j]
            if u.GetNetname() != t.GetNetname() or not g.intersects(gu):
                continue
            if lay_ is None or lu is None or lay_ == lu:
                parent[find(i)] = find(j)
    bad = set()
    for ref, net, lid, pg in pads:
        if ref in fixed:
            continue
        for j in tree.query(pg):
            t, g, lay_ = items[int(j)]
            if t.GetNetname() == net and (lay_ is None or lay_ == lid) and g.intersects(pg):
                bad.add(find(int(j)))
    lost = [t for i, (t, _, _) in enumerate(items) if find(i) in bad]
    gone += lost
    for t in gone:
        board.Delete(t)
    for z in board.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    return len(gone), len(locked) - len(lost)


def key_roles(board):
    """Each switch's network in role order - series R (its SWITCH_LEG), pull-up R, C - read
    off the nets (as the left key board's trial does)."""
    nets = {f.GetReference(): {p.GetNetname() for p in f.Pads()} for f in board.GetFootprints()}
    roles = {}
    for sw in sorted(r for r in nets if r.startswith("SW")):
        leg = next(n for n in nets[sw] if n.endswith("SWITCH_LEG"))
        series = next(r for r, ns in nets.items() if r != sw and leg in ns)
        key = next(n for n in nets[series] if n != leg)
        pull = next(r for r, ns in nets.items() if r.startswith("R") and key in ns and r != series)
        cap = next(r for r, ns in nets.items() if r.startswith("C") and key in ns)
        roles[sw] = [series, pull, cap]
    return roles


def place(board, lay, comps, fixed, log):
    geo = pcb_main.geometry()
    rails = [p["net"] for p in lay["planes"]] + [i["net"] for i in lay["islands"]] + ["DEV_3V3"]
    bd = pcb_pack.board_of(board, rails=rails)
    # the island rule on the In1 island only (the In2 strip is a return path, not a place)
    isl = next(i for i in lay["islands"] if i.get("layer") == "In1.Cu")
    bd.islands = {isl["net"]: to_pcb_poly(isl["outline"])}
    # the body CAD's height rooms (pcb_main.check_heights reads the same keep-outs)
    k = geo["keepouts"]
    rooms = []
    for name, v in k.items():
        if name != "elsewhere" and v[4] > 0:
            (x0, y0), (x1, y1) = pcb.to_pcb(v[0], v[1]), pcb.to_pcb(v[2], v[3])
            rooms.append((box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), v[4], name))
    bd.rooms, bd.room_default = rooms, k["elsewhere"][4]
    heights = lay.get("heights") or {}
    for r, p in bd.parts.items():
        name = p.item.GetFPID().GetLibItemName().wx_str()
        p.height = next((v for key, v in heights.items() if key in name), None)
    # the iron room round the hand-soldered pads
    rowref = {}
    for r in bd.parts:
        rowref.setdefault(comps.get(r, {}).get("row", r), []).append(r)
    for rule in (lay.get("iron_room") or {}).get("rules") or []:
        for row in rule["rows"]:
            for r in rowref.get(row, []):
                cop = bd.parts[r].copper.get("F")
                if cop is not None:
                    bd.iron.append((r, "F", cop.buffer(0.25), rule["min"]))
    bd.unplaced = {r for r in bd.parts if r not in fixed}
    body = sorted(fixed)
    pk = pcb_pack.Packer(bd, body, log)
    roles = key_roles(board)
    sheets = {r: comps.get(r, {}).get("sheet", "") for r in bd.parts}
    rep = pk.cold(sheets, patterns=[(list(roles), roles)])
    pk.apply(board)
    return rep, sorted(bd.unplaced), pk


def silk(board, lay, comps):
    gone = [d for d in board.GetDrawings() if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
    for d in gone:
        board.Delete(d)
    pcb.add_silk_generic(board, lay, comps)
    return len(gone)


def measure(path):
    b = pcbnew.LoadBoard(path)
    tr = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    errs, unc = pcb_route2.drc(path)
    return {"length_mm": round(sum(pcbnew.ToMM(t.GetLength()) for t in tr), 1),
            "vias": sum(1 for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)),
            "drc_errors": len(errs), "unconnected": unc}


def main():
    arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    out = os.path.abspath(arg("--out", HERE))
    plotdir = arg("--plot")
    os.makedirs(out, exist_ok=True)
    lay = yaml.safe_load(open(os.path.join(HERE, "layout.yaml")))
    comps = comps_of()
    board = pcbnew.LoadBoard(SRC)
    fixed = fixed_parts(board, lay, comps)
    n, kept = strip(board, fixed)
    print(f"cold: {len(fixed)} part(s) fixed, {len(board.GetFootprints()) - len(fixed)} to place; "
          f"{n} track(s) and via(s) stripped, {kept} locked kept")
    for r in sorted(fixed):
        print(f"cold:   fixed {r}: {fixed[r]}")
    log = []
    rep, left, pk = place(board, lay, comps, fixed, log)
    for what, refs, res in rep:
        print(f"cold: place {what}: {', '.join(refs)} - {res}")
    for line in log:
        print("cold: " + line)
    if left:
        raise SystemExit(f"cold: still unplaced: {left}")
    print(f"cold: silkscreen made again ({silk(board, lay, comps)} old drawing(s) cleared)")
    if "--place-only" in sys.argv:
        pcbnew.SaveBoard(OUT, board)
        errs, _ = pcb_route2.drc(OUT, fill=False)
        pe = [e[:3] for e in errs if e[0] in ("courtyards_overlap", "items_not_allowed")]
        print(f"cold: placed only - wrote {os.path.relpath(OUT, ROOT)}; KiCad placement findings: {pe or 'none'}")
        return 1 if pe else 0
    m = pcb_route2.model_from_board(board, lay)
    r = pcb_route2.Router(m, flow=0.3, budget=3_000_000)

    def checkpoint(k, name):
        return os.path.join(out, f"main-board.cold.{k}-{name}.kicad_pcb")

    def plot(k, name, nets, path):
        if not plotdir:
            return None
        import pcb_plot
        png = os.path.join(plotdir, f"cold-{k}-{name}.png")
        pcb_plot.plot(path, png, nets=nets, title=f"main board cold: family {k} {name}")
        return png
    rep = r.stage(FAMILIES, board=board, checkpoint=checkpoint, first=lay.get("route_first") or [], plot=plot)
    for line in r.log:
        print("cold: route " + line)
    for x in rep:
        print("cold: family " + json.dumps({k_: v for k_, v in x.items() if k_ != "liquid"}, default=str))
    failed = {n_: v for x in rep for n_, v in x["failed"].items()}
    import pcb_route
    pcbnew.SaveBoard(OUT, board)
    board = pcbnew.LoadBoard(OUT)
    pcb_route.tidy(board, lay)
    pcbnew.SaveBoard(OUT, board)
    code = (f"import sys, json, yaml; sys.path.insert(0, {os.path.join(ROOT, 'tools')!r}); import pcb_route2; "
            f"print('ORPH ' + json.dumps(pcb_route2.fix_plane_orphans({OUT!r}, yaml.safe_load(open({os.path.join(HERE, 'layout.yaml')!r})))))")
    t = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    orph = [json.loads(line[5:]) for line in t.stdout.splitlines() if line.startswith("ORPH ")]
    if not orph:
        raise SystemExit(f"cold: the plane orphan pass failed:\n{t.stderr[-2000:]}")
    print(f"cold: plane fragments fanned out again: {orph[0][0]}; still apart: {orph[0][1] or 'none'}")
    print(f"cold: wrote {os.path.relpath(OUT, ROOT)}; failed {failed or 'none'}")
    print(f"cold: source {measure(SRC)}")
    print(f"cold: trial  {measure(OUT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
