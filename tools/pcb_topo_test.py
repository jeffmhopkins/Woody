#!/usr/bin/env python3
"""The topological router's bench (ADR 0029, #47): constructed boards, each a case the grid
router handles badly or not at all, each held to KiCad's DRC (zero errors, zero
unconnected) and pcb.py check's acid traps, as pcb_route2_test holds the grid router.

    python3 tools/pcb_topo_test.py [cell ...] [--plot DIR]
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CELLS = ["squeeze", "middle", "fan", "around", "cross", "grid", "scramble", "triad", "channel", "tree",
         "stagemix", "stacked", "stage4", "island4", "crowd",
         "widths", "clear", "layercost", "guard", "part", "mixed"]


def _setup():
    import pcbnew
    import pcb_route2 as R2
    import pcb_testboards as T
    import pcb_topo as TP
    import pcb_route2_test as B
    return pcbnew, R2, T, TP, B


class _Runs:
    def __init__(self, runs):
        self.runs = runs


def _route(b, lay, order, layer=0):
    """Route two-pad nets `order` (in that order) on one layer; lay and return everything."""
    _, R2, _, TP, _ = _setup()
    m = R2.model_from_board(b, lay)
    pairs = [(n, *m.pads_of(n)) for n in order]
    runs, failed, mp = TP.route_layer(m, layer, pairs)
    bad = {r.net: R2.fits(r, m)[:2] for r in runs if R2.fits(r, m)}
    for r in runs:
        R2.lay(r, m)
    return m, runs, failed, bad, mp


def _result(name, b, m, runs, failed, bad, out, plot):
    _, _, _, _, B = _setup()
    res = B.finish(name, b, m, _Runs(runs), out, plot)
    res.update(failed=failed, unfit={k: [x[0] for x in v] for k, v in bad.items()},
               length=round(sum(r.length() for r in runs), 1))
    res["pass"] = not failed and B.clean(res)
    return res


def _front(*nets):
    _, _, _, _, B = _setup()
    return dict(B.LAY, net_classes={"front": {"nets": list(nets), "layers": ["F.Cu"]}})


def cell_squeeze(out, plot):
    """Two lanes, two nets. A first, down the channel's middle; B squeezes in beside it -
    A's line moves over by the geometry, with no push and no rip-up."""
    _, _, T, _, _ = _setup()
    b = T.new_board(60.0, 16.0)
    for ys in ((0.0, 6.6), (7.8, 16.0)):
        T.keepout(b, 15.0, ys[0], 45.0, ys[1], layers=("F", "B"))
    T.tp(b, "A1", "A", 10.0, 7.2)
    T.tp(b, "A2", "A", 50.0, 7.2)
    T.tp(b, "B1", "B", 4.0, 3.0)
    T.tp(b, "B2", "B", 56.0, 13.0)
    m, runs, failed, bad, _ = _route(b, _front("A", "B"), ["A", "B"])
    return _result("squeeze", b, m, runs, failed, bad, out, plot)


def cell_middle(out, plot):
    """Three lanes, three nets; the MIDDLE one routed last. It takes the place between the
    two already there - merging between traces - and they part for it."""
    _, _, T, _, _ = _setup()
    b = T.new_board(60.0, 18.0)
    gap = 1.75                       # three tracks at 0.25 + 0.2, and their clearance to the walls
    y0, y1 = 9.0 - gap / 2, 9.0 + gap / 2
    T.keepout(b, 15.0, 0.0, 45.0, y0, layers=("F", "B"))
    T.keepout(b, 15.0, y1, 45.0, 18.0, layers=("F", "B"))
    for n, ya, yb in (("U", 3.0, 3.0), ("D", 15.0, 15.0), ("M", 9.0, 9.0)):
        T.tp(b, n + "1", n, 4.0, ya)
        T.tp(b, n + "2", n, 56.0, yb)
    m, runs, failed, bad, _ = _route(b, _front("U", "D", "M"), ["U", "D", "M"])
    return _result("middle", b, m, runs, failed, bad, out, plot)


def cell_fan(out, plot):
    """A 2 x 5, 1.27 mm header fanned out on one layer to ten pads in a row, in the order its
    pins stand: the lines leave between the pads and spread - the escape the main board's
    J-MCU needs."""
    _, _, T, _, _ = _setup()
    b = T.new_board(40.0, 30.0)
    nets = [f"N{k}" for k in range(10)]
    T.header(b, "J1", nets, 20.0, 8.0)
    # the pads' order round the header: column x -1.95 rows 0..4 (pins 1, 3, ..), x +1.95
    # rows 0..4 (pins 2, 4, ..); the targets in the order that keeps the fan planar: left
    # column top to bottom then round to the right column bottom to top
    left = [nets[k] for k in range(0, 10, 2)]
    right = [nets[k] for k in range(1, 10, 2)]
    ring = left + right[::-1]
    for i, n in enumerate(ring):
        T.tp(b, f"T{i}", n, 4.0 + i * 3.5, 25.0, w=1.2, h=1.2)
    m, runs, failed, bad, _ = _route(b, _front(*nets), ring)
    return _result("fan", b, m, runs, failed, bad, out, plot)


def cell_around(out, plot):
    """A block of pads between a net's two ends: the line goes round it, held off each
    corner by its clearance (the chord between two bends must not cut a corner)."""
    _, _, T, _, _ = _setup()
    b = T.new_board(40.0, 24.0)
    k = 0
    for i in range(4):
        for j in range(3):
            T.tp(b, f"X{k}", f"X{k}", 16.0 + i * 2.5, 9.5 + j * 2.5, w=1.4, h=1.4)
            k += 1
    T.tp(b, "S1", "S", 4.0, 12.0)
    T.tp(b, "S2", "S", 36.0, 12.0)
    T.tp(b, "R1", "R", 4.0, 14.0)
    T.tp(b, "R2", "R", 36.0, 10.0)
    m, runs, failed, bad, _ = _route(b, _front("S", "R"), ["S", "R"])
    return _result("around", b, m, runs, failed, bad, out, plot)


def _board2(b, nets):
    """Route `nets` on both layers (T2) and lay them. Returns (model, runs, failed, bad, rep)."""
    _, R2, _, TP, B = _setup()
    m = R2.model_from_board(b, B.LAY)
    runs, failed, rep = TP.route_board(m, nets)
    bad = {}
    for r in runs:
        f = R2.fits(r, m)
        if f:
            bad[r.net] = f[:2]
        R2.lay(r, m)
    return m, runs, failed, bad, rep


def _result2(name, b, m, runs, failed, bad, rep, out, plot):
    res = _result(name, b, m, runs, failed, bad, out, plot)
    res.update(vias=sum(len(r.vias()) for r in runs), split=rep["split"], rounds=len(rep["log"]))
    return res


def cell_cross(out, plot):
    """Two front pads' nets whose straight lines cross: one goes to the back by a via
    beside each of its pads."""
    _, _, T, _, _ = _setup()
    b = T.new_board(30.0, 20.0)
    T.tp(b, "A1", "A", 4.0, 4.0)
    T.tp(b, "A2", "A", 26.0, 16.0)
    T.tp(b, "B1", "B", 4.0, 16.0)
    T.tp(b, "B2", "B", 26.0, 4.0)
    m, runs, failed, bad, rep = _board2(b, ["A", "B"])
    res = _result2("cross", b, m, runs, failed, bad, rep, out, plot)
    res["pass"] = res["pass"] and res["vias"] == 2
    return res


def cell_grid(out, plot):
    """Four nets across and four down, every across net crossing every down one: across on
    one layer, down on the other, a via at each pad on the wrong side."""
    _, _, T, _, _ = _setup()
    b = T.new_board(40.0, 40.0)
    for i in range(4):
        y = 10.0 + i * 6.0
        T.tp(b, f"H{i}a", f"H{i}", 4.0, y)
        T.tp(b, f"H{i}b", f"H{i}", 36.0, y)
        x = 10.0 + i * 6.0
        T.tp(b, f"V{i}a", f"V{i}", x, 4.0)
        T.tp(b, f"V{i}b", f"V{i}", x, 36.0)
    nets = [f"H{i}" for i in range(4)] + [f"V{i}" for i in range(4)]
    m, runs, failed, bad, rep = _board2(b, nets)
    return _result2("grid", b, m, runs, failed, bad, rep, out, plot)


def cell_scramble(out, plot):
    """A through-hole 2 x 5 header (2.54 mm) whose ten lines go to a row of pads in the
    REVERSE of the order they leave in - no single layer takes them; both layers do, the
    header's pins being on both."""
    pcbnew, _, T, _, _ = _setup()
    b = T.new_board(40.0, 34.0)
    fp = T._fp(b, "J1", "HDR-2x5-2.54")
    nets = [f"S{k}" for k in range(10)]
    for k, n in enumerate(nets):
        T._tht(b, fp, k + 1, (-1.27 if k % 2 == 0 else 1.27), ((k // 2) - 2) * 2.54, 1.7, 1.0, n)
    T._court_rect(fp, 5.2, 13.0)
    T._place(b, fp, 20.0, 9.0)
    left = [nets[k] for k in range(0, 10, 2)]
    right = [nets[k] for k in range(1, 10, 2)]
    ring = (left + right[::-1])[::-1]
    for i, n in enumerate(ring):
        T.tp(b, f"T{i}", n, 4.0 + i * 3.5, 29.0, w=1.2, h=1.2)
    m, runs, failed, bad, rep = _board2(b, nets)
    return _result2("scramble", b, m, runs, failed, bad, rep, out, plot)


def cell_triad(out, plot):
    """Three nets each crossing both others: two layers cannot part all three pairs, so one
    goes round or changes layer partway. It must route, legally."""
    _, _, T, _, _ = _setup()
    b = T.new_board(40.0, 40.0)
    import math
    for k, n in enumerate(("P", "Q", "W")):
        a = math.radians(90 + 120 * k)
        T.tp(b, f"{n}1", n, 20.0 + 14 * math.cos(a), 20.0 + 14 * math.sin(a))
        T.tp(b, f"{n}2", n, 20.0 - 14 * math.cos(a + 0.35), 20.0 - 14 * math.sin(a + 0.35))
    m, runs, failed, bad, rep = _board2(b, ["P", "Q", "W"])
    return _result2("triad", b, m, runs, failed, bad, rep, out, plot)


def cell_channel(out, plot):
    """The grid router's push board (pcb_testboards.channel): A, and CLK of three pads,
    through a channel two tracks wide. The grid router needed a shove; here CLK's tree takes
    the lane beside A in the plan."""
    _, _, T, _, _ = _setup()
    b = T.channel()
    _, R2, _, TP, B = _setup()
    lay = dict(B.LAY, net_classes={"front": {"nets": ["A", "CLK"], "layers": ["F.Cu"]}})
    m = R2.model_from_board(b, lay)
    runs, failed, rep = TP.route_board(m, ["A", "CLK"])
    bad = {}
    for r in runs:
        f = R2.fits(r, m)
        if f:
            bad[r.net] = f[:2]
        R2.lay(r, m)
    return _result2("channel", b, m, runs, failed, bad, rep, out, plot)


def cell_tree(out, plot):
    """A five-pad clock (a source and four loads round the board) and four two-pad data
    lines across its branches: the trees, the layers and the vias together."""
    _, _, T, _, _ = _setup()
    b = T.new_board(40.0, 40.0)
    T.tp(b, "C0", "CLK", 20.0, 20.0)
    for k, (x, y) in enumerate(((6.0, 6.0), (34.0, 6.0), (6.0, 34.0), (34.0, 34.0))):
        T.tp(b, f"C{k + 1}", "CLK", x, y)
    for k, (a, c) in enumerate((((4.0, 14.0), (36.0, 14.0)), ((4.0, 26.0), (36.0, 26.0)),
                                ((14.0, 4.0), (14.0, 36.0)), ((26.0, 4.0), (26.0, 36.0)))):
        T.tp(b, f"D{k}a", f"D{k}", *a)
        T.tp(b, f"D{k}b", f"D{k}", *c)
    m, runs, failed, bad, rep = _board2(b, ["CLK", "D0", "D1", "D2", "D3"])
    return _result2("tree", b, m, runs, failed, bad, rep, out, plot)


def _stage(name, b, lay, fams, out, plot, ground=None):
    """Route `fams` through Router.stage (T4) and judge the board as the grid router's
    stage cells are judged."""
    _, R2, _, _, B = _setup()
    m = R2.model_from_board(b, lay)
    r = R2.Router(m, flow=0.3)
    rep = r.stage(fams, board=b, ground=ground)
    res = B.finish(name, b, m, r, out, plot, pour=ground, written=True)
    res.update(families=[(x["family"], x["nets"], x["runs"], x["failed"], x["vias"]) for x in rep],
               topo_log=[l_ for l_ in r.log if "topo" in l_][:4])
    res["pass"] = B.clean(res) and not any(x["failed"] for x in rep)
    return res, m, r, rep


def cell_stagemix(out, plot):
    """The grid router's stages board (minikey): the rail by the grid router, the keys by
    the topological planner, in one Router.stage - the rail's copper locked under the keys."""
    _, R2, T, _, B = _setup()
    import pcb_pack as P
    b = T.minikey()
    bd = P.board_of(b)
    pk = P.Packer(bd, ["SW1", "SW2", "SW3", "J1", "H1", "H2", "H3", "H4"])
    pk.pack("U1", ["C6", "R11"])
    pk.pack("J1", ["C7"])
    pk.pattern(["SW1", "SW2", "SW3"], {f"SW{k}": list(T.MINIKEY["keys"][k]) for k in (1, 2, 3)})
    pk.apply(b)
    lay = dict(B.LAY, power_nets=["V3V3"])
    fams = [{"name": "rail", "nets": ["V3V3"]}, {"name": "keys", "nets": ["KEY*", "SWL*", "FREE"], "engine": "topo"},
            {"name": "rest", "nets": ["*"], "engine": "topo"}]
    res, *_ = _stage("stagemix", b, lay, fams, out, plot, ground="GND")
    return res


def cell_stacked(out, plot):
    """Two topo families, the second planned against the first's LOCKED copper: across, then
    down - the grid board in two stages."""
    _, _, T, _, B = _setup()
    b = T.new_board(40.0, 40.0)
    for i in range(4):
        y = 10.0 + i * 6.0
        T.tp(b, f"H{i}a", f"H{i}", 4.0, y)
        T.tp(b, f"H{i}b", f"H{i}", 36.0, y)
        x = 10.0 + i * 6.0
        T.tp(b, f"V{i}a", f"V{i}", x, 4.0)
        T.tp(b, f"V{i}b", f"V{i}", x, 36.0)
    fams = [{"name": "across", "nets": ["H*"], "engine": "topo"}, {"name": "down", "nets": ["V*"], "engine": "topo"}]
    res, *_ = _stage("stacked", b, B.LAY, fams, out, plot)
    return res


def cell_stage4(out, plot):
    """The four-layer board: GND and POS planes, their fanout vias laid first; the signals by
    the topological planner on the outer layers, round the fanout."""
    _, R2, T, _, B = _setup()
    b, lay = T.four_layer(False)
    res, m, r, rep = _stage("stage4", b, lay, [{"name": "sig", "nets": ["S*"], "engine": "topo"}], out, plot)
    p = os.path.join(out, "stage4.kicad_pcb")
    bad, on_plane, vias = B._four_checks(R2, b, lay, p)
    res.update(check_planes=bad[:5], tracks_on_plane_layers=on_plane)
    res["pass"] = res["pass"] and not bad and not on_plane
    return res


def cell_island4(out, plot):
    """The four-layer board with an AGND island, its moat and its tie: the island's nets and
    the rest by the topological planner, kept off the moat."""
    _, R2, T, _, B = _setup()
    b, lay = T.four_layer(True)
    fams = [{"name": "sig", "nets": ["S*", "SIG_A", "AIN", "A3V3"], "engine": "topo"}]
    res, m, r, rep = _stage("island4", b, lay, fams, out, plot)
    p = os.path.join(out, "island4.kicad_pcb")
    bad, on_plane, vias = B._four_checks(R2, b, lay, p)
    res.update(check_planes=bad[:5], tracks_on_plane_layers=on_plane)
    res["pass"] = res["pass"] and not bad and not on_plane
    return res


def crowd_board():
    """The main board's J-MCU crowd, small: a 2 x 10, 1.27 mm through-hole header (J1) with
    a 14-pin driver (U6) and a 6-pin protection array (U1) beside it, series and pull
    resistors, and the far ends at the board's edges - the nets that walled each other in
    on eight grid-router runs (2026-10-11), as the real one has them: header pin to IC pin
    to resistor, three pads a net."""
    pcbnew, _, T, _, _ = _setup()
    W, H = 64.0, 44.0
    # four layers as the main board has them: GND the plane on In1.Cu, V3 on In2.Cu, each
    # pin of theirs down to it by a fanout via; the signals on the two outer layers
    b = T.new_board(W, H, layers=4)
    rect = [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, H - 0.3), (0.3, H - 0.3)]
    T.zone(b, "GND", pcbnew.In1_Cu, rect)
    T.zone(b, "V3", pcbnew.In2_Cu, rect)
    fp = T._fp(b, "J1", "HDR-2x10-1.27")
    pins = {}
    for k in range(20):
        col, row = k // 2, k % 2
        x, y = -5.715 + col * 1.27, (-0.635 if row == 0 else 0.635)
        pins[k + 1] = (x, y)
    net_of = {4: "IO1", 5: "IO2", 6: "IO7", 8: "IO38", 10: "IO35", 12: "IO36", 14: "IO34", 16: "TXD",
              18: "IO37", 19: "IO6", 2: "GND", 20: "GND"}
    for k, (x, y) in pins.items():
        T._tht(b, fp, k, x, y, 0.85, 0.5, net_of.get(k, ""))
    T._court_rect(fp, 13.6, 3.0)
    T._place(b, fp, 36.0, 37.0)
    # U6 - the LED and MIDI driver: IO1 in, IO2 in, outputs to the edge
    T.soic(b, "U6", ["GND", "IO1", "GATE", "GND", "IO6", "MTIP", "GND", "MRING", "IO2", "GND", "", "GND", "GND", ""],
           24.0, 18.0)
    # U1 - the protection array on IO35, IO36, IO34
    T.soic(b, "U1", ["IO35", "GND", "IO36", "IO34", "", ""], 30.0, 29.0)
    # series and pull resistors
    T.passive(b, "R10", "IO1", "GND", 18.0, 10.0)
    T.passive(b, "R49", "V3", "IO2", 14.0, 14.0)
    T.passive(b, "R48", "V3", "IO6", 30.0, 10.0)
    T.passive(b, "R11", "GATE", "LEDDI", 33.0, 14.0)
    T.passive(b, "R35", "IO7", "SHLD", 16.0, 30.0)
    T.passive(b, "R34", "IO38", "SCK", 12.0, 34.0)
    T.passive(b, "R1", "IO35", "SCLK", 54.0, 24.0, rot=90.0)
    T.passive(b, "R2", "IO36", "MOSI", 57.0, 24.0, rot=90.0)
    # the far ends, at the edges
    for ref, n, x, y in (("TP1", "SHLD", 3.0, 30.0), ("TP2", "SCK", 3.0, 36.0), ("TP3", "SCLK", 54.0, 4.0),
                         ("TP4", "MOSI", 58.0, 4.0), ("TP5", "LEDDI", 44.0, 4.0), ("TP6", "MTIP", 3.0, 18.0),
                         ("TP7", "MRING", 3.0, 22.0), ("TP8", "IO37", 61.0, 30.0), ("TP9", "TXD", 61.0, 36.0),
                         ("TP10", "IO34", 61.0, 16.0), ("TP11", "IO35", 3.0, 8.0), ("TP12", "IO36", 8.0, 4.0)):
        T.tp(b, ref, n, x, y)
    return b


def cell_crowd(out, plot):
    """THE GATE before the main board (#47 T4b): the J-MCU crowd, small, one topo family on
    two layers. Every net routes; DRC clean."""
    _, _, _, _, B = _setup()
    b = crowd_board()
    nets = ["IO1", "IO2", "IO6", "IO7", "IO38", "IO35", "IO36", "IO34", "TXD", "IO37", "GATE", "LEDDI", "MTIP",
            "MRING", "SHLD", "SCK", "SCLK", "MOSI"]
    lay = dict(B.LAY, planes=[{"layer": "In1.Cu", "net": "GND"}, {"layer": "In2.Cu", "net": "V3"}], fanout=["GND", "V3"])
    fams = [{"name": "crowd", "nets": nets, "engine": "topo"}]
    res, m, r, rep = _stage("crowd", b, lay, fams, out, plot)
    p_ = os.path.join(out, "crowd.kicad_pcb")
    bad, on_plane, _ = B._four_checks(*_setup()[1:2], b, lay, p_)
    res.update(check_planes=bad[:5], tracks_on_plane_layers=on_plane)
    res["pass"] = res["pass"] and not bad and not on_plane
    res["pushed"] = [p[0] for x in rep for p in x["pushed"]]
    res["topo_log"] = [l_ for l_ in r.log if l_.startswith("topo")]
    res["pass"] = res["pass"] and not res["pushed"]
    return res


# ------------------------------------------------------------------ T6: per-net and per-part rules

def _copper(b, net=None, other=False):
    """Shapely copper of `net` (or of every net but it, with other=True), per KiCad layer."""
    import pcbnew
    from shapely.geometry import LineString, Point
    from shapely.ops import unary_union
    mm = pcbnew.ToMM
    out = {}
    def want(n):
        return (n != net) if other else (n == net)
    for t in b.GetTracks():
        if not want(t.GetNetname()) or not t.GetNetname():
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            g = Point(mm(t.GetPosition().x), mm(t.GetPosition().y)).buffer(mm(t.GetWidth(pcbnew.F_Cu)) / 2)
            for L in (pcbnew.F_Cu, pcbnew.B_Cu):
                out.setdefault(L, []).append(g)
        else:
            g = LineString([(mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y))]).buffer(mm(t.GetWidth()) / 2)
            out.setdefault(t.GetLayer(), []).append(g)
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if not want(pad.GetNetname()) or not pad.GetNetname():
                continue
            for L in (pcbnew.F_Cu, pcbnew.B_Cu):
                if pad.IsOnLayer(L):
                    from pcb_route2 import _poly_of
                    out.setdefault(L, []).append(_poly_of(pad.GetEffectivePolygon(L)))
    return {L: unary_union(gs) for L, gs in out.items()}


def _gap(b, net, others=None):
    """The least distance on any layer between `net`'s copper and every other net's (or the
    copper of the nets in `others`)."""
    mine = _copper(b, net)
    if others is None:
        theirs = _copper(b, net, other=True)
    else:
        from shapely.ops import unary_union
        parts = [_copper(b, n) for n in others]
        theirs = {}
        for d in parts:
            for L, g in d.items():
                theirs[L] = unary_union([theirs[L], g]) if L in theirs else g
    return min((mine[L].distance(theirs[L]) for L in mine if L in theirs), default=99.0)


def Point_far():
    from shapely.geometry import Point
    return Point(1e6, 1e6)


def _t6_board(w=40.0, h=24.0):
    _, _, T, _, _ = _setup()
    return T.new_board(w, h)


def cell_widths(out, plot):
    """A 0.6 mm rail and three 0.25 mm signals through one channel: each at its own class's
    width, the rail's room counted at its own pitch (not the family's widest)."""
    pcbnew, R2, T, _, B = _setup()
    b = _t6_board(50.0, 20.0)
    T.keepout(b, 15.0, 0.0, 35.0, 6.4, layers=("F", "B"))
    T.keepout(b, 15.0, 10.4, 35.0, 20.0, layers=("F", "B"))
    T.tp(b, "P1", "PWR", 4.0, 8.4, w=1.5, h=1.5)
    T.tp(b, "P2", "PWR", 46.0, 8.4, w=1.5, h=1.5)
    for k, y in enumerate((3.0, 14.0, 17.0)):
        T.tp(b, f"S{k}a", f"S{k}", 4.0, y)
        T.tp(b, f"S{k}b", f"S{k}", 46.0, y)
    lay = dict(B.LAY, net_classes={"rail": {"nets": ["PWR"], "track": 0.6}})
    res, m, r, rep = _stage("widths", b, lay, [{"name": "all", "nets": ["PWR", "S*"], "engine": "topo"}], out, plot)
    ws = sorted({round(pcbnew.ToMM(t.GetWidth()), 2) for t in b.GetTracks() if t.GetNetname() == "PWR"
                 and not isinstance(t, pcbnew.PCB_VIA)})
    res["pwr_widths"] = ws
    res["pass"] = res["pass"] and ws == [0.6]
    return res


def cell_clear(out, plot):
    """A class with 0.5 mm clearance (a high-voltage node) among 0.2 mm signals: every other
    net's copper kept 0.5 off it - measured on the board, KiCad's DRC knowing only 0.2."""
    _, R2, T, _, B = _setup()
    b = _t6_board()
    T.tp(b, "H1", "HV", 4.0, 12.0)
    T.tp(b, "H2", "HV", 36.0, 12.0)
    for k, (a, c) in enumerate((((4.0, 6.0), (36.0, 18.0)), ((4.0, 18.0), (36.0, 6.0)), ((20.0, 2.0), (20.0, 22.0)))):
        T.tp(b, f"S{k}a", f"S{k}", *a)
        T.tp(b, f"S{k}b", f"S{k}", *c)
    lay = dict(B.LAY, net_classes={"hv": {"nets": ["HV"], "clearance": 0.5}})
    res, m, r, rep = _stage("clear", b, lay, [{"name": "all", "nets": ["HV", "S*"], "engine": "topo"}], out, plot)
    g = round(_gap(b, "HV"), 3)
    res["hv_gap"] = g
    res["pass"] = res["pass"] and g >= 0.5 - 0.005
    return res


def cell_layercost(out, plot):
    """Two nets that must cross; A's class makes B.Cu twenty times dearer: A stays on the
    front, the other goes under it."""
    pcbnew, R2, T, _, B = _setup()
    b = _t6_board(30.0, 20.0)
    T.tp(b, "A1", "A", 4.0, 4.0)
    T.tp(b, "A2", "A", 26.0, 16.0)
    T.tp(b, "C1", "C", 4.0, 16.0)
    T.tp(b, "C2", "C", 26.0, 4.0)
    lay = dict(B.LAY, net_classes={"front": {"nets": ["A"], "layer_cost": {"B.Cu": 20.0}}})
    res, m, r, rep = _stage("layercost", b, lay, [{"name": "all", "nets": ["A", "C"], "engine": "topo"}], out, plot)
    back = sum(pcbnew.ToMM(t.GetLength()) for t in b.GetTracks() if t.GetNetname() == "A"
               and not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() == pcbnew.B_Cu)
    res["a_on_back_mm"] = round(back, 2)
    res["pass"] = res["pass"] and back < 0.01
    return res


def cell_guard(out, plot):
    """A locked pair with a 0.55 mm guard (layout.yaml pairs:, as the breath sensor's): every
    other net's copper kept the clearance plus the guard off its legs."""
    pcbnew, R2, T, _, B = _setup()
    b = _t6_board(40.0, 24.0)
    for n, y in (("PA", 11.6), ("PB", 12.6)):
        T.tp(b, f"{n}1", n, 4.0, y, w=0.6, h=0.6)
        T.tp(b, f"{n}2", n, 36.0, y, w=0.6, h=0.6)
    T.track(b, "PA", [(4.0, 11.6), (36.0, 11.6)], w=0.25, locked=True)
    T.track(b, "PB", [(4.0, 12.6), (36.0, 12.6)], w=0.25, locked=True)
    for k, (ya, yb) in enumerate(((4.0, 20.0), (20.0, 4.0))):
        T.tp(b, f"S{k}a", f"S{k}", 10.0 + k * 20.0, ya)
        T.tp(b, f"S{k}b", f"S{k}", 10.0 + k * 20.0, yb)
    lay = dict(B.LAY, pairs=[{"nets": ["PA", "PB"], "layer": "F.Cu", "width": 0.25, "gap": 0.75, "guard": 0.55}])
    res, m, r, rep = _stage("guard", b, lay, [{"name": "all", "nets": ["S*"], "engine": "topo"}], out, plot)
    # to the pair's LEGS (its locked tracks), on its layer: the guard is round the legs
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    legs = unary_union([LineString([(pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)),
                                    (pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y))]).buffer(pcbnew.ToMM(t.GetWidth()) / 2)
                        for t in b.GetTracks() if t.GetNetname() in ("PA", "PB") and t.GetLayer() == pcbnew.F_Cu
                        and not isinstance(t, pcbnew.PCB_VIA)])
    gF = min(_copper(b, n).get(pcbnew.F_Cu, Point_far()).distance(legs) for n in ("S0", "S1"))
    res["gap_to_pair"] = round(gF, 3)
    # the guard is on the pair's layer for tracks, everywhere for vias (pcb.py check_pair_guard)
    res["pass"] = res["pass"] and gF >= 0.2 + 0.55 - 0.005
    return res


def cell_part(out, plot):
    """part_clearance: {U1: 0.6} - every other net's copper 0.2 + 0.6 off U1's pads, while
    U1's own nets reach them."""
    pcbnew, R2, T, _, B = _setup()
    b = _t6_board(40.0, 24.0)
    T.soic(b, "U1", ["N1", "N2", "", "", "", "", "", ""], 20.0, 12.0)
    T.tp(b, "T1", "N1", 4.0, 4.0)
    T.tp(b, "T2", "N2", 4.0, 20.0)
    for k, (xa, xb) in enumerate(((14.0, 26.0), (26.0, 14.0))):
        T.tp(b, f"S{k}a", f"S{k}", xa, 2.0)
        T.tp(b, f"S{k}b", f"S{k}", xb, 22.0)
    lay = dict(B.LAY, part_clearance={"U1": 0.6})
    res, m, r, rep = _stage("part", b, lay, [{"name": "all", "nets": ["N1", "N2", "S*"], "engine": "topo"}], out, plot)
    u1 = {}
    for fp in b.GetFootprints():
        if fp.GetReference() == "U1":
            from pcb_route2 import _poly_of
            from shapely.ops import unary_union
            u1 = unary_union([_poly_of(p.GetEffectivePolygon(pcbnew.F_Cu)) for p in fp.Pads()])
    # on U1's own layer: its pads are SMD, and a track may pass under it on the back
    d = min(_copper(b, n).get(pcbnew.F_Cu, Point_far()).distance(u1) for n in ("S0", "S1"))
    res["gap_to_U1"] = round(d, 3)
    res["pass"] = res["pass"] and d >= 0.2 + 0.6 - 0.005
    return res


def cell_mixed(out, plot):
    """The crowd board with the rules at once: a 0.4 mm rail class on the LED line, a 0.4 mm
    clearance class on the MIDI drive, B.Cu dear for the SPI pair, and 0.4 mm more round U1
    (the protection array)."""
    _, R2, _, _, B = _setup()
    b = crowd_board()
    nets = ["IO1", "IO2", "IO6", "IO7", "IO38", "IO35", "IO36", "IO34", "TXD", "IO37", "GATE", "LEDDI", "MTIP",
            "MRING", "SHLD", "SCK", "SCLK", "MOSI"]
    lay = dict(B.LAY, planes=[{"layer": "In1.Cu", "net": "GND"}, {"layer": "In2.Cu", "net": "V3"}], fanout=["GND", "V3"],
               net_classes={"led": {"nets": ["LEDDI", "GATE"], "track": 0.4},
                            "midi": {"nets": ["MTIP", "MRING"], "clearance": 0.4},
                            "spi": {"nets": ["SCLK", "MOSI"], "layer_cost": {"B.Cu": 6.0}}},
               part_clearance={"U1": 0.4})
    res, m, r, rep = _stage("mixed", b, lay, [{"name": "crowd", "nets": nets, "engine": "topo"}], out, plot)
    gm = min(_gap(b, n) for n in ("MTIP", "MRING"))
    res["midi_gap"] = round(gm, 3)
    res["pass"] = res["pass"] and gm >= 0.4 - 0.005
    return res


def run_cell(name, out, plot):
    import time
    t0 = time.monotonic()
    res = globals()[f"cell_{name}"](out, plot)
    res["seconds"] = round(time.monotonic() - t0, 1)
    return res


def main():
    args = sys.argv[1:]
    plot = None
    if "--plot" in args:
        i = args.index("--plot")
        plot = os.path.abspath(args[i + 1])
        os.makedirs(plot, exist_ok=True)
        del args[i:i + 2]
    if args and args[0] == "--cell":
        print("RESULT " + json.dumps(run_cell(args[1], args[2], plot), default=str))
        return 0
    out = tempfile.mkdtemp(prefix="topo-bench-")
    ok = True
    for c in args or CELLS:
        cmd = [sys.executable, os.path.abspath(__file__), "--cell", c, out] + (["--plot", plot] if plot else [])
        p = subprocess.run(cmd, capture_output=True, text=True)
        line = [l for l in p.stdout.splitlines() if l.startswith("RESULT ")]
        if p.returncode or not line:
            print(f"{c:10s} FAIL (crashed)\n{p.stderr[-1500:]}")
            ok = False
            continue
        res = json.loads(line[-1][7:])
        passed = res.pop("pass")
        ok &= passed
        print(f"{c:10s} {'PASS' if passed else 'FAIL'}  {json.dumps(res, default=str)}")
    print(f"boards in {out}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
