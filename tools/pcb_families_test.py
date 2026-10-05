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

THE FENCE CASE (#40: the tail trial's fallback re-routed chain lines 140 mm outside its
region). WALL, already routed and unlocked, runs from its pad at x 10 along the bottom
edge and up x 30 to its pad at the top edge: TARGET (25, 5) -> (40, 15) has no way past
it on its one layer, so the only way through is to take WALL up - and WALL has copper
outside the region x 20-60.
  4. no region, rip_up: 1  (control) WALL is taken up and TARGET routed
  5. region [20, 0, 60, 20]          TARGET fails, cleanly and at once; WALL untouched

THE LAYER-3 CHANNEL. A four-layer board; TARGET (10, 10) -> (50, 10) on the front, a
locked wall of another net across the front at x 30, and an In2.Cu keep-out over
x 25-35 but for a channel y 9-11. The family names [F.Cu, In2.Cu] and a region:
  6. it routes, through In2.Cu, inside the channel, nothing on In2 in the keep-out
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


def edge(b, w, h):
    for (x0, y0), (x1, y1) in (((0, 0), (w, 0)), ((w, 0), (w, h)), ((w, h), (0, h)), ((0, h), (0, 0))):
        s_ = pcbnew.PCB_SHAPE(b)
        s_.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s_.SetLayer(pcbnew.Edge_Cuts)
        s_.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0)))
        s_.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        s_.SetWidth(MM(0.1))
        b.Add(s_)


def pads(b, net, pts, ref0):
    ni = pcbnew.NETINFO_ITEM(b, net)
    b.Add(ni)
    for m, (x, y) in enumerate(pts):
        fp = pcbnew.FOOTPRINT(b)
        fp.SetReference(f"TP{ref0 + m}")
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
    return ni


def track(b, ni, pts, layer=pcbnew.F_Cu, locked=False, w=0.25):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0)))
        t.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        t.SetWidth(MM(w))
        t.SetLayer(layer)
        t.SetNet(ni)
        t.SetLocked(locked)
        b.Add(t)


def copper(b, net):
    return sorted((t.GetLayer(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y)
                  for t in b.GetTracks() if t.GetNetname() == net)


def fence_case(region):
    """4 / 5: WALL is the only rip-up candidate, and it has copper outside the region."""
    import time
    b = pcbnew.BOARD()
    edge(b, 60.0, 20.0)
    pads(b, "TARGET", [(25.0, 5.0), (40.0, 15.0)], 1)
    wall = pads(b, "WALL", [(10.0, 15.0), (30.0, 1.0)], 3)
    track(b, wall, [(10.0, 15.0), (10.0, 19.2), (30.0, 19.2), (30.0, 1.0)])
    before = copper(b, "WALL")
    lay = dict(LAY, rip_up=1, net_classes={"one_layer": {"nets": ["TARGET", "WALL"], "track": 0.25, "layers": ["F.Cu"]}})
    fam = {"name": "t", "nets": ["TARGET"]}
    if region:
        fam["region"] = region
    lay["families"] = [fam]
    t0 = time.monotonic()
    failed = pcb_route.route_families(b, lay, [("TARGET", (25.0, 5.0), (40.0, 15.0))])
    return sorted({m[0] for m in failed}), copper(b, "WALL") == before, copper(b, "TARGET"), time.monotonic() - t0


def channel_case(plot=None):
    """6: a family on [F.Cu, In2.Cu] through an In2 channel between keep-outs."""
    from shapely.geometry import LineString, box
    b = pcbnew.BOARD()
    b.SetCopperLayerCount(4)
    edge(b, 60.0, 20.0)
    pads(b, "TARGET", [(10.0, 10.0), (50.0, 10.0)], 1)
    wall = pcbnew.NETINFO_ITEM(b, "WALL")
    b.Add(wall)
    track(b, wall, [(30.0, 0.6), (30.0, 19.4)], locked=True)
    keep = [(25.0, 0.0, 35.0, 9.0), (25.0, 11.0, 35.0, 20.0)]
    for x0, y0, x1, y1 in keep:
        z = pcbnew.ZONE(b)
        z.SetIsRuleArea(True)
        ls = pcbnew.LSET()
        ls.AddLayer(pcbnew.In2_Cu)
        z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowCopperPour(True)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(MM(x), MM(y))
        b.Add(z)
    lay = dict(LAY, net_classes={}, families=[{"name": "channel", "nets": ["TARGET"], "layers": ["F.Cu", "In2.Cu"],
                                              "region": [5.0, 2.0, 55.0, 18.0]}])
    failed = pcb_route.route_families(b, lay, [("TARGET", (10.0, 10.0), (50.0, 10.0))])
    inner = [t for t in b.GetTracks() if type(t) is pcbnew.PCB_TRACK and t.GetNetname() == "TARGET" and t.GetLayer() == pcbnew.In2_Cu]
    kz = [box(*k) for k in keep]
    hit = [t for t in inner if any(LineString([(pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)),
                                               (pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y))]).buffer(0.125).intersects(k) for k in kz)]
    vias = sum(1 for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "TARGET")
    if plot:
        p = os.path.join(tempfile.mkdtemp(prefix="families-"), "c.kicad_pcb")
        pcbnew.SaveBoard(p, b)
        import pcb_plot
        pcb_plot.plot(p, os.path.join(plot, "families-test-channel.png"), nets=["TARGET", "WALL"], title="families test: In2 channel")
    return [m[0] for m in failed], len(inner), len(hit), vias


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
    f4, same4, t4, s4 = fence_case(None)
    print(f"4. fence case, no region (control):         failed {f4 or 'none'}, WALL {'untouched' if same4 else 'taken up'}, "
          f"TARGET {len(t4)} track(s), {s4:.1f} s")
    ok &= not f4 and not same4
    f5, same5, t5, s5 = fence_case([20.0, 0.0, 60.0, 20.0])
    print(f"5. fence case, region x 20-60:              failed {f5 or 'none'}, WALL {'untouched' if same5 else 'taken up'}, "
          f"TARGET {len(t5)} track(s), {s5:.1f} s")
    ok &= f5 == ["TARGET"] and same5 and not t5
    f6, n6, h6, v6 = channel_case(a.plot)
    print(f"6. In2.Cu channel:                          failed {f6 or 'none'}, {n6} In2 track(s), {v6} via(s), "
          f"{h6} In2 track(s) in the keep-out")
    ok &= not f6 and n6 > 0 and h6 == 0
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
