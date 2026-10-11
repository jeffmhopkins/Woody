#!/usr/bin/env python3
"""pcb_topo - the topological router (ADR 0029, #47).

A line is planned before it is drawn. Each copper layer is a constrained Delaunay
triangulation of the room to route in (Shewchuk's `triangle`): its vertices are the pads'
centres, the corners of what no track may cross (keep-outs, holes, locked copper, the
board's edge) and the points the quality refinement adds. A route is the path of triangle
edges a line crosses and, on each edge, its PLACE IN THAT EDGE'S ORDER of lines. A new line
takes a place between two lines already on an edge - it squeezes between them - and nothing
is re-laid, because nothing is laid yet: the lines beyond it are pushed over by one pitch
when the geometry is drawn. That is the owner's "push traces out of the way and merge
between traces" (2026-10-11), here a fact of the plan rather than a repair after a failure.

Inside one triangle every line is a chord between two points of the triangle's boundary,
and two lines on one layer cross exactly when their chords interleave; the search refuses
a place whose chord would cross (T1: one layer - T2 prices the crossing and resolves it
with a via). An edge's CAPACITY is how many centrelines fit along its free part (its length
less what the obstacles at either end, grown by clearance and half a track, take).

Geometry last: each line is the shortest path through its PORTALS - on each edge it crosses,
the stretch its place in the order leaves it - by the funnel algorithm, a rubber band held
off each vertex by that vertex's clearance and the lines ordered inside it. Lines that cross
an edge on the slant are spaced wider along it (pitch / sin of the angle), so they keep a
pitch apart square to themselves. The result is pcb_route2 Runs: the grid router's fits(),
write() and KiCad's DRC judge them exactly as they judge its own.

T1 (this file): one layer, two-pad nets. T2 layers and vias, T3 nets of more pads, T4 the
stage's engine option, T5 the main board (#47).
"""
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

MARGIN = 0.08               # mm round a pad: a chord round a vertex sags inside the circle its ends are on
SNAP = 0.025               # mm round everything: Run puts every point on pcb_route2's 0.05 lattice


def _polys(g):
    if g.is_empty:
        return []
    return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > 1e-6]


class Map:
    """One layer of a pcb_route2 Model, triangulated. `nets`: the nets to be routed here -
    their pads are terminals; every other pad, hole, keep-out and track on the layer is an
    obstacle (pads are vertices too: a line passes them on one side or the other)."""

    def __init__(self, model, layer, nets, pitch=None, width=None, quality=None, max_area=None):
        R = model.rules
        self.m, self.layer = model, layer
        self.nets = set(nets)
        self.width = width or max(R.width(n) for n in nets)
        self.clear = max([R.clear(n) for n in nets] + [R.clearance])
        self.pitch = pitch or (self.width + self.clear + SNAP)
        # obstacles that are areas (no line passes through them): keep-outs, holes, locked
        # copper on this layer, and the outside of the board
        areas = []
        for e in model.index.e.values():
            if layer not in set(e.layers):
                continue
            if e.kind == "keepout" and e.tracks:
                areas.append(e.geom)
            elif e.kind == "hole":
                areas.append(e.geom)
            elif e.kind in ("track", "via") and e.net not in self.nets:
                areas.append(e.geom)
        self.areas = unary_union(areas) if areas else Polygon()
        self.room = model.inside.difference(self.areas.buffer(self.clear + self.width / 2))
        # the pads on this layer: every one a vertex
        self.pads = [p for p in model.pads if layer in set(p.layers)]
        verts, segs, holes = [], [], []
        for p in self.pads:
            verts.append(p.centre)
        self.npad = len(verts)
        # a ring of points round each pad, just outside what it keeps clear and in its own
        # shape (a circle missed a square pad's corners: a chord between two bends 30 deg
        # apart cut 0.16 mm into the corner's clearance): the edges from the pad to its
        # ring are where lines bend round it, every 30 deg of each corner's arc
        # The pad is joined to every point of its ring by a constrained edge - a fan - so a
        # line near a pad crosses those edges, and bends where each one's free part starts
        # (without the fan, Delaunay joined ring points across a corner and a line cut it)
        for i, p in enumerate(self.pads):
            grown = p.geom.buffer(self.clear + self.width / 2 + MARGIN + 0.05, quad_segs=3)
            for q in list(grown.exterior.coords)[:-1]:
                if model.inside.contains(Point(q)) and not self.areas.contains(Point(q)):
                    segs.append((i, len(verts)))
                    verts.append(q)
        # the outline and the area obstacles as constrained segments (their simplified
        # boundaries), the area obstacles as holes
        def ring(coords):
            coords = list(coords)[:-1]
            i0 = len(verts)
            verts.extend(coords)
            segs.extend((i0 + k, i0 + (k + 1) % len(coords)) for k in range(len(coords)))
        # the free room - the board's inside less the area obstacles - as rings: each
        # polygon's outside and its holes (a keep-out to the board's edge is a bite out of
        # the outside, not a hole; one in the middle is a hole)
        room = model.inside.difference(self.areas).simplify(0.02)
        for poly in _polys(room):
            ring(poly.exterior.coords)
            for hole in poly.interiors:
                ring(hole.coords)
                holes.append(Polygon(hole).representative_point().coords[0])
        A = {"vertices": np.array(verts, dtype=float), "segments": np.array(segs, dtype=int)}
        if holes:
            A["holes"] = np.array(holes, dtype=float)
        # no quality refinement by default: its Steiner points went inside the pads' rings
        # (at a square pad's corners) and walled the pad in - the rings do its work there
        flags = "p" + (f"q{quality}" if quality else "") + (f"a{max_area}" if max_area else "")
        T = triangle.triangulate(A, flags)
        self.xy = [tuple(v) for v in T["vertices"]]
        self.tris = [tuple(int(i) for i in t) for t in T["triangles"]]
        # the pads keep their index (triangle keeps the input vertices first, in order)
        self.pad_of = {i: self.pads[i] for i in range(self.npad)}
        self.vtri = {}
        self.edges, self.etris = {}, {}
        for ti, (a, b, c) in enumerate(self.tris):
            for v in (a, b, c):
                self.vtri.setdefault(v, []).append(ti)
            for u, v in ((a, b), (b, c), (c, a)):
                k = (min(u, v), max(u, v))
                self.etris.setdefault(k, []).append(ti)
        for k, ts in self.etris.items():
            if len(ts) == 2:
                self.edges[k] = self._free(k)
        self.order = {k: [] for k in self.edges}        # line ids, from k[0]'s end to k[1]'s
        self.chords = {ti: [] for ti in range(len(self.tris))}   # (line, end, end)
        self.lines = {}                                  # id: {net, ends, path}

    # ---------------------------------------------------------------- the edges

    def _blockers(self, net=None):
        if not hasattr(self, "_blk"):
            pads = unary_union([p.geom for p in self.pads]).buffer(self.clear + self.width / 2 + MARGIN)
            areas = self.areas.buffer(self.clear + self.width / 2 + SNAP)
            outside = self.m.outline.buffer(5.0).difference(self.m.inside).buffer(self.width / 2 + SNAP)
            self._blk = unary_union([pads, areas, outside])
        return self._blk

    def _free(self, k):
        """(t0, t1, length): the free stretch of edge k, as distances from its first end."""
        a, b = self.xy[k[0]], self.xy[k[1]]
        seg = LineString([a, b])
        L = seg.length
        free = seg.difference(self._blockers())
        pieces = [g for g in getattr(free, "geoms", [free]) if g.geom_type == "LineString" and g.length > 0] \
            if not free.is_empty else []
        if not pieces:
            # a single point free (or none): room for nothing unless it is exactly zero long
            return (0.0, -1.0, L)
        g = max(pieces, key=lambda g: g.length)
        t0 = seg.project(Point(g.coords[0]))
        t1 = seg.project(Point(g.coords[-1]))
        return (min(t0, t1), max(t0, t1), L)

    def capacity(self, k, pitch=None):
        t0, t1, _ = self.edges[k]
        if t1 < t0:
            return 0
        return int(math.floor((t1 - t0) / (pitch or self.pitch) + 1e-9)) + 1

    def _at(self, k, frac):
        a, b = self.xy[k[0]], self.xy[k[1]]
        return (a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac)

    def _slot_point(self, k, s):
        """Where a new line in slot s of edge k (s lines on k[0]'s side of it) would cross."""
        t0, t1, L = self.edges[k]
        n = len(self.order[k]) + 1
        t = t0 + (t1 - t0) * (s + 0.5) / n if t1 > t0 else (t0 + t1) / 2
        return self._at(k, t / L if L else 0.5)

    # ---------------------------------------------------------------- the chords

    def _bpos(self, ti, end, new=False):
        """Where `end` - ('v', vertex), ('e', edge, place) or an _EdgeRef - sits on triangle
        ti's boundary, as a number round it (vertex a 0, edge ab (0, 1), b 1, ...). An edge's
        k lines stand at (i + 1) / (k + 1) along it; a new line's slot s at (s + 0.5) / (k + 1)
        - between the lines either side of it, and never on one."""
        a, b, c = self.tris[ti]
        if isinstance(end, _EdgeRef):
            k, place = end.k, self.order[end.k].index(end.lid)
        elif end[0] == "v":
            return float((a, b, c).index(end[1]))
        else:
            _, k, place = end
        n = len(self.order[k])
        f = (place + (0.5 if new else 1.0)) / (n + 1)
        for base, (u, v) in enumerate(((a, b), (b, c), (c, a))):
            if (min(u, v), max(u, v)) == k:
                return base + (f if u == k[0] else 1.0 - f)
        raise ValueError("edge not on triangle")

    def _crossings(self, ti, e1, e2):
        """How many lines already in triangle ti a new chord e1 - e2 would cross."""
        p1, p2 = self._bpos(ti, e1, new=True), self._bpos(ti, e2, new=True)
        lo, hi = min(p1, p2), max(p1, p2)
        n = 0
        for lid, q1, q2 in self.chords[ti]:
            a, b = self._bpos(ti, q1), self._bpos(ti, q2)
            if min(abs(a - lo), abs(a - hi), abs(b - lo), abs(b - hi)) < 1e-9:
                continue        # a shared end (a vertex both lines leave from)
            if (lo < a < hi) != (lo < b < hi):
                n += 1
        return n

    # ---------------------------------------------------------------- the search

    def route(self, net, pa, pb):
        """Plan one line from pad vertex pa to pad vertex pb. Returns the line id, or None."""
        import heapq
        P, Q = self.xy[pa], self.xy[pb]
        h = lambda pt: math.dist(pt, Q)
        heap, best, came = [], {}, {}
        cnt = 0
        goal = None
        goal_cost = math.inf
        # from the start vertex into each of its triangles
        for ti in self.vtri.get(pa, []):
            if pb in self.tris[ti] and self._crossings(ti, ("v", pa), ("v", pb)) == 0:
                c = math.dist(P, Q)
                if c < goal_cost:
                    goal, goal_cost = ("direct", ti), c
            for k in self._tri_edges(ti):
                if k not in self.edges or len(self.order[k]) >= self.capacity(k):
                    continue
                for s in range(len(self.order[k]) + 1):
                    if self._crossings(ti, ("v", pa), ("e", k, s)):
                        continue
                    pt = self._slot_point(k, s)
                    g = math.dist(P, pt)
                    nxt = self._other(k, ti)
                    st = (k, s, nxt)
                    if g < best.get(st, math.inf):
                        best[st] = g
                        came[st] = ("start", ti)
                        cnt += 1
                        heapq.heappush(heap, (g + h(pt), cnt, g, st, pt))
        while heap:
            f, _, g, st, pt = heapq.heappop(heap)
            if f >= goal_cost:
                break
            if g > best.get(st, math.inf) + 1e-12:
                continue
            k1, s1, ti = st
            if pb in self.tris[ti] and self._crossings(ti, ("e", k1, s1), ("v", pb)) == 0:
                c = g + math.dist(pt, Q)
                if c < goal_cost:
                    goal, goal_cost = ("end", st, ti), c
            for k2 in self._tri_edges(ti):
                if k2 == k1 or k2 not in self.edges or len(self.order[k2]) >= self.capacity(k2):
                    continue
                for s2 in range(len(self.order[k2]) + 1):
                    if self._crossings(ti, ("e", k1, s1), ("e", k2, s2)):
                        continue
                    p2 = self._slot_point(k2, s2)
                    g2 = g + math.dist(pt, p2)
                    st2 = (k2, s2, self._other(k2, ti))
                    if g2 < best.get(st2, math.inf) - 1e-12:
                        best[st2] = g2
                        came[st2] = (st, ti)
                        cnt += 1
                        heapq.heappush(heap, (g2 + h(p2), cnt, g2, st2, p2))
        if goal is None:
            return None
        # the path, start to end: [(edge, slot, triangle before it)]
        if goal[0] == "direct":
            steps, last_t = [], goal[1]
        else:
            _, st, last_t = goal
            steps = []
            while True:
                prev = came[st]
                if prev[0] == "start":
                    steps.append((st[0], st[1], prev[1]))
                    break
                pst, ti = prev
                steps.append((st[0], st[1], ti))
                st = pst
            steps.reverse()
        return self._commit(net, pa, pb, steps, last_t)

    def _tri_edges(self, ti):
        a, b, c = self.tris[ti]
        return [(min(u, v), max(u, v)) for u, v in ((a, b), (b, c), (c, a))]

    def _other(self, k, ti):
        ts = self.etris[k]
        return ts[0] if ts[1] == ti else ts[1]

    def _commit(self, net, pa, pb, steps, last_t):
        """Write a planned line into the orders and the triangles' chords. Each slot was read
        against the orders as they stood; an edge is crossed once, so each is still right."""
        lid = len(self.lines)
        ends = [("v", pa)] + [("e", k, s) for k, s, _ in steps] + [("v", pb)]
        tris = [t for _, _, t in steps] + [last_t]
        # chords first, with the half-places of the new line, then the orders
        for k, s, _ in steps:
            self.order[k].insert(s, lid)
        for i, ti in enumerate(tris):
            a_, b_ = ends[i], ends[i + 1]
            self.chords[ti].append((lid, self._ref(a_, lid), self._ref(b_, lid)))
        self.lines[lid] = {"net": net, "pa": pa, "pb": pb, "edges": [k for k, _, _ in steps], "tris": tris}
        return lid

    def _ref(self, end, lid):
        """An end as chords keep it: a vertex, or an edge and this line's place in its order
        (read again each time: places move as lines are inserted beside it)."""
        if end[0] == "v":
            return end
        return _EdgeRef(end[1], lid)

    # ---------------------------------------------------------------- the geometry

    def geometry(self, iterations=6):
        """Each line's centreline, as [(x, y)]: the rubber band through its portals.

        Where a line crosses an edge is held a spacing from where the lines beside it in the
        edge's order cross - the spacing their slant needs (pitch / sin of the angle) - so
        the bands relax against each other: they start packed in their places, and each pass
        draws every line taut between its neighbours as they stand (Gauss-Seidel). Every
        pass is legal, because a line only ever moves inside the room its neighbours leave."""
        self.pos = {}
        for k, lids in self.order.items():
            if not lids:
                continue
            t0, t1, _ = self.edges[k]
            n = len(lids)
            slack = max(0.0, (t1 - t0) - (n - 1) * self.pitch)
            for i, lid in enumerate(lids):
                self.pos[(k, lid)] = t0 + slack / 2 + i * self.pitch
        spacing = {k: self.pitch for k in self.order}
        paths = {}
        for _ in range(iterations):
            for lid in self.lines:
                paths[lid] = self._band(lid, spacing)
                self._settle(lid, paths[lid])
            # the slant: lines crossing an edge at angle a keep a pitch apart square to
            # themselves when they are pitch / sin(a) apart along it - as far as the edge's
            # free part allows
            for k, lids in self.order.items():
                if len(lids) < 2:
                    continue
                a, b = self.xy[k[0]], self.xy[k[1]]
                ex, ey = R2._unit(b[0] - a[0], b[1] - a[1])
                worst = 1.0
                for lid in lids:
                    d = _dir_at(paths[lid], LineString([a, b]))
                    if d is not None:
                        worst = min(worst, max(0.3, abs(ex * d[1] - ey * d[0])))
                t0, t1, _ = self.edges[k]
                spacing[k] = min(self.pitch / worst, max(self.pitch, (t1 - t0) / (len(lids) - 1)))
        return paths

    def _settle(self, lid, path):
        """Record where `path` now crosses each of its edges (as a distance along it)."""
        line = LineString(path)
        for k in self.lines[lid]["edges"]:
            a, b = self.xy[k[0]], self.xy[k[1]]
            e = LineString([a, b])
            x = line.intersection(e)
            if x.is_empty:
                continue
            pt = x if x.geom_type == "Point" else (x.geoms[0] if hasattr(x, "geoms") else x.centroid)
            if pt.geom_type != "Point":
                pt = pt.centroid
            self.pos[(k, lid)] = e.project(pt)

    def _portal(self, k, lid, spacing):
        """The stretch of edge k line lid may cross on: from a spacing past the line before it
        in the order to a spacing short of the line after it, inside the edge's free part.
        (lo point, hi point) along k[0] -> k[1]."""
        t0, t1, L = self.edges[k]
        lids = self.order[k]
        i = lids.index(lid)
        p = spacing.get(k, self.pitch)
        lo = t0 if i == 0 else self.pos[(k, lids[i - 1])] + p
        hi = t1 if i == len(lids) - 1 else self.pos[(k, lids[i + 1])] - p
        lo, hi = max(lo, t0), min(hi, t1)
        if lo > hi:                     # no room: where it stands
            lo = hi = min(max(self.pos[(k, lid)], t0), t1)
        return self._at(k, lo / L), self._at(k, hi / L)

    def _band(self, lid, spacing):
        ln = self.lines[lid]
        P, Q = self.xy[ln["pa"]], self.xy[ln["pb"]]
        portals = [(P, P)]
        for k, ti in zip(ln["edges"], ln["tris"]):
            lo, hi = self._portal(k, lid, spacing)
            # left and right as seen walking from triangle ti across k
            ca = _centroid([self.xy[v] for v in self.tris[ti]])
            mid = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)
            dx, dy = mid[0] - ca[0], mid[1] - ca[1]
            side = dx * (lo[1] - mid[1]) - dy * (lo[0] - mid[0])
            portals.append((lo, hi) if side > 0 else (hi, lo))
        portals.append((Q, Q))
        return _funnel(portals)


class _EdgeRef:
    """A chord's end on an edge: the edge and the line, whose place in the edge's order is
    read when it is needed (lines inserted beside it move it)."""
    __slots__ = ("k", "lid")

    def __init__(self, k, lid):
        self.k, self.lid = k, lid


def _centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def _dir_at(path, edge):
    """The unit direction of `path` where it crosses `edge`, or None."""
    for a, b in zip(path, path[1:]):
        s = LineString([a, b])
        if s.length > 1e-9 and s.intersects(edge):
            return R2._unit(b[0] - a[0], b[1] - a[1])
    return None


def _tri2(a, b, c):
    """Twice the signed area of a, b, c (positive: c left of a -> b, x right, y up)."""
    return (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])


def _funnel(portals):
    """The simple stupid funnel algorithm (Mononen): the shortest path through portals given
    as (left, right) pairs, the first and last a single point each."""
    pts = [portals[0][0]]
    apex, left, right = portals[0][0], portals[0][0], portals[0][1]
    ai = li = ri = 0
    i = 1
    n = len(portals)
    while i < n:
        pl, pr = portals[i]
        # the right side
        if _tri2(apex, right, pr) >= 0:
            if apex == right or _tri2(apex, left, pr) < 0:
                right, ri = pr, i
            else:
                pts.append(left)
                apex, ai = left, li
                left, right = apex, apex
                li = ri = ai
                i = ai + 1
                continue
        # the left side
        if _tri2(apex, left, pl) <= 0:
            if apex == left or _tri2(apex, right, pl) > 0:
                left, li = pl, i
            else:
                pts.append(right)
                apex, ai = right, ri
                left, right = apex, apex
                li = ri = ai
                i = ai + 1
                continue
        i += 1
    if pts[-1] != portals[-1][0]:
        pts.append(portals[-1][0])
    return pts


def route_layer(model, layer, pairs, **kw):
    """Plan and draw two-pad nets on one layer. pairs: [(net, pad, pad)] (pcb_route2 Pads),
    routed in the order given. Returns (runs, failed): pcb_route2 Runs, and [net] not placed."""
    nets = [n for n, _, _ in pairs]
    mp = Map(model, layer, nets, **kw)
    vid = {id(p): i for i, p in mp.pad_of.items()}
    failed, lids = [], {}
    for net, a, b in pairs:
        lid = mp.route(net, vid[id(a)], vid[id(b)])
        if lid is None:
            failed.append(net)
        else:
            lids[lid] = net
    paths = mp.geometry()
    runs = []
    for lid, net in lids.items():
        pts = [(x, y, layer) for x, y in paths[lid]]
        runs.append(R2.Run(net, pts, model.rules.width(net), via=model.rules.via_size(net)))
    return runs, failed, mp
