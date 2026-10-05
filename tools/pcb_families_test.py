"""The families stage (tools/pcb_route.py route_families, issue #41) on a constructed
board - built in memory, written nowhere but a scratch directory, never a board under
hardware/.

    python3 tools/pcb_families_test.py            # the three cases; exit 1 on a failure
    python3 tools/pcb_families_test.py --plot DIR # ...and each result's 2D plot there
    python3 tools/pcb_families_test.py --identity hardware/boards/module-jack [--rev HEAD]

--identity: on a scratch copy of a routed board with its unlocked routing taken up, the
connections KiCad then counts missing are routed twice, each in its own process with
KiCad's UUID generator seeded alike - once by complete() as it stands at --rev
(default HEAD), once by route_families() as it stands in the working tree - and the
two saved .kicad_pcb files compared BYTE FOR BYTE. Without `families:` they must be
identical. The board under hardware/ is only read.

THE BOXING-IN CASE. A 60 x 20 mm board, one routed layer (both nets in a net class
with `layers: [F.Cu]`, so a via cannot settle it):
  LONG   (5, 10) -> (45, 10)    40 mm along the middle
  SHORT  (25, 1.2) -> (25, 18.8) 17.6 mm across it, its pads hard against both edges
SHORT can go round either end of LONG (there is room past both pads); LONG cannot go
round SHORT (its pads leave no room at either edge). complete's order - shortest
first - lays SHORT straight across and walls LONG in.
  1. no families:          the old order, complete() itself
  2. families: [LONG]       LONG first, then SHORT (rest) goes round
  3. families: [both]       one family: negotiation finds the same answer itself
"""
import argparse
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcbnew                    # noqa: E402
import pcb_route                 # noqa: E402

MM = pcbnew.FromMM
LAY = {"rules": {"track": 0.25, "track_min": 0.2, "clearance": 0.2, "via": 0.7, "via_drill": 0.3,
                 "edge_clearance": 0.3},
       "net_classes": {"one_layer": {"nets": ["LONG", "SHORT"], "track": 0.25, "layers": ["F.Cu"]}}}
PADS = {"LONG": [(5.0, 10.0), (45.0, 10.0)], "SHORT": [(25.0, 1.2), (25.0, 18.8)]}


def board():
    b = pcbnew.BOARD()
    w, h = 60.0, 20.0
    for (x0, y0), (x1, y1) in (((0, 0), (w, 0)), ((w, 0), (w, h)), ((w, h), (0, h)), ((0, h), (0, 0))):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0)))
        s.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        s.SetWidth(MM(0.1))
        b.Add(s)
    for k, (net, pts) in enumerate(PADS.items()):
        ni = pcbnew.NETINFO_ITEM(b, net)
        b.Add(ni)
        for m, (x, y) in enumerate(pts):
            fp = pcbnew.FOOTPRINT(b)
            fp.SetReference(f"TP{2 * k + m + 1}")
            b.Add(fp)
            pad = pcbnew.PAD(fp)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            pad.SetShape(pcbnew.PAD_SHAPE_RECT)
            pad.SetSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0)))
            ls = pcbnew.LSET()
            ls.AddLayer(pcbnew.F_Cu)
            pad.SetLayerSet(ls)
            pad.SetNumber("1")
            fp.Add(pad)
            fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
            pad.SetNet(ni)
    return b


def run(families, plot=None, tag=""):
    b = board()
    lay = dict(LAY, **({"families": families} if families else {}))
    conns = sorted(((n, *pts) for n, pts in PADS.items()), key=lambda m: pcb_route.math.dist(m[1], m[2]))
    rep = []
    failed = pcb_route.route_families(b, lay, conns, report=rep)
    length = sum(pcbnew.ToMM(t.GetLength()) for t in b.GetTracks() if type(t) is pcbnew.PCB_TRACK)
    if plot:
        p = os.path.join(tempfile.mkdtemp(prefix="families-"), "t.kicad_pcb")
        pcbnew.SaveBoard(p, b)
        import pcb_plot
        pcb_plot.plot(p, os.path.join(plot, f"families-test-{tag}.png"), nets=list(PADS), title=f"families test: {tag}")
    return sorted(m[0] for m in failed), length, rep


RUN = """
import json, sys
sys.path[:0] = {paths!r}
import pcbnew, yaml, pcb_route
lay = yaml.safe_load(open({layout!r}))
miss = [(n, tuple(a), tuple(b)) for n, a, b in json.load(open({miss!r}))]
board = pcbnew.LoadBoard({src!r})
pcbnew.KIID.SeedGenerator(41)
failed = pcb_route.{fn}(board, lay, miss)
pcbnew.SaveBoard({out!r}, board)
print("FAILED", len(failed))
"""


def identity(bdir, rev):
    """complete() at `rev` against route_families() now, on one board, byte for byte."""
    import hashlib
    import json
    import shutil
    import subprocess
    name = os.path.basename(os.path.normpath(bdir))
    t = tempfile.mkdtemp(prefix="families-identity-")
    for f in (name + ".kicad_pcb", name + ".kicad_pro", "fp-lib-table", "sym-lib-table"):
        if os.path.exists(os.path.join(bdir, f)):
            shutil.copy(os.path.join(bdir, f), t)
    old = os.path.join(t, "old")
    os.mkdir(old)
    root = os.path.dirname(HERE)
    with open(os.path.join(old, "pcb_route.py"), "w") as f:
        f.write(subprocess.run(["git", "-C", root, "show", f"{rev}:tools/pcb_route.py"], capture_output=True,
                               text=True, check=True).stdout)
    src = os.path.join(t, name + ".kicad_pcb")
    b = pcbnew.LoadBoard(src)
    gone = [x for x in b.GetTracks() if not x.IsLocked()]
    for x in gone:
        b.Delete(x)
    pcbnew.SaveBoard(src, b)
    pcb_route.fill_zones(src)
    import pcb
    miss = sorted(pcb.unconnected_of(src), key=lambda m: pcb_route.math.dist(m[1], m[2]))
    json.dump(miss, open(os.path.join(t, "miss.json"), "w"))
    print(f"identity: {name} - {len(gone)} unlocked track(s) and via(s) taken up, {len(miss)} connection(s) missing")
    outs = []
    for tag, paths, fn in (("old", [old, HERE], "complete"), ("new", [HERE], "route_families")):
        out = os.path.join(t, f"{tag}.kicad_pcb")
        code = RUN.format(paths=paths, layout=os.path.join(bdir, "layout.yaml"), miss=os.path.join(t, "miss.json"),
                          src=src, fn=fn, out=out)
        r = subprocess.run(["nice", "-n", "19", sys.executable, "-c", code], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"identity: the {tag} run failed:\n{r.stderr[-2000:]}")
        last = [ln for ln in r.stdout.splitlines() if ln.startswith("FAILED")][-1]
        data = open(out, "rb").read()
        outs.append(data)
        print(f"identity: {tag:<3} {fn:<14} {last.split()[1]} failed, {len(data)} bytes, "
              f"sha256 {hashlib.sha256(data).hexdigest()[:16]}")
    same = outs[0] == outs[1]
    print(f"identity: {'BYTE-IDENTICAL' if same else 'DIFFERENT'} ({t})")
    return same


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot")
    ap.add_argument("--identity")
    ap.add_argument("--rev", default="HEAD")
    a = ap.parse_args()
    if a.identity:
        return 0 if identity(a.identity, a.rev) else 1
    ok = True
    f1, l1, _ = run(None, a.plot, "old-order")
    print(f"1. no families (complete, shortest first): failed {f1 or 'none'}, {l1:.1f} mm of track")
    ok &= f1 == ["LONG"]
    f2, l2, r2 = run([{"name": "spine", "nets": ["LONG"]}], a.plot, "long-first")
    print(f"2. families: [spine: LONG], then rest:       failed {f2 or 'none'}, {l2:.1f} mm of track")
    ok &= not f2
    f3, l3, r3 = run([{"name": "both", "nets": ["LONG", "SHORT"]}], a.plot, "negotiated")
    print(f"3. families: [both] (negotiated):           failed {f3 or 'none'}, {l3:.1f} mm of track, "
          f"{r3[0]['negotiated']} negotiated in {r3[0]['rounds']} round(s)")
    ok &= not f3 and r3[0]["negotiated"] == 2
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
