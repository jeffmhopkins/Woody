#!/usr/bin/env python3
"""The per-net scorecard of a routed board: what "this looks weird" was, as numbers (#47).

    python3 tools/pcb_score.py <board.kicad_pcb> [--nets GLOB,...] [--csv OUT] [--md OUT]
                               [--flag RATIO] [--all]

For each net with two or more pads and copper of its own (or every such net, --all):
- pads, and the AIRWIRE: the shortest tree through its pads' centres, in mm;
- the routed length (its tracks), the ratio routed / airwire, and its vias;
- OPEN: connections still missing, by KiCad's connectivity (zones filled first);
- DANGLING: track ends that touch nothing of the net (no pad, via, track or zone);
- ACID: pcb.py check's acid traps (pcb.check_tracks).
A net is FLAGGED when it is open, dangles, has an acid trap, or routes more than --flag
(default 1.5) times its airwire. Nets with a zone (the planes) are left out: their airwire
is the plane. The totals line ends the table.

Two boards routed from one placement score on the same terms (the Freerouting benchmark,
2026-10-12), which is the point: a number to compare, where a plot only shows.
"""
import csv
import fnmatch
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _mst(points):
    """The length of the minimum spanning tree through points (Prim's)."""
    if len(points) < 2:
        return 0.0
    left = list(range(1, len(points)))
    best = {i: math.dist(points[0], points[i]) for i in left}
    total = 0.0
    while left:
        i = min(left, key=lambda k: best[k])
        total += best[i]
        left.remove(i)
        for k in left:
            best[k] = min(best[k], math.dist(points[i], points[k]))
    return total


def score(path, nets=None, flag=1.5, everything=False):
    """[{net, pads, airwire, length, ratio, vias, open, dangling, acid, flags}] for the board."""
    import pcbnew
    import pcb
    b = pcbnew.LoadBoard(path)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    conn = b.GetConnectivity()
    mm = pcbnew.ToMM
    zoned = {z.GetNetname() for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()}
    pads = {}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() and not p.GetNetname().startswith("unconnected"):
                pads.setdefault(p.GetNetname(), []).append(p)
    tracks = [t for t in b.GetTracks() if type(t) is pcbnew.PCB_TRACK]
    vias = [t for t in b.GetTracks() if type(t) is pcbnew.PCB_VIA]
    by_net = {}
    for t in tracks:
        by_net.setdefault(t.GetNetname(), []).append(t)
    vias_of = {}
    for v in vias:
        vias_of[v.GetNetname()] = vias_of.get(v.GetNetname(), 0) + 1
    acid = {}
    for line in pcb.check_tracks(b):
        n_ = line.split("[tracks] ", 1)[1].split(" on ", 1)[0]
        acid[n_] = acid.get(n_, 0) + 1

    def dangling(net):
        """Track ends of `net` touching nothing of it."""
        ts = by_net.get(net, [])
        ends = {}
        for t in ts:
            for e in (t.GetStart(), t.GetEnd()):
                ends[(t.GetLayer(), e.x, e.y)] = ends.get((t.GetLayer(), e.x, e.y), 0) + 1
        n = 0
        for t in ts:
            for e in (t.GetStart(), t.GetEnd()):
                if ends[(t.GetLayer(), e.x, e.y)] > 1:
                    continue
                if any(v.GetNetname() == net and v.HitTest(e) for v in vias):
                    continue
                if any(p.IsOnLayer(t.GetLayer()) and p.HitTest(e) for p in pads.get(net, [])):
                    continue
                if any(u is not t and u.GetLayer() == t.GetLayer() and u.HitTest(e) for u in ts):
                    continue
                if any(z.GetNetname() == net and z.IsOnLayer(t.GetLayer()) and z.HitTestFilledArea(t.GetLayer(), e)
                       for z in b.Zones()):
                    continue
                n += 1
        return n

    rows = []
    for net, ps in sorted(pads.items()):
        if len(ps) < 2 or net in zoned:
            continue
        if nets and not any(fnmatch.fnmatchcase(net, g) for g in nets):
            continue
        if not everything and not nets and net not in by_net:
            continue
        air = _mst([(mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in ps])
        length = sum(mm(t.GetLength()) for t in by_net.get(net, []))
        r = {"net": net, "pads": len(ps), "airwire": round(air, 1), "length": round(length, 1),
             "ratio": round(length / air, 2) if air > 0 else 0.0, "vias": vias_of.get(net, 0),
             "open": _open(b, conn, net, ps), "dangling": dangling(net), "acid": acid.get(net, 0)}
        f = []
        if r["open"]:
            f.append("open")
        if r["dangling"]:
            f.append("dangling")
        if r["acid"]:
            f.append("acid")
        if r["ratio"] > flag:
            f.append(f">{flag}x")
        r["flags"] = " ".join(f)
        rows.append(r)
    return rows


def _open(b, conn, net, ps):
    """Connections of `net` still missing: its pads in groups that its copper joins, less one.
    Copper joins where it overlaps on a layer both pieces are on - pads, tracks, vias (every
    layer) and filled zones - by geometry (KiCad's own connectivity takes a list of item
    types its Python binding will not build)."""
    import pcbnew
    from shapely.geometry import LineString, Point
    from shapely.strtree import STRtree
    mm = pcbnew.ToMM
    cu = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
    items = []                                  # (geometry, layers, is pad)
    for p in ps:
        for L in cu:
            if p.IsOnLayer(L):
                items.append((_poly(p.GetEffectivePolygon(L, pcbnew.ERROR_INSIDE)), {L}, True))
    for t in b.GetTracks():
        if t.GetNetname() != net:
            continue
        if type(t) is pcbnew.PCB_VIA:
            c = t.GetPosition()
            items.append((Point(mm(c.x), mm(c.y)).buffer(mm(t.GetWidth(pcbnew.F_Cu)) / 2), set(cu), False))
        elif type(t) is pcbnew.PCB_TRACK:
            a_, e_ = t.GetStart(), t.GetEnd()
            g = LineString([(mm(a_.x), mm(a_.y)), (mm(e_.x), mm(e_.y))]) if a_ != e_ else Point(mm(a_.x), mm(a_.y))
            items.append((g.buffer(mm(t.GetWidth()) / 2), {t.GetLayer()}, False))
    for z in b.Zones():
        if z.GetNetname() != net or z.GetIsRuleArea():
            continue
        for L in cu:
            if z.IsOnLayer(L) and z.HasFilledPolysForLayer(L):
                items.append((_poly(z.GetFilledPolysList(L)), {L}, False))
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    tree = STRtree([g for g, _, _ in items])
    for i, (g, ls, _) in enumerate(items):
        for j in tree.query(g):
            j = int(j)
            if j > i and ls & items[j][1] and g.intersects(items[j][0]):
                parent[find(i)] = find(j)
    # a pad on several layers is one piece of copper (a through-hole pad)
    k = 0
    for p in ps:
        ids = []
        for L in cu:
            if p.IsOnLayer(L):
                ids.append(k)
                k += 1
        for i in ids[1:]:
            parent[find(i)] = find(ids[0])
    groups = {find(i) for i, (_, _, pad) in enumerate(items) if pad}
    return max(0, len(groups) - 1)


def _poly(ps):
    """A KiCad SHAPE_POLY_SET as one shapely geometry."""
    import pcbnew
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    pts = lambda c: [(pcbnew.ToMM(c.CPoint(j).x), pcbnew.ToMM(c.CPoint(j).y)) for j in range(c.PointCount())]
    out = []
    for i in range(ps.OutlineCount()):
        o = pts(ps.Outline(i))
        if len(o) >= 3:
            out.append(Polygon(o, [pts(ps.Hole(i, h)) for h in range(ps.HoleCount(i))]).buffer(0))
    return unary_union(out)


def totals(rows):
    return {"nets": len(rows), "airwire": round(sum(r["airwire"] for r in rows), 1),
            "length": round(sum(r["length"] for r in rows), 1),
            "ratio": round(sum(r["length"] for r in rows) / max(1e-9, sum(r["airwire"] for r in rows)), 2),
            "vias": sum(r["vias"] for r in rows), "open": sum(r["open"] for r in rows),
            "dangling": sum(r["dangling"] for r in rows), "acid": sum(r["acid"] for r in rows),
            "flagged": sum(1 for r in rows if r["flags"])}


COLS = ["net", "pads", "airwire", "length", "ratio", "vias", "open", "dangling", "acid", "flags"]


def markdown(rows, title=""):
    t = totals(rows)
    out = [f"## {title}" if title else "", "",
           f"{t['nets']} nets, {t['length']} mm routed for {t['airwire']} mm of airwire "
           f"({t['ratio']}x), {t['vias']} vias, {t['open']} open, {t['dangling']} dangling, "
           f"{t['acid']} acid, {t['flagged']} flagged.", "",
           "| " + " | ".join(COLS) + " |", "|" + "---|" * len(COLS)]
    for r in sorted(rows, key=lambda r: (not r["flags"], -r["ratio"])):
        out.append("| " + " | ".join(str(r[c]) for c in COLS) + " |")
    return "\n".join(out) + "\n"


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    def opt(k, d=None):
        if k in args:
            i = args.index(k)
            v = args[i + 1]
            del args[i:i + 2]
            return v
        return d
    nets = opt("--nets")
    nets = nets.split(",") if nets else None
    out_csv, out_md, flag = opt("--csv"), opt("--md"), float(opt("--flag", 1.5))
    everything = "--all" in args
    if everything:
        args.remove("--all")
    rows = score(args[0], nets, flag, everything)
    t = totals(rows)
    for r in sorted(rows, key=lambda r: (not r["flags"], -r["ratio"])):
        print(f"{r['net'][:44]:44s} {r['pads']:3d} {r['airwire']:7.1f} {r['length']:7.1f} {r['ratio']:5.2f}x "
              f"{r['vias']:3d}v open {r['open']} dangl {r['dangling']} acid {r['acid']}  {r['flags']}")
    print(f"score: {t['nets']} nets, {t['length']} mm for {t['airwire']} mm airwire ({t['ratio']}x), "
          f"{t['vias']} vias, open {t['open']}, dangling {t['dangling']}, acid {t['acid']}, flagged {t['flagged']}")
    if out_csv:
        with open(out_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            w.writerows(rows)
    if out_md:
        with open(out_md, "w") as f:
            f.write(markdown(rows, os.path.basename(args[0])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
