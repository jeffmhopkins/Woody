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

CELLS = ["squeeze", "middle", "fan", "around"]


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
