#!/usr/bin/env python3
"""pcb_topo - the topological router (ADR 0029, #47).

A line is planned before it is drawn. Each copper layer is a constrained Delaunay
triangulation (Shewchuk's `triangle`) of the room to route in. Its vertices are the CORNERS
of everything a track must keep clear of - each pad's polygon, the keep-outs, holes and
locked copper, the board's edge - and each pad's centre, where its own line starts. A pad's
outline and a fan from its centre to its corners are constrained edges, so a pad is a little
wheel of triangles only its own net may enter.

A route is the path of triangle edges a line crosses and, on each edge, its PLACE IN THAT
EDGE'S ORDER of lines. A new line takes a place between two lines already on an edge - it
squeezes between them - and nothing is re-laid, because nothing is laid yet: the lines
beyond it are pushed over by one pitch when the geometry is drawn. That is the owner's "push
traces out of the way and merge between traces" (2026-10-11), here a fact of the plan
rather than a repair after a failure.

Inside one triangle every line is a chord between two points of the triangle's boundary,
and two lines on one layer cross exactly when their chords interleave; the search refuses
a place whose chord would cross (T1: one layer - T2 prices the crossing and resolves it
with a via). An edge's CAPACITY is how many centrelines fit along its free part (its length
less what the obstacles at its ends take, grown by clearance and half a track).

Geometry last: each line is the shortest path through its PORTALS - on each edge it crosses,
the stretch between where its neighbours in the order cross, a spacing off each - by the
funnel algorithm, relaxed in passes (each line taut between its neighbours as they stand).
Where it bends at a corner it is drawn as an ARC round that corner at the radius the bend
stands at - a clearance and half a track out, one pitch more for each line nested inside -
so nested lines are concentric and a bend never cuts a corner. A last pass measures every
pair of neighbours and widens the spacing where a slant brought them too close.

The result is pcb_route2 Runs, their points exact (not on pcb_route2's lattice): the grid
router's fits(), write() and KiCad's DRC judge them exactly as they judge its own.

T1 (this file): one layer, two-pad nets. T2 layers and vias, T3 nets of more pads, T4 the
stage's engine option, T4b the small test boards, T5 the main board (#47).
"""
import heapq
import math
import os
import sys

import numpy as np
import triangle
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcb_route2 as R2     # noqa: E402

TOL = 0.01                  # mm: added to every clearance the plan keeps (rounding, arcs)
ARC_STEP = math.radians(15) # an arc is drawn in steps of this; its points stand outside the circle
SLACK = 0.05               # mm a gap must spare beyond the clearances to be a lane
VIA_REF = "~via"            # the ref of a via the plan places (a pad on every layer, of its net)


def _polys(g):
    if g.is_empty:
        return []
    return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > 1e-6]


SIDE = 0.5                  # mm: no outline side longer - see _split


def _split(pts, side=SIDE):
    """A closed ring's points with every side cut to at most `side`: the narrowest gap
    between a corner and an outline is square onto a side's middle, and only an EDGE of the
    map is measured - with long sides that gap fell inside a triangle, and a line went
    through a passage narrower than a track (the four-layer board's S1, by C1)."""
    out = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        n = max(1, int(math.ceil(math.dist(a, b) / side)))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
    return out


def _corners(poly, tol=0.02):
    """A pad's outline as corners (its convex hull, simplified), its sides split to SIDE."""
    h = poly.convex_hull.simplify(tol)
    if h.geom_type != "Polygon":
        h = poly.buffer(0.01).convex_hull
    pts = list(h.exterior.coords)[:-1]
    # counter-clockwise, without repeats
    if Polygon(pts).exterior.is_ccw is False:
        pts = pts[::-1]
    return _split(pts)


class Map:
    """One layer of a pcb_route2 Model, triangulated. `nets`: the nets to be routed here.
    Every pad on the layer is a wheel only its net enters; everything else on the layer -
    holes, keep-outs, other nets' copper - is an area obstacle, a hole in the map."""

    def __init__(self, model, layer, nets, pitch=None, width=None, lanes=1, narrow=False, layers=None):
        """`layer` None: every layer at once - the PLAN map, where a net's way and its
        crossings are negotiated before it has a layer: all copper on any layer is in the
        way, and each edge takes `lanes` times the lines (one set per layer)."""
        R = model.rules
        self.m, self.layer, self.lanes = model, layer, lanes
        # the plan map (layer None): what is on any of the SIGNAL layers being planned - not
        # the plane layers, whose reservations (the splits) walled every pad in on the main
        # board (J4.10 reached a millimetre round itself; five power nets unplanned)
        if layer is None:
            sig = set(layers) if layers is not None else set(range(model.nl))
            on = (lambda ls: bool(set(ls) & sig))
        else:
            on = (lambda ls: layer in set(ls))
        self.nets = set(nets)
        # `narrow`: the map at the family's NARROWEST track and clearance, each wider line
        # charged its extra where it crosses an edge (room) - at the widest, a 0.3 mm rail
        # could not leave a 1.27 mm header's pin because 0.5 mm rails were in its family
        # (the main board's power family: five of seven nets unplanned, 2026-10-11)
        pick = min if narrow else max
        self.width = width or pick(R.width(n) for n in nets)
        self.clear = pick(R.clear(n) for n in nets) if narrow else max([R.clear(n) for n in nets] + [R.clearance])
        self.keep = self.clear + self.width / 2 + TOL            # a centreline's distance off copper
        self.pitch = pitch or (self.width + self.clear + TOL)
        areas = []
        for e in model.index.e.values():
            if not on(e.layers):
                continue
            if (e.kind == "keepout" and e.tracks) or e.kind == "hole" \
                    or (e.kind in ("track", "via") and e.net not in self.nets) \
                    or (e.kind == "reserve" and not (set(e.family or ()) & self.nets)):
                # a reservation (a pair's guard, a part's clearance, a pin's escape band) is in
                # the way of every net it is not for - the grid router holds it so, and a plan
                # through it is one the grid cannot lay (#47 T6)
                areas.append(e.geom)
        self.areas = unary_union(areas) if areas else Polygon()
        self.pads = [p for p in model.pads if on(p.layers)]
        # a pad whose centre is under copper (a plane pad's own fanout track) is no terminal
        # here, but it is still copper: it joins the areas - left out, the map had no corner
        # of it and a line was planned straight across it (the four-layer board's C1)
        under = [p.geom for p in self.pads if self.areas.contains(Point(p.centre))]
        if under:
            self.areas = unary_union([self.areas] + under)
        verts, segs, holes = [], [], []
        self.vpad = {}                  # vertex -> the pad (index) it is the centre or a corner of
        self.centre = {}                # pad index -> its centre vertex
        room = model.inside.difference(self.areas)
        for i, p in enumerate(self.pads):
            if not room.contains(Point(p.centre)):
                continue                # a pad under copper or a keep-out: not reachable here
            c = len(verts)
            verts.append(p.centre)
            self.centre[i] = c
            self.vpad[c] = i
            cs = _corners(p.geom)
            first = len(verts)
            for q in cs:
                self.vpad[len(verts)] = i
                segs.append((c, len(verts)))            # the fan
                verts.append(q)
            for k in range(len(cs)):                    # the outline
                segs.append((first + k, first + (k + 1) % len(cs)))

        def ring(coords):
            coords = _split(list(coords)[:-1])
            i0 = len(verts)
            verts.extend(coords)
            segs.extend((i0 + k, i0 + (k + 1) % len(coords)) for k in range(len(coords)))
        # the free room as rings: a keep-out to the board's edge is a bite out of the
        # outside, one in the middle a hole
        for poly in _polys(room.simplify(0.01)):
            ring(poly.exterior.coords)
            for hole in poly.interiors:
                ring(hole.coords)
                # seeded in the obstacle, not in free room nested inside the hole (an island of
                # room in a ring of copper): seeded there, triangle ate the island (the main
                # board, a 106 mm² hole at x 306)
                solid = Polygon(hole).difference(room).buffer(-0.02)    # off simplify's slivers
                solid = max(_polys(solid) or [Polygon(hole)], key=lambda g: g.area)
                holes.append(solid.representative_point().coords[0])
        # triangle (C) is fed clean input or it crashes the process (the island board, a
        # segfault): coincident points merged - the first keeps its index, so the pads'
        # centres and corners keep theirs - zero-length and repeated segments dropped
        key, remap, clean = {}, {}, []
        for i, (x, y) in enumerate(verts):
            k_ = (round(x, 5), round(y, 5))
            if k_ in key:
                remap[i] = key[k_]
            else:
                key[k_] = remap[i] = len(clean)
                clean.append((x, y))
        segs = sorted({(min(remap[a], remap[b]), max(remap[a], remap[b])) for a, b in segs if remap[a] != remap[b]})
        self._remap = remap
        self.centre = {i: remap[c] for i, c in self.centre.items()}
        vp = {}
        for v, i in self.vpad.items():
            vp.setdefault(remap[v], i)          # a corner two pads share: the first pad's
        self.vpad = vp
        A = {"vertices": np.array(clean, dtype=float), "segments": np.array(segs, dtype=int).reshape(-1, 2)}
        if holes:
            A["holes"] = np.array(holes, dtype=float)
        T = triangle.triangulate(A, "p")
        self.xy = [(float(v[0]), float(v[1])) for v in T["vertices"]]
        self.tris = [tuple(int(i) for i in t) for t in T["triangles"]]
        self.vtri, self.etris = {}, {}
        for ti, (a, b, c) in enumerate(self.tris):
            for v in (a, b, c):
                self.vtri.setdefault(v, []).append(ti)
            for u, v in ((a, b), (b, c), (c, a)):
                self.etris.setdefault((min(u, v), max(u, v)), []).append(ti)
        # what copper keeps clear of: every pad, every area, the board's edge
        pads_g = unary_union([p.geom for p in self.pads]) if self.pads else Polygon()
        outside = model.outline.buffer(5.0).difference(model.inside)
        self._rest = unary_union([self.areas.buffer(self.keep), outside.buffer(self.width / 2 + TOL)])
        self._padkeep = [p.geom.buffer(self.keep) for p in self.pads]
        from shapely.strtree import STRtree as _T
        self._padtree = _T(self._padkeep) if self._padkeep else None
        self._span = {}
        self.blk = unary_union([pads_g.buffer(self.keep), self._rest])
        self.edges, self.inpad = {}, {}
        for k, ts in self.etris.items():
            if len(ts) != 2:
                continue
            pa_, pb_ = self.vpad.get(k[0]), self.vpad.get(k[1])
            L = math.dist(self.xy[k[0]], self.xy[k[1]])
            if pa_ is not None and pa_ == pb_:
                # inside one pad (its fan or its outline): its own net's way out, anywhere
                self.inpad[k] = pa_
                self.edges[k] = (0.05 * L, 0.95 * L, L)
            else:
                self.edges[k] = self._free(k)
        # every corner a line can bend round: the pads' corners and the room's
        from shapely.strtree import STRtree
        cs = [v for v, i in self.vpad.items() if v != self.centre.get(i)]
        cs += [i for i in range(len(self.xy)) if i not in self.vpad]
        self.corner_ids = cs
        self.corner_tree = STRtree([Point(self.xy[i]) for i in cs])
        self.order = {k: [] for k in self.edges}            # line ids, from k[0]'s end to k[1]'s
        self.chords = {ti: [] for ti in range(len(self.tris))}
        self.lines = {}

    # ---------------------------------------------------------------- the edges

    def _free(self, k):
        """(t0, t1, length): the longest free stretch of edge k, as distances from k[0]."""
        a, b = self.xy[k[0]], self.xy[k[1]]
        seg = LineString([a, b])
        L = seg.length
        free = seg.difference(self.blk)
        pieces = [g for g in getattr(free, "geoms", [free]) if g.geom_type == "LineString" and g.length > 0] \
            if not free.is_empty else []
        if not pieces:
            return (0.0, -1.0, L)
        g = max(pieces, key=lambda g: g.length)
        t0, t1 = seg.project(Point(g.coords[0])), seg.project(Point(g.coords[-1]))
        return (min(t0, t1), max(t0, t1), L)

    def span(self, k, own=()):
        """Edge k's free part for a line from the pads `own`: an end on one of them is that
        line's own copper, not in its way. Measured against every pad, the edges between a
        header pin's open side and its neighbours' (they run along the pin column) had no
        free part at all, and nothing could leave the pin: on the main board J4.10 reached a
        millimetre round itself and five power nets went unplanned (#47 T5)."""
        # The PLAN map's only: its lines are guides. A per-layer map's are drawn as bands, and
        # the drawing measures each edge without the relief - a line placed there on an edge
        # it took for shut came apart into thousands of segments (the fan board)
        mine = [e for e in (self.vpad.get(k[0]), self.vpad.get(k[1])) if e is not None and e in own]
        if self.layer is not None or not mine or k in self.inpad:
            return self.edges[k]
        key = (k, frozenset(mine))
        if key not in self._span:
            seg = LineString([self.xy[k[0]], self.xy[k[1]]])
            near = [self._padkeep[i] for i in self._padtree.query(seg) if i not in own]
            blk = unary_union(near + [self._rest.intersection(seg.buffer(0.01))])
            free = seg.difference(blk)
            pieces = [g for g in getattr(free, "geoms", [free]) if g.geom_type == "LineString" and g.length > 0] \
                if not free.is_empty else []
            if not pieces:
                self._span[key] = (0.0, -1.0, seg.length)
            else:
                g = max(pieces, key=lambda g: g.length)
                t0, t1 = seg.project(Point(g.coords[0])), seg.project(Point(g.coords[-1]))
                self._span[key] = (min(t0, t1), max(t0, t1), seg.length)
        return self._span[key]

    def pitch_of(self, net):
        """The centre-to-centre room a line of `net` takes: its class's track and clearance."""
        R = self.m.rules
        return R.width(net) + R.clear(net) + TOL

    def room(self, k, net, own=()):
        """Whether edge k takes one more line, of `net`, beside those on it: the pitches of
        all of them, each net's own class (#47 T6 - a 0.6 mm rail is not a 0.2 mm signal),
        within its free part (per layer of the plan map's `lanes`)."""
        if k in self.inpad:
            return self.inpad[k] in own and len(self.order[k]) < 8
        t0, t1, _ = self.span(k, own)
        if t1 - t0 < SLACK:
            return False
        others = [self.lines[l]["net"] for l in self.order[k]]
        ps = [self.pitch_of(n_) for n_ in others] + [self.pitch_of(net)]
        need = sum(ps) - max(ps)
        # each end of the free part was measured at this map's keep; a line keeping further
        # off copper (wider, or a wider clearance) has that much less of it, at each end
        R = self.m.rules
        extra = max(0.0, max(R.clear(n_) + R.width(n_) / 2 + TOL - self.keep for n_ in others + [net]))
        return need <= (t1 - t0 - SLACK - 2 * extra) * self.lanes + 1e-9

    def capacity(self, k, own=()):
        """How many lines edge k takes. An edge inside a pad takes its own net's line only."""
        if k in self.inpad:
            return 8 if self.inpad[k] in own else 0     # a pad of several lines of its net
        t0, t1, _ = self.span(k, own)
        # a lane wants SLACK more than the bare clearances: a gap of exactly a track between
        # two of a SOIC's pins (0.67 mm for 0.65) took a line the geometry then could not
        # draw clear (the crowd board's IO1 and GATE between U6's pins)
        if t1 - t0 < SLACK:
            return 0
        return (int(math.floor((t1 - t0 - SLACK) / self.pitch + 1e-9)) + 1) * self.lanes

    def _at(self, k, t):
        a, b = self.xy[k[0]], self.xy[k[1]]
        L = math.dist(a, b)
        f = t / L if L else 0.5
        return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)

    def _slot_point(self, k, s):
        t0, t1, L = self.edges[k]
        n = len(self.order[k]) + 1
        t = t0 + (t1 - t0) * (s + 0.5) / n if t1 > t0 else L / 2
        return self._at(k, t)

    # ---------------------------------------------------------------- the chords

    def _bpos(self, ti, end, new=False):
        """Where `end` - ('v', vertex), ('e', edge, place) or an _EdgeRef - sits on triangle
        ti's boundary, as a number round it (vertex a 0, edge ab (0, 1), b 1, ...). An edge's
        n lines stand at (i + 1) / (n + 1) along it; a new line's slot s at (s + 0.5) / (n + 1)
        - between the lines either side of it, and never on one."""
        a, b, c = self.tris[ti]
        if isinstance(end, _EdgeRef):
            k, place = end.k, self.order[end.k].index(end.lid)
        elif end[0] == "v":
            return float((a, b, c).index(end[1]))
        else:
            _, k, place = end
        f = (place + (0.5 if new else 1.0)) / (len(self.order[k]) + 1)
        for base, (u, v) in enumerate(((a, b), (b, c), (c, a))):
            if (min(u, v), max(u, v)) == k:
                return base + (f if u == k[0] else 1.0 - f)
        raise ValueError("edge not on triangle")

    def _crossings(self, ti, e1, e2):
        """The lines already in triangle ti a new chord e1 - e2 would cross (their ids)."""
        p1, p2 = self._bpos(ti, e1, new=True), self._bpos(ti, e2, new=True)
        lo, hi = min(p1, p2), max(p1, p2)
        out = []
        for lid_, q1, q2 in self.chords[ti]:
            if self.lines[lid_]["net"] == getattr(self, "_cur", None):
                continue        # the same net's copper: lines of one net may meet and cross
            a, b = self._bpos(ti, q1), self._bpos(ti, q2)
            if min(abs(a - lo), abs(a - hi), abs(b - lo), abs(b - hi)) < 1e-9:
                continue        # a shared end (a vertex both lines leave from)
            if (lo < a < hi) != (lo < b < hi):
                out.append(lid_)
        return out

    def crossed(self, lid):
        """The other nets' lines line lid crosses, as the orders now stand."""
        out = set()
        for ti, chords in self.chords.items():
            mine = [c for c in chords if c[0] == lid]
            if not mine:
                continue
            for _, e1, e2 in mine:
                p1, p2 = self._bpos(ti, e1), self._bpos(ti, e2)
                lo, hi = min(p1, p2), max(p1, p2)
                for l2, q1, q2 in chords:
                    if l2 == lid or self.lines[l2]["net"] == self.lines[lid]["net"]:
                        continue
                    a, b = self._bpos(ti, q1), self._bpos(ti, q2)
                    if min(abs(a - lo), abs(a - hi), abs(b - lo), abs(b - hi)) < 1e-9:
                        continue
                    if (lo < a < hi) != (lo < b < hi):
                        out.add(l2)
        return out

    # ---------------------------------------------------------------- the search

    def _xcost(self, ti, e1, e2):
        """What a chord e1 - e2 in triangle ti costs in crossings: None (refused) when it
        crosses anything and crossings are not allowed (the per-layer maps); else the price
        of each line it crosses (the plan map: self.cross(net, other net) -> mm)."""
        xs = self._crossings(ti, e1, e2)
        if not xs:
            return 0.0
        if self._cross is None:
            return None
        return sum(self._cross(self._cur, self.lines[l]["net"]) for l in xs)

    def route(self, net, ia, ib, pending=(), toll=None, tee=False, cross=None, guide=None, guide_w=1.5):
        """Plan one line from pad ia's centre to pad ib's (indices into self.pads). Returns
        the line id, or None. `pending`: [(a, b)] the straight airwires of nets still to be
        routed; each one this line's way crosses costs `toll` mm (default: a few pitches) -
        so a line does not take, for being first, the way a later one needs (the fan board:
        the first line went between the header's columns and round under its own, and the
        last pad of that column was sealed in)."""
        toll = 4.0 if toll is None else toll
        if ia not in self.centre or ib not in self.centre:
            return None
        self._cur = net
        self._cross = cross
        # THE GUIDE: the way the negotiated plan found for this net (plan_layers), followed
        # here as a cost - each mm of line `guide_w` mm dearer for each mm it strays beyond
        # a band round the guide - so a layer laid net by net keeps the order and the sides
        # the negotiation settled, instead of planning them again from scratch
        self._guide, self._gw = guide, guide_w
        pa, pb = self.centre[ia], self.centre[ib]
        own = {ia, ib}
        P, Q = self.xy[pa], self.xy[pb]
        heap, best, came = [], {}, {}
        cnt = 0
        goal, goal_cost = None, math.inf

        def ok(k):
            return k in self.edges and self.room(k, net, own)

        def tolls(a, b):
            # crossing a pending airwire near one of its ends seals that pad's way out - six
            # tolls; anywhere else one (the stagemix board: the keys crossed between U1's
            # rows, a few mm from the pins the next family needed, for one toll each)
            t = 0.0
            for (c, d) in pending:
                if _cross(a, b, c, d):
                    x = _meet(a, b, c, d)
                    t += toll * (6.0 if min(math.dist(x, c), math.dist(x, d)) < 3.0 else 1.0)
            return t

        def stray(a, b):
            if self._guide is None:
                return 0.0
            mid = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            off = mid.distance(self._guide) - 0.5
            return self._gw * math.dist(a, b) * off if off > 0 else 0.0

        def push(st, g, pt, frm):
            nonlocal cnt
            if g < best.get(st, math.inf) - 1e-12:
                best[st] = g
                came[st] = frm
                cnt += 1
                heapq.heappush(heap, (g + math.dist(pt, Q), cnt, g, st, pt))
        for ti in self.vtri.get(pa, []):
            if pb in self.tris[ti] and self._xcost(ti, ("v", pa), ("v", pb)) is not None:
                goal, goal_cost = ("direct", ti), math.dist(P, Q) + self._xcost(ti, ("v", pa), ("v", pb))
            for k in self._tri_edges(ti):
                if not ok(k) or pa in k:
                    continue
                for s in range(len(self.order[k]) + 1):
                    xc = self._xcost(ti, ("v", pa), ("e", k, s))
                    if xc is not None:
                        pt = self._slot_point(k, s)
                        push((k, s, self._other(k, ti)), math.dist(P, pt) + tolls(P, pt) + xc + stray(P, pt), pt, ("start", ti))
        while heap:
            f, _, g, st, pt = heapq.heappop(heap)
            if f >= goal_cost:
                break
            if g > best.get(st, math.inf) + 1e-12:
                continue
            k1, s1, ti = st
            if tee:
                lids = self.order[k1]
                for nb in (s1 - 1, s1):
                    if 0 <= nb < len(lids) and self.lines[lids[nb]]["net"] == net and g < goal_cost:
                        goal, goal_cost = ("tee", st, lids[nb]), g
            xq = self._xcost(ti, ("e", k1, s1), ("v", pb)) if pb in self.tris[ti] else None
            if xq is not None:
                c = g + math.dist(pt, Q) + tolls(pt, Q) + xq + stray(pt, Q)
                if c < goal_cost:
                    goal, goal_cost = ("end", st, ti), c
            for k2 in self._tri_edges(ti):
                if k2 == k1 or not ok(k2):
                    continue
                for s2 in range(len(self.order[k2]) + 1):
                    xc = self._xcost(ti, ("e", k1, s1), ("e", k2, s2))
                    if xc is not None:
                        p2 = self._slot_point(k2, s2)
                        push((k2, s2, self._other(k2, ti)), g + math.dist(pt, p2) + tolls(pt, p2) + xc + stray(pt, p2), p2, (st, ti))
        if goal is None:
            return None
        steps = []
        host = None
        if goal[0] == "direct":
            last_t = goal[1]
        else:
            _, st, last_t = goal
            if goal[0] == "tee":
                host, last_t = goal[2], None
            while True:
                prev = came[st]
                if prev[0] == "start":
                    steps.append((st[0], st[1], prev[1]))
                    break
                pst, ti = prev
                steps.append((st[0], st[1], ti))
                st = pst
            steps.reverse()
        return self._commit(net, pa, None if host is not None else pb, steps, last_t, host)

    def _tri_edges(self, ti):
        a, b, c = self.tris[ti]
        return [(min(u, v), max(u, v)) for u, v in ((a, b), (b, c), (c, a))]

    def _other(self, k, ti):
        ts = self.etris[k]
        return ts[0] if ts[1] == ti else ts[1]

    def _commit(self, net, pa, pb, steps, last_t, host=None):
        """Write a planned line into the orders and the triangles' chords. Each slot was read
        against the orders as they stood; an edge is crossed once, so each is still right.
        A tee (host set) ends on its last edge, beside the host, and has no last chord."""
        lid = len(self.lines)
        ends = [("v", pa)] + [("e", k, s) for k, s, _ in steps] + ([("v", pb)] if host is None else [])
        tris = [t for _, _, t in steps] + ([last_t] if host is None else [])
        for k, s, _ in steps:
            self.order[k].insert(s, lid)
        for i, ti in enumerate(tris):
            self.chords[ti].append((lid, self._ref(ends[i], lid), self._ref(ends[i + 1], lid)))
        self.lines[lid] = {"net": net, "pa": pa, "pb": pb, "edges": [k for k, _, _ in steps],
                           "tris": [t for _, _, t in steps] + ([last_t] if host is None else []), "host": host}
        return lid

    def _ref(self, end, lid):
        return end if end[0] == "v" else _EdgeRef(end[1], lid)

    # ---------------------------------------------------------------- the geometry

    def geometry(self, passes=6, rounds=8):
        """Each line's centreline, as [(x, y)]. The bands relax in `passes` (each line taut
        between where its neighbours cross); then each bend becomes an arc; then every pair
        of neighbours is measured and, where a slant brought them under a pitch, the spacing
        on the edges they share is widened and the bands drawn again (up to `rounds`)."""
        self.spacing = {k: self.pitch for k in self.order}
        paths = {}
        for _ in range(rounds):
            self._pack()
            for _ in range(passes):
                for lid in self.lines:
                    pts, _ = self._band(lid)
                    self._settle(lid, pts)
            paths = {lid: self._round(lid, self._inflate(lid, self._band(lid)[0])) for lid in self.lines}
            for lid in self.lines:
                net = self.lines[lid]["net"]
                others = [LineString(p) for l2, p in paths.items()
                          if l2 != lid and len(p) > 1 and self.lines[l2]["net"] != net]
                mine = LineString(paths[lid]).buffer(3.0) if len(paths[lid]) > 1 else None
                near_ = [g for g in others if mine is not None and g.intersects(mine)]
                og = unary_union(near_) if near_ else None
                paths[lid] = self._ends(lid, paths[lid], og)
                # and off every other net's line as off copper: neighbours in no edge's order
                # (one ending beside the other, or round a bend) are spaced by nothing else
                # (the crowd board: IO7 0.1 mm into IO38 and IO36)
                if og is not None:
                    pushed = self._inflate(lid, paths[lid], lines=og)
                    # kept only if it bends nothing sharper than a right angle: pushed off
                    # its neighbours where they leave adjacent pads, a fan's lines zig-zagged
                    # (the fan board, 59 acid traps) - a pair still too close is the
                    # planner's check's to send back (_verify)
                    if _sharpest(pushed) >= 90.0 or _sharpest(pushed) >= _sharpest(paths[lid]):
                        paths[lid] = pushed
            if not self._widen(paths):
                break
        for lid, ln in self.lines.items():
            if ln["host"] is not None and len(paths[lid]) >= 2 and len(paths.get(ln["host"], [])) >= 2:
                paths[lid] = self._tee_end(paths[lid], LineString(paths[ln["host"]]))
        return paths

    def _tee_end(self, pts, host):
        """A branch cut where it first comes within a track's width of its trunk, and ended
        square on the trunk from there: drawn to the trunk's crossing on its last edge it ran
        along the trunk first and zig-zagged into it (the stagemix board's KEY3, 37 deg)."""
        reach = self.width
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            seg = LineString([a, b])
            if seg.distance(host) <= reach:
                # the first point of this segment that close
                lo, hi = 0.0, 1.0
                if Point(a).distance(host) > reach:
                    for _ in range(30):
                        mid = (lo + hi) / 2
                        q = (a[0] + (b[0] - a[0]) * mid, a[1] + (b[1] - a[1]) * mid)
                        if Point(q).distance(host) <= reach:
                            hi = mid
                        else:
                            lo = mid
                    q = (a[0] + (b[0] - a[0]) * hi, a[1] + (b[1] - a[1]) * hi)
                    out.append(q)
                foot = host.interpolate(host.project(Point(out[-1])))
                out.append((foot.x, foot.y))
                return out
            out.append(b)
        foot = host.interpolate(host.project(Point(out[-1])))
        return out + [(foot.x, foot.y)]

    def _pack(self):
        """Every line where its place puts it, packed round the middle of each edge's free
        part, a spacing apart - the legal start the passes relax from."""
        self.pos = {}
        for k, lids in self.order.items():
            if not lids:
                continue
            t0, t1, L = self.edges[k]
            sp = self.spacing[k]
            slack = max(0.0, (t1 - t0) - (len(lids) - 1) * sp)
            for i, lid in enumerate(lids):
                self.pos[(k, lid)] = t0 + slack / 2 + i * sp

    def _settle(self, lid, path):
        line = LineString(path)
        for k in self.lines[lid]["edges"]:
            e = LineString([self.xy[k[0]], self.xy[k[1]]])
            x = line.intersection(e)
            if x.is_empty:
                continue
            pt = x if x.geom_type == "Point" else x.centroid
            self.pos[(k, lid)] = e.project(pt)

    def _portal(self, k, lid):
        """(lo t, hi t): the stretch of edge k line lid may cross on - a spacing past the line
        before it in the order, a spacing short of the one after, inside the free part."""
        t0, t1, _ = self.edges[k]
        lids = self.order[k]
        i = lids.index(lid)
        sp = self.spacing[k]
        net = self.lines[lid]["net"]
        # a neighbour of the same net is the same copper: no spacing off it (spaced, a tee's
        # branch pushed its own trunk up into a needless V - the stagemix board's KEY3)
        sp_lo = 0.0 if i > 0 and self.lines[lids[i - 1]]["net"] == net else sp
        sp_hi = 0.0 if i < len(lids) - 1 and self.lines[lids[i + 1]]["net"] == net else sp
        lo = t0 if i == 0 else self.pos[(k, lids[i - 1])] + sp_lo
        hi = t1 if i == len(lids) - 1 else self.pos[(k, lids[i + 1])] - sp_hi
        lo, hi = max(lo, t0), min(hi, t1)
        if lo > hi:
            lo = hi = min(max(self.pos[(k, lid)], t0), t1)
        return lo, hi

    def _band(self, lid):
        """The funnel through the line's portals: (points, bends) - bends[j] is the vertex the
        j-th point bends round (None at the two ends)."""
        ln = self.lines[lid]
        P = self.xy[ln["pa"]]
        if ln["host"] is not None:
            k = ln["edges"][-1]
            Q = self._at(k, self.pos.get((k, ln["host"]), sum(self.edges[k][:2]) / 2))
        else:
            Q = self.xy[ln["pb"]]
        portals, verts = [(P, P)], [(None, None)]
        for k, ti in zip(ln["edges"], ln["tris"]):
            lo, hi = self._portal(k, lid)
            plo, phi = self._at(k, lo), self._at(k, hi)
            ca = _centroid([self.xy[v] for v in self.tris[ti]])
            mid = ((plo[0] + phi[0]) / 2, (plo[1] + phi[1]) / 2)
            dx, dy = mid[0] - ca[0], mid[1] - ca[1]
            side = dx * (plo[1] - mid[1]) - dy * (plo[0] - mid[0])
            # an arc only where the line is PRESSED against the corner at that end: packed up
            # to it (each line nearer the corner a spacing from the next, the nearest at the
            # free part's start) and that start the corner's own clearance, not a third
            # obstacle mid-edge. A bend against anything else stays a point (an arc there,
            # round a far vertex, drew a loop off the board - the fan board, 2026-10-11)
            vlo = vhi = None
            if side > 0:
                portals.append((plo, phi))
                verts.append((vlo, vhi))
            else:
                portals.append((phi, plo))
                verts.append((vhi, vlo))
        portals.append((Q, Q))
        verts.append((None, None))
        return _funnel(portals, verts)

    def _pressed(self, k, lid, lo, hi):
        """(corner at k[0] or None, corner at k[1] or None): the corner line lid presses on,
        at each end of its portal on edge k."""
        if k in self.inpad:
            return None, None
        t0, t1, L = self.edges[k]
        lids = self.order[k]
        i, n = lids.index(lid), len(lids)
        sp = self.spacing[k]
        reach = self.keep + 0.3          # the corner's own clearance, give or take its shape
        at0 = t0 < reach and lo <= t0 + i * sp + 1e-6
        at1 = (L - t1) < reach and hi >= t1 - (n - 1 - i) * sp - 1e-6
        return (k[0] if at0 else None), (k[1] if at1 else None)

    def _copper_for(self, net):
        """What a line of `net` keeps a centreline's distance (self.keep) off: every other
        net's pad and every area; and the board's edge, half a track off."""
        if not hasattr(self, "_cop"):
            self._cop = {}
        if net not in self._cop:
            pads = [p.geom for p in self.pads if p.net != net]
            g = unary_union(pads + [self.areas]) if pads or not self.areas.is_empty else Polygon()
            outside = self.m.outline.buffer(5.0).difference(self.m.inside)
            self._cop[net] = (g, outside)
        return self._cop[net]

    def _inflate(self, lid, pts, rounds=60, lines=None):
        """The band made legal against copper: wherever a segment comes nearer a pad or an
        area than a centreline may, a point is put in, pushed out to exactly that distance
        from the nearest point of the copper, and the band checked again - so a bend round a
        corner becomes an arc of as many points as it needs, whatever the corner's shape (an
        arc drawn round a corner chosen from the bend's edge, or from the nearest corner,
        was round the wrong one as often as not - the around and fan boards, 2026-10-11)."""
        from shapely.ops import nearest_points
        cop, outside = self._copper_for(self.lines[lid]["net"])
        # only the copper near the line: the whole board's, measured every round, made one
        # family on the crowd board take over ten minutes
        from shapely.geometry import box as _box
        x0, y0, x1, y1 = LineString(pts).bounds if len(pts) > 1 else (pts[0][0], pts[0][1], pts[0][0], pts[0][1])
        cop = cop.intersection(_box(x0 - 3.0, y0 - 3.0, x1 + 3.0, y1 + 3.0))
        need = self.keep - TOL / 2
        # other nets' lines are measured centreline to centreline, a pitch (no buffering:
        # buffering every neighbour's arcs each pass was the whole of the crowd board's time)
        need_l = self.width + self.clear + TOL / 2
        if lines is not None:
            lines = lines.intersection(_box(x0 - 3.0, y0 - 3.0, x1 + 3.0, y1 + 3.0))
        # the line's own terminal pads: inside them it is its own copper, not near anyone's
        ln = self.lines[lid]
        own = unary_union([self.pads[self.vpad[v]].geom for v in (ln["pa"], ln["pb"]) if v is not None])
        pts = list(pts)
        for _ in range(rounds):
            worst, at = 0.0, None
            for i, (a, b) in enumerate(zip(pts, pts[1:])):
                seg = LineString([a, b])
                if seg.length < 1e-9:
                    continue
                inside_own = own is not None and own.contains(seg)
                for g, nd in ((cop, need), (None if inside_own else lines, need_l)):
                    if g is None or g.is_empty:
                        continue
                    short = nd - seg.distance(g)
                    if short > worst + 1e-6:
                        worst, at = short, (i, seg, g, nd)
            if at is None:
                break
            i, seg, g, nd = at
            po, ps = nearest_points(g, seg)
            nx, ny = ps.x - po.x, ps.y - po.y
            nn = math.hypot(nx, ny)
            if nn < 1e-9:
                # the segment runs into the copper: push square to it, away from its middle
                a, b = pts[i], pts[i + 1]
                ux, uy = R2._unit(b[0] - a[0], b[1] - a[1])
                cx, cy = g.centroid.x, g.centroid.y
                nx, ny = -uy, ux
                if (ps.x - cx) * nx + (ps.y - cy) * ny < 0:
                    nx, ny = -nx, -ny
                nn = 1.0
            q = (po.x + nx / nn * (nd + TOL), po.y + ny / nn * (nd + TOL))
            if q in pts:
                break
            pts.insert(i + 1, q)
        return pts

    def _ends(self, lid, pts, others=None):
        """Each end pulled tight from its own pad: the line need only reach the pad, not its
        centre, so it starts at the point of the pad (a hair inside its edge) nearest the
        furthest point of the band a straight run from there reaches legally. Without this a
        line that left its pad by the wrong side doubled back round the pad's own corner -
        an acid trap (the around board, R at R1)."""
        cop, _ = self._copper_for(self.lines[lid]["net"])
        need = self.keep - TOL / 2
        from shapely.ops import nearest_points
        for end in (0, 1):
            seq = pts if end == 0 else pts[::-1]
            v = self.lines[lid]["pa" if end == 0 else "pb"]
            if v is None:
                continue            # a tee's end, on its host
            via = self.pads[self.vpad[v]].ref == VIA_REF
            # a via: the line on the other layer meets this one at its centre, so the end
            # stays there and only what follows it is pulled tight (a hook back into a via
            # was an acid trap - the scramble board's S3 and S5)
            pad = Point(self.xy[v]) if via else self.pads[self.vpad[v]].geom.buffer(-0.05)
            if pad.is_empty:
                continue
            best = None
            for j in range(min(len(seq) - 1, 12), 0, -1):
                tgt = Point(seq[j])
                q = nearest_points(pad, tgt)[0]
                run = LineString([(q.x, q.y), seq[j]])
                if run.length > 1e-6 and (cop.is_empty or run.distance(cop) >= need) and \
                        (others is None or run.distance(others) >= self.width + self.clear + TOL / 2):
                    best = [(q.x, q.y)] + seq[j:]
                    break
            if best:
                seq = best
            pts = seq if end == 0 else seq[::-1]
        return pts

    def _round(self, lid, pts, sharp=100.0):
        """Every bend sharper than `sharp` degrees (pcb.py check's acid trap is any under 90:
        a hairpin round a small pad - the stagemix board's KEY3) drawn as an arc round the
        nearest copper, at the distance the bend keeps from it; kept only if the arc keeps
        that distance from all copper."""
        from shapely.ops import nearest_points
        cop, _ = self._copper_for(self.lines[lid]["net"])
        if cop.is_empty or len(pts) < 3:
            return pts
        out = [pts[0]]
        for i in range(1, len(pts) - 1):
            A, V, C = out[-1], pts[i], pts[i + 1]
            u = R2._unit(A[0] - V[0], A[1] - V[1])
            w = R2._unit(C[0] - V[0], C[1] - V[1])
            ang = math.degrees(math.acos(max(-1.0, min(1.0, u[0] * w[0] + u[1] * w[1]))))
            if ang >= sharp:
                out.append(V)
                continue
            O = nearest_points(cop, Point(V))[0]
            o = (O.x, O.y)
            r = math.dist(o, V)
            if r < self.keep * 0.9 or math.dist(A, o) <= r + 1e-6 or math.dist(C, o) <= r + 1e-6:
                out.append(V)
                continue
            turn = _tri2(A, V, C)
            arc = _arc(o, r, _tangent(A, o, r, turn), _tangent(C, o, r, -turn), turn)
            if arc is None or LineString([A] + arc + [C]).distance(cop) < self.keep - TOL:
                out.append(V)
                continue
            out.extend(arc)
        out.append(pts[-1])
        return out

    def _corner_at(self, a, b, c):
        """The corner the path a -> b -> c bends round at b: the nearest corner to b on the
        inside of the turn, within reach of a pressed bend (a clearance off it, and a pitch
        for each line that could be nested inside); None if there is none. Read from the
        geometry, not from the edge the bend stands on - that edge's end is often another
        corner (the around board: R bent at pad S1's lower corner, the edge ran to R1's, and
        the line up S1's side cut in)."""
        turn = _tri2(a, b, c)
        if abs(turn) < 1e-9:
            return None
        reach = self.keep + self.pitch * 8
        best, bd = None, math.inf
        for j in self.corner_tree.query(Point(b).buffer(reach)):
            v = self.corner_ids[int(j)]
            q = self.xy[v]
            d = math.dist(q, b)
            # inside the turn: between the chord a -> c and the bend, on b's side of it
            if d < bd and d <= reach and _tri2(a, c, q) * _tri2(a, c, b) > 0:
                best, bd = v, d
        return best

    def _arcs(self, pts, bends):
        """Each run of bends round one corner drawn as an arc round it at the radius the bend
        stands at, from the tangent off the point before to the tangent toward the point after;
        the arc's points stand just outside the circle, so its chords never cut inside."""
        bends = [None] + [self._corner_at(pts[i - 1], pts[i], pts[i + 1]) for i in range(1, len(pts) - 1)] + [None]
        out = [pts[0]]
        j = 1
        n = len(pts)
        while j < n - 1:
            v = bends[j]
            if v is None:
                out.append(pts[j])
                j += 1
                continue
            j2 = j
            while j2 + 1 < n - 1 and bends[j2 + 1] == v:
                j2 += 1
            c = self.xy[v]
            r = max(math.dist(pts[i], c) for i in range(j, j2 + 1))
            A, C = out[-1], pts[j2 + 1]
            if math.dist(A, c) <= r + 1e-6 or math.dist(C, c) <= r + 1e-6:
                out.extend(pts[j:j2 + 1])
                j = j2 + 1
                continue
            turn = _tri2(A, pts[j], C)          # > 0: a left turn, the vertex on the left
            t_in = _tangent(A, c, r, turn)
            t_out = _tangent(C, c, r, -turn)
            arc = _arc(c, r, t_in, t_out, turn)
            if arc is None:                     # more than a half turn: not a bend round c
                out.extend(pts[j:j2 + 1])
            else:
                out.extend(arc)
            j = j2 + 1
        out.append(pts[-1])
        return out

    def _widen(self, paths):
        """Measure each pair of neighbours (adjacent in an edge's order); where one is under a
        pitch from the other, widen the spacing on every edge they stand adjacent on. True if
        anything was widened."""
        need = self.width + self.clear + TOL / 2
        geo = {lid: LineString(p) for lid, p in paths.items()}
        widened = False
        seen = set()
        for k, lids in self.order.items():
            for a, b in zip(lids, lids[1:]):
                if self.lines[a]["net"] == self.lines[b]["net"]:
                    continue
                pair = (min(a, b), max(a, b))
                if pair in seen:
                    continue
                seen.add(pair)
                d = geo[a].distance(geo[b])
                if d < need:
                    grow = (need - d) + TOL
                    for k2, l2 in self.order.items():
                        for x, y in zip(l2, l2[1:]):
                            if {x, y} == {a, b}:
                                t0, t1, _ = self.edges[k2]
                                cap = (t1 - t0) / max(1, len(l2) - 1)
                                self.spacing[k2] = min(self.spacing[k2] + grow, max(cap, self.spacing[k2]))
                    widened = True
        return widened


class _EdgeRef:
    """A chord's end on an edge: the edge and the line, whose place in the edge's order is
    read when it is needed (lines inserted beside it move it)."""
    __slots__ = ("k", "lid")

    def __init__(self, k, lid):
        self.k, self.lid = k, lid


def _cross(a, b, c, d):
    """Whether segments a-b and c-d cross properly (touching ends do not count)."""
    d1, d2 = _tri2(c, d, a), _tri2(c, d, b)
    d3, d4 = _tri2(a, b, c), _tri2(a, b, d)
    return d1 * d2 < 0 and d3 * d4 < 0


def _meet(a, b, c, d):
    """Where lines a-b and c-d meet (they are known to cross)."""
    den = (b[0] - a[0]) * (d[1] - c[1]) - (b[1] - a[1]) * (d[0] - c[0])
    if abs(den) < 1e-12:
        return a
    t = ((c[0] - a[0]) * (d[1] - c[1]) - (c[1] - a[1]) * (d[0] - c[0])) / den
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def _tri2(a, b, c):
    """Twice the signed area of a, b, c."""
    return (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])


def _tangent(p, c, r, turn):
    """The point where a line from p touches the circle (c, r), on the side that keeps the
    circle on the turn's inside (turn > 0: the circle on the left of p -> tangent)."""
    d = math.dist(p, c)
    base = math.atan2(p[1] - c[1], p[0] - c[0])
    phi = math.acos(max(-1.0, min(1.0, r / d)))
    cands = [base + phi, base - phi]
    best = None
    for a in cands:
        t = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
        side = _tri2(p, t, c)                    # > 0: c on the left of p -> t
        if (side > 0) == (turn > 0):
            best = t
    return best or (c[0] + r * math.cos(cands[0]), c[1] + r * math.sin(cands[0]))


def _arc(c, r, t_in, t_out, turn):
    """Points round (c, r) from t_in to t_out, turning with the path (turn > 0: the path
    turns left, so round the circle clockwise as seen from c... the short way that keeps c
    inside the turn). Points stand at r / cos(step / 2), so every chord is outside the circle."""
    a0 = math.atan2(t_in[1] - c[1], t_in[0] - c[0])
    a1 = math.atan2(t_out[1] - c[1], t_out[0] - c[0])
    # the path turns left round a centre on its left: it goes round the circle
    # counter-clockwise
    if turn > 0:
        while a1 < a0:
            a1 += 2 * math.pi
    else:
        while a1 > a0:
            a1 -= 2 * math.pi
    span = a1 - a0
    if abs(span) > math.pi + 1e-6:
        return None
    n = max(1, int(math.ceil(abs(span) / ARC_STEP)))
    ro = r / math.cos(abs(span) / n / 2)
    out = [t_in]
    for i in range(1, n):
        a = a0 + span * i / n
        out.append((c[0] + ro * math.cos(a), c[1] + ro * math.sin(a)))
    out.append(t_out)
    return out


def _funnel(portals, verts):
    """The simple stupid funnel algorithm (Mononen): the shortest path through portals given
    as (left, right) pairs, the first and last a single point each. Returns (points, bends):
    the vertex each point bends round, read from `verts` ((left's, right's) per portal)."""
    pts, bends = [portals[0][0]], [None]
    apex, left, right = portals[0][0], portals[0][0], portals[0][1]
    ai = li = ri = 0
    i = 1
    n = len(portals)
    while i < n:
        pl, pr = portals[i]
        if _tri2(apex, right, pr) >= 0:
            if apex == right or _tri2(apex, left, pr) < 0:
                right, ri = pr, i
            else:
                pts.append(left)
                bends.append(verts[li][0])
                apex, ai = left, li
                left, right = apex, apex
                li = ri = ai
                i = ai + 1
                continue
        if _tri2(apex, left, pl) <= 0:
            if apex == left or _tri2(apex, right, pl) > 0:
                left, li = pl, i
            else:
                pts.append(right)
                bends.append(verts[ri][1])
                apex, ai = right, ri
                left, right = apex, apex
                li = ri = ai
                i = ai + 1
                continue
        i += 1
    if pts[-1] != portals[-1][0]:
        pts.append(portals[-1][0])
        bends.append(None)
    return pts, bends


def route_layer(model, layer, pairs, **kw):
    """Plan and draw two-pad nets on one layer. pairs: [(net, pad, pad)] (pcb_route2 Pads),
    routed in the order given. Returns (runs, failed, map): pcb_route2 Runs with exact points,
    and [net] not placed."""
    mp = Map(model, layer, [n for n, _, _ in pairs], **kw)
    idx = {id(p): i for i, p in enumerate(mp.pads)}
    failed, lids = [], {}
    for j, (net, a, b) in enumerate(pairs):
        pending = [(x.centre, y.centre) for _, x, y in pairs[j + 1:]]
        lid = mp.route(net, idx[id(a)], idx[id(b)], pending=pending)
        if lid is None:
            failed.append(net)
        else:
            lids[lid] = net
    paths = mp.geometry()
    runs = []
    for lid, net in lids.items():
        r = R2.Run(net, [(0, 0, layer)], model.rules.width(net), via=model.rules.via_size(net))
        r.pts = _clean([(round(float(x), 4), round(float(y), 4), layer) for x, y in paths[lid]])
        runs.append(r)
    return runs, failed, mp


# ------------------------------------------------------------------ T2: layers and vias

_VIAS = 0


def _via_pad(model, net, xy):
    d, drill = model.rules.via_size(net)
    global _VIAS
    _VIAS += 1
    return R2.Pad(ref=VIA_REF, num=str(_VIAS), net=net, layers=set(range(model.nl)),
                  geom=Point(xy).buffer(d / 2, quad_segs=8), centre=xy, smd=False, drill=drill)


def _via_ok(model, net, xy, placed, layers):
    """Whether a via of `net` may stand at xy: inside the board, clear of every other net's
    copper and every hole and keep-out on the layers it joins, and of the vias placed."""
    R = model.rules
    d, _ = R.via_size(net)
    g = Point(xy).buffer(d / 2)
    if not model.inside.contains(g):
        return False
    for e in model.index.query(g.buffer(1.0).bounds):
        if e.kind == "keepout" and not (e.vias or e.tracks):
            continue
        if e.net == net and e.kind != "keepout":
            continue
        gap = R.hole_to_hole if e.kind == "hole" else R.gap(net, e.net)
        if set(e.layers) & set(layers) and e.geom.distance(g) < gap + TOL:
            return False
    for p in model.pads:
        if p.net != net and p.geom.distance(g) < R.gap(net, p.net) + TOL:
            return False
        # and off its own net's SMD pads by pcb_route2's own-pad gap (fits: via-on-pad)
        if p.net == net and p.smd and p.geom.distance(g) < R2.OWN_PAD_GAP + TOL:
            return False
    for q in placed:
        if q.net != net and q.geom.distance(g) < R.gap(net, q.net) + TOL:
            return False
        if q.geom.distance(g) < R.hole_to_hole + TOL:
            return False
    return True


def _reach(model, net, pad, layer, placed=()):
    """The free room `pad` can reach on `layer` with a track of `net`: the board's inside
    less every other net's copper on that layer (pads, tracks, vias, keep-outs, holes, the
    vias placed so far) grown by the clearance and half a track - the pieces of it the pad
    touches. A via for the pad must stand in it: placed by distance alone it went where the
    pad could not reach (the stagemix board's U1.2, walled in by an earlier family's keys)."""
    R = model.rules
    w = R.width(net)
    keep = R.clear(net) + w / 2 + TOL
    obs = []
    for e in model.index.e.values():
        if layer not in set(e.layers) or e.net == net:
            continue
        if (e.kind == "keepout" and e.tracks) or e.kind in ("hole", "track", "via", "pad") \
                or (e.kind == "reserve" and net not in (e.family or ())):
            obs.append(e.geom)
    obs += [p.geom for p in model.pads if p.net != net and layer in set(p.layers)]
    obs += [q.geom for q in placed if q.net != net]
    free = model.inside.difference(unary_union(obs).buffer(keep)) if obs else model.inside
    near = pad.geom.buffer(keep + 0.05)
    return unary_union([g for g in _polys(free) if g.intersects(near)])


def _place_via(model, net, near, toward, placed, layers, rmin=None, region=None):
    """A legal via of `net` as near `near` as it can stand, on the side toward `toward`:
    rings of candidates, nearest first, each ring's best by its distance to `toward`. With
    `region`, only where a track can reach it (_reach)."""
    d, _ = model.rules.via_size(net)
    r0 = rmin if rmin is not None else d / 2 + model.rules.clearance + 0.3
    for ring_ in range(12):
        r = r0 + ring_ * 0.25
        cands = []
        for j in range(24):
            a = 2 * math.pi * j / 24
            q = (near[0] + r * math.cos(a), near[1] + r * math.sin(a))
            if region is not None and not region.contains(Point(q)):
                continue
            if _via_ok(model, net, q, placed, layers):
                cands.append((math.dist(q, toward), q))
        if cands:
            return min(cands)[1]
    return None


def _mst(points):
    """Prim's tree over points [(key, (x, y))]: [(key, key)], each edge joining a point to
    the nearest one already in the tree."""
    if len(points) < 2:
        return []
    inn, rest, out = [points[0]], list(points[1:]), []
    while rest:
        a, b = min(((a, b) for a in inn for b in rest), key=lambda ab: math.dist(ab[0][1], ab[1][1]))
        out.append((a[0], b[0]))
        inn.append(b)
        rest.remove(b)
    return out


def _colour(nets, xg, allowed, vias_on, start, passes=12, dear=None):
    """Layers for nets from their crossing graph xg {net: {other: count}}: each net the layer
    with the fewest crossings with nets on the same layer (ten each), then the fewest vias
    (three each), passes until nothing changes - a min-conflict 2-colouring that keeps what
    it was given where that is as good."""
    col = dict(start)
    for _ in range(passes):
        moved = False
        for n in sorted(nets, key=lambda n: (-sum(xg.get(n, {}).values()), n)):
            if not allowed[n]:
                continue
            def cost(L):
                same = sum(c for m_, c in xg.get(n, {}).items() if col.get(m_) == L)
                # a class's layer_cost (the analog nets' B.Cu at 6x): five per unit over one
                extra = 5.0 * (dear(n, L) - 1.0) if dear else 0.0
                return (same * 10 + vias_on(n, L) * 3 + extra, 0 if L == col.get(n) else 1, L)
            best = min(allowed[n], key=cost)
            if best != col.get(n):
                col[n], moved = best, True
        if not moved:
            break
    return col


def plan_layers(model, nets, pads, layers, allowed, start, rounds=6, log=None, later=()):
    """THE NEGOTIATION (ADR 0029 step 3): every net planned in one map of all layers at once
    (Map(layer=None)), where a line may cross another net's - cheaply if the two are on
    different layers as things stand, dearly (and dearer each round they do it again) if on
    the same - then the layers chosen again from the crossings planned (_colour). Plan and
    layers settle together. Returns the layers of the round with the fewest same-layer
    crossings (then the fewest nets unplanned)."""
    log = log if log is not None else []
    hist = {}
    col = dict(start)
    best = None
    vias_on = lambda n, L: sum(1 for p in pads[n] if L not in p.layers)
    future = [(model.pads_of(n)[i].centre, model.pads_of(n)[j].centre) for n in later
              for i, j in _mst([(k, p.centre) for k, p in enumerate(model.pads_of(n))])]
    order = sorted(nets, key=lambda n: (-sum(math.dist(a.centre, b.centre) for a in pads[n] for b in pads[n]), n))
    for rnd in range(rounds):
        mp = Map(model, None, nets, lanes=len(layers), narrow=True, layers=layers)
        idx = {id(p): i for i, p in enumerate(mp.pads)}

        def price(a, b):
            k = frozenset((a, b))
            return (1.0 if col.get(a) != col.get(b) else 8.0) + hist.get(k, 0.0)
        lids, unplanned = {}, []
        for n in order:
            ends = pads[n]
            tree = _mst([(k, e.centre) for k, e in enumerate(ends)])
            for q, (i, j) in enumerate(tree):
                if id(ends[j]) not in idx or id(ends[i]) not in idx:
                    unplanned.append(n)
                    break
                lid = mp.route(n, idx[id(ends[j])], idx[id(ends[i])], tee=q > 0, cross=price, pending=future)
                if lid is None:
                    unplanned.append(n)
                    break
                lids.setdefault(n, []).append(lid)
        xg = {}
        for n, ls in lids.items():
            for l in ls:
                for l2 in mp.crossed(l):
                    m_ = mp.lines[l2]["net"]
                    xg.setdefault(n, {})[m_] = xg.get(n, {}).get(m_, 0) + 1
        col = _colour(nets, xg, allowed, vias_on, col,
                      dear=lambda n, L: model.rules.layer_cost(n, model.layer_names[L]))
        same = sum(c for n, d in xg.items() for m_, c in d.items() if col.get(n) == col.get(m_)) // 2
        total = sum(c for d in xg.values() for c in d.values()) // 2
        log.append(f"topo plan round {rnd + 1}: crossings {total}, on one layer {same}; unplanned {sorted(set(unplanned))}")
        key = (same, len(set(unplanned)))
        if best is None or key < best[0]:
            best = (key, dict(col), mp, dict(lids))
        if key == (0, 0):
            break
        for n, d in xg.items():
            for m_, c in d.items():
                if col.get(n) == col.get(m_):
                    k = frozenset((n, m_))
                    hist[k] = hist.get(k, 0.0) + 4.0 * c
        order = sorted(nets, key=lambda n: (-sum(c for m_, c in xg.get(n, {}).items() if col.get(m_) == col.get(n)), n))
    # the guides: the best round's lines drawn (in the plan map, every layer's copper in the
    # way) - one MultiLineString of each net's lines
    key, col, mp, lids = best
    paths = mp.geometry(passes=3, rounds=1)
    from shapely.geometry import MultiLineString
    guides = {n: MultiLineString([paths[l] for l in ls if len(paths[l]) > 1]) for n, ls in lids.items()}
    plan_layers.last = {"same": key[0], "unplanned": key[1]}
    return col, guides


def plan(model, nets, layers=None, log=None, later=(), rounds=6):
    """THE PLAN alone (ADR 0029 as amended 2026-10-11): every net of `nets` planned together,
    crossings negotiated, a layer chosen for each net. Returns {"layer": {net: layer index},
    "guide": {net: MultiLineString}} - the grid router lays the copper along it
    (pcb_route2.Router.stage, engine: topo)."""
    log = log if log is not None else []
    pads = {n: model.pads_of(n) for n in nets}
    many = [n for n in nets if len(pads[n]) >= 2]
    if layers is None:
        layers = sorted({L for n in many for L in model.track_layers(n)})
    allowed = {n: [L for L in model.track_layers(n) if L in layers] for n in many}
    if not many:
        return {"layer": {}, "guide": {}, "same": 0, "unplanned": 0, "length": 0.0, "score": 0.0}
    aw = {n: [(pads[n][i].centre, pads[n][j].centre)
              for i, j in _mst([(k, p.centre) for k, p in enumerate(pads[n])])] for n in many}
    adj = {n: {m_ for m_ in many if m_ != n and any(_cross(*e, *f) for e in aw[n] for f in aw[m_])}
           for n in many}
    start = {}
    for n in sorted(many, key=lambda n: (-len(adj[n]), n)):
        if allowed[n]:
            start[n] = min(allowed[n], key=lambda L: (sum(1 for m_ in adj[n] if start.get(m_) == L) * 10
                                                      + sum(1 for p in pads[n] if L not in p.layers) * 3, L))
    if len(layers) < 2:
        col = start
        mp = Map(model, layers[0], many, narrow=True)
        idx = {id(p): i for i, p in enumerate(mp.pads)}
        lids = {}
        for n in many:
            tree = _mst([(k, e.centre) for k, e in enumerate(pads[n])])
            for q, (i, j) in enumerate(tree):
                if id(pads[n][j]) in idx and id(pads[n][i]) in idx:
                    lid = mp.route(n, idx[id(pads[n][j])], idx[id(pads[n][i])], tee=q > 0)
                    if lid is not None:
                        lids.setdefault(n, []).append(lid)
        paths = mp.geometry(passes=3, rounds=1)
        from shapely.geometry import MultiLineString
        guides = {n: MultiLineString([paths[l] for l in ls if len(paths[l]) > 1]) for n, ls in lids.items()}
        un = len(set(many) - set(guides))
        length = sum(g.length for g in guides.values())
        return {"layer": col, "guide": guides, "same": 0, "unplanned": un, "length": length,
                "score": un * 100.0 + length}
    col, guides = plan_layers(model, many, pads, layers, allowed, start, rounds=rounds, log=log, later=later)
    last = getattr(plan_layers, "last", {"same": 0, "unplanned": 0})
    length = sum(g.length for g in guides.values())
    return {"layer": col, "guide": guides, "same": last["same"], "unplanned": last["unplanned"] + len(set(many) - set(guides)),
            "length": length, "score": last["same"] * 10.0 + (last["unplanned"] + len(set(many) - set(guides))) * 100.0 + length}


def route_board(model, nets, layers=None, rounds=4, log=None, later=()):
    """Nets on the board's signal layers (T2, T3): each net to one layer - fewest crossings
    of its tree's straight airwires with nets on the same layer, then fewest vias - a via
    beside each pad not on that layer, the net's pads (or their vias) joined by a tree of
    two-pad lines; then each layer planned by the T1 planner. A net that fails moves to
    another layer and the board is planned again, up to `rounds`. `later`: nets of families
    still to come - their straight airwires are priced as this family's pending ones are, so
    a family does not wall in the next (the stagemix board: the keys wrapped U1 and the last
    family's SCK could not leave its pin). Returns (runs, failed, report): one Run per line,
    and one per via (its two layers at one point)."""
    import copy
    log = log if log is not None else []
    pads = {n: model.pads_of(n) for n in nets}
    many = [n for n in nets if len(pads[n]) >= 2]
    if layers is None:
        layers = sorted({L for n in many for L in model.track_layers(n)})
    allowed = {n: [L for L in model.track_layers(n) if L in layers] for n in many}
    aw = {n: [(pads[n][i].centre, pads[n][j].centre)
              for i, j in _mst([(k, p.centre) for k, p in enumerate(pads[n])])] for n in many}
    adj = {n: {m_ for m_ in many if m_ != n and any(_cross(*e, *f) for e in aw[n] for f in aw[m_])}
           for n in many}
    future = [(model.pads_of(n)[i].centre, model.pads_of(n)[j].centre) for n in later
              for i, j in _mst([(k, p.centre) for k, p in enumerate(model.pads_of(n))])]
    forced, guides = {}, {}
    if len(layers) > 1 and len(many) > 1:
        start = {}
        for n in sorted(many, key=lambda n: (-len(adj[n]), n)):
            if allowed[n]:
                start[n] = min(allowed[n], key=lambda L: (sum(1 for m_ in adj[n] if start.get(m_) == L) * 10
                                                          + sum(1 for p in pads[n] if L not in p.layers) * 3, L))
        forced, guides = plan_layers(model, many, pads, layers, allowed, start, log=log, later=later)
    failed, runs = list(nets), []
    best = None
    for rnd in range(rounds):
        # 1. layers: most-crossed first; a layer its pads are on saves vias
        assign = {}
        for n in sorted(many, key=lambda n: (-len(adj[n]), n)):
            if n in forced:
                assign[n] = forced[n]
                continue
            def cost(L):
                same = sum(1 for m_ in adj[n] if assign.get(m_) == L)
                vias = sum(1 for p in pads[n] if L not in p.layers)
                return (same * 10 + vias * 3, L)
            assign[n] = min(allowed[n], key=cost) if allowed[n] else None
        # 2. vias, then each net's tree
        placed, pieces, stubs = [], {}, {}
        for n in many:
            L = assign[n]
            if L is None:
                continue
            centre = (sum(p.centre[0] for p in pads[n]) / len(pads[n]), sum(p.centre[1] for p in pads[n]) / len(pads[n]))
            ends, ok = [], True
            for p in pads[n]:
                if L in p.layers:
                    ends.append(p)
                    continue
                pl = next((x for x in sorted(p.layers) if x in allowed[n]), None)
                xy = _place_via(model, n, p.centre, centre, placed, layers,
                                region=_reach(model, n, p, pl, placed)) if pl is not None else None
                if xy is None:
                    ok = False
                    break
                v = _via_pad(model, n, xy)
                placed.append(v)
                stubs.setdefault(n, []).append((pl, p, v))
                ends.append(v)
            if not ok:
                continue
            # the tree in Prim's order: its first line pad to pad, then each new pad's line
            # from that pad, ending on the tree where it first comes beside it (a tee) or at
            # its nearest pad
            tree = _mst([(k, e.centre) for k, e in enumerate(ends)])
            pieces[n] = [(L, ends[j], ends[i], q > 0) for q, (i, j) in enumerate(tree)] + \
                [(pl, p, v, False) for (pl, p, v) in stubs.get(n, [])]
        m2 = copy.copy(model)
        m2.pads = list(model.pads) + placed
        # 3. each layer
        got, bad = {}, set()
        for L in layers:
            # net by net, the longest first; each net's pieces in their tree order
            span = {n: sum(math.dist(x.centre, y.centre) for (_, x, y, _) in ps) for n, ps in pieces.items()}
            pairs = [(n, x, y, t) for n in sorted(pieces, key=lambda n: (-span[n], n))
                     for (Lp, x, y, t) in pieces[n] if Lp == L]
            if not pairs:
                continue
            mp = Map(m2, L, sorted({n for n, _, _, _ in pairs}))
            idx = {id(p): i for i, p in enumerate(mp.pads)}
            lids = {}
            for j, (n, x, y, t) in enumerate(pairs):
                pending = [(u.centre, w.centre) for n2, u, w, _ in pairs[j + 1:] if n2 != n] + future
                # a via stub (pad to its via) follows no guide: the plan had no via
                g_ = guides.get(n) if not (x.ref == VIA_REF) != (y.ref == VIA_REF) else None
                lid = mp.route(n, idx[id(x)], idx[id(y)], pending=pending, tee=t,
                               guide=g_ if g_ is not None and not g_.is_empty else None)
                if lid is None:
                    bad.add(n)
                    log.append(f"topo: {n} on {model.layer_names[L]}: no way from {x.ref}.{x.num} to {y.ref}.{y.num}"
                               + (" (or its tree)" if t else ""))
                else:
                    lids[lid] = (n, x, y)
            paths = mp.geometry()
            for lid, (n, x, y) in lids.items():
                got[(n, L, id(x), id(y))] = paths[lid]
        failed = sorted(set(nets) - set(pieces)) + sorted(bad)
        # THE CHECK, in the planner: each net's runs held to fits() against everything laid
        # before them (earlier families, and this round's nets already passed); a net that
        # does not fit goes back to be planned again like one that was not planned. The
        # geometry can only spend the room the plan gave it - where the plan gave too little
        # a line was pushed off one neighbour into another (the crowd board: IO1 into U6.1)
        built = _build(model, pieces, got, placed, failed, layers)
        unfit = _verify(model, built)
        for n, why in sorted(unfit.items()):
            log.append(f"topo: {n} drawn but does not fit - {why}")
        failed = sorted(set(failed) | set(unfit))
        log.append(f"topo round {rnd + 1}: layers {dict(sorted(assign.items()))}; vias {len(placed)}; failed {failed}")
        if best is None or len(failed) < len(best[1]):
            best = (built, failed, dict(assign), len(placed))
        if not failed or rnd == rounds - 1:
            break
        for n in failed:
            if n in many and allowed[n]:
                others = [x for x in allowed[n] if x != assign.get(n)]
                if others:
                    forced[n] = others[(rnd // 1) % len(others)]
    built, failed, assign, nvias = best
    runs = [r for n, rs in built.items() if n not in failed for r in rs]
    return runs, failed, {"assign": assign, "vias": nvias, "split": [], "log": log}


def _sharpest(pts):
    """The sharpest bend of a polyline, in degrees between its two legs (180 = straight)."""
    worst = 180.0
    for a, v, c in zip(pts, pts[1:], pts[2:]):
        u = R2._unit(a[0] - v[0], a[1] - v[1])
        w = R2._unit(c[0] - v[0], c[1] - v[1])
        if u == (0.0, 0.0) or w == (0.0, 0.0):
            continue
        worst = min(worst, math.degrees(math.acos(max(-1.0, min(1.0, u[0] * w[0] + u[1] * w[1])))))
    return worst


def _clean(pts, eps=1e-3):
    """A run's points with every one within `eps` of the one kept before it dropped (the last
    kept always): two points 1e-4 apart wrote a zero-length track, whose direction is
    noise - an acid trap at 0 deg (the crowd board's IO2)."""
    out = []
    for i, p in enumerate(pts):
        if out and math.dist(p[:2], out[-1][:2]) < eps:
            if i == len(pts) - 1:
                out[-1] = p
            continue
        out.append(p)
    return out


def _build(model, pieces, got, placed, failed, layers):
    """{net: [Run]} - each planned line a Run, each via a Run of its two layers at a point."""
    R = model.rules
    out = {}
    for n, ps in pieces.items():
        if n in failed:
            continue
        for (L, x, y, _) in ps:
            path = got.get((n, L, id(x), id(y)))
            if path is None:
                continue
            r = R2.Run(n, [(0, 0, 0)], R.width(n), via=R.via_size(n))
            r.pts = _clean([(round(float(px), 4), round(float(py), 4), L) for px, py in path])
            out.setdefault(n, []).append(r)
    for v in placed:
        if v.net in failed or v.net not in pieces:
            continue
        r = R2.Run(v.net, [(0, 0, 0)], R.width(v.net), via=R.via_size(v.net))
        x, y = round(float(v.centre[0]), 4), round(float(v.centre[1]), 4)
        r.pts = [(x, y, min(layers)), (x, y, max(layers))]
        out.setdefault(v.net, []).append(r)
    return out


def _verify(model, built):
    """{net: why} for each net whose runs do not fit, laid net by net (longest first) over
    what is already on the board, then all taken up again - the model is left as it was."""
    laid, bad = [], {}
    for n in sorted(built, key=lambda n: -sum(r.length() for r in built[n])):
        why = None
        for r in built[n]:
            f = R2.fits(r, model)
            if f:
                why = f"{f[0][0]} at ({f[0][1][0]:.2f}, {f[0][1][1]:.2f})"
                break
        if why:
            bad[n] = why
            continue
        for r in built[n]:
            R2.lay(r, model)
            laid.append(r)
    for r in laid:
        R2.unlay(r, model)
    return bad
