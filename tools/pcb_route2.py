"""The centreline router (issue #46): one copper model, one legality test, and the
tools that move copper once it is laid. tools/pcb_route.py still routes every real
board; this module routes a board only when asked, and writes only where it is told.

    python3 tools/pcb_route2.py route   BOARD.kicad_pcb --layout layout.yaml -o OUT.kicad_pcb [--nets A,B] [--ground GND]
                                        [--fence x0,y0,x1,y1] [--liquid] [--fillet MM]
    python3 tools/pcb_route2.py reroute BOARD.kicad_pcb --layout layout.yaml -o OUT.kicad_pcb --net N [--pull MM]
    python3 tools/pcb_route2.py tidy    BOARD.kicad_pcb --layout layout.yaml -o OUT.kicad_pcb [--fillet MM]

THE MODEL
  * `Rules` - width, clearance, a class's layers, layer costs and via size, parsed ONCE
    from layout.yaml `rules:` / `fab:` / `net_classes:`. Nothing below keeps a copy.
  * `CopperIndex` - every pad, track, via, hole, keep-out and reservation, in a bucket
    grid. A LOCKED entry has no remove and no move: `remove` raises. Pads are locked.
  * `Run` - one route as a centreline: points (x, y, layer), a via wherever two points
    share x, y and change layer, a width per segment, an optional fillet radius.
  * `fits(run, index, model)` - THE ONLY LAY PREDICATE. Exact geometry (shapely) against
    every other net's copper at the pair's clearance, holes, keep-outs, reservations,
    the board edge and the fence; a via also against SMD pads (its own net's too) and
    hole to hole. The search may be optimistic; nothing is laid that fails `fits`.
    `fits` cannot see a pour: a run that is legal can still cut a ground pin off its
    plane, so a poured board is proved by KiCad's DRC after a fill (pcb_route2_test).
  * `Field` - a board-mm rectangle that steers the search inside it: `heading` (an axis,
    degrees: a move off it costs 1 + k sin^2 of the angle), `weight` (< 1 prefer, > 1
    avoid; a field with no heading is --prefer / --avoid), `spread` (a halo cost round
    other nets' tracks), and the lay values
    `clearance` and `track`, reached over `taper` mm from the field's edge. Width never
    goes under the class or fab minimum, and a power net's width only with `power: true`.
    A heading only PENALISES: it decides how a route runs where it already goes, and never
    draws one in. A lane - routes that should travel inside the field, along it - is a
    heading with a weight under 1. A route whose net travel is across a heading pays for
    every step, and on open board may saw-tooth to do it: give it no such field.

THE SEARCH (`Router.connect`)
  A* on a sketch grid (`pitch`, a multiple of the 0.05 mm LATTICE every laid point is
  snapped to). State: layer, cell, heading - the heading is carried through a via, so a
  route does not double back across one. Moves cost their length times the layer's cost
  and the fields'; a turn costs by its angle (135 and 180 degrees cost, they are not
  banned); a via costs `via_cost` mm. The heuristic is a distance transform from the
  targets over cells free on any layer, scaled by the cheapest multiplier, so it stays
  admissible. A node budget and a time cap stop it; an EXHAUSTED search is reported as
  "no path" (an answer), a stopped one as "budget" (no answer). Heap ties break on
  (f, g, counter). Single-layer first: a via-free path within `via_first_ratio` of the
  best path with vias is taken instead.

THE TOOLS
  * families: a `bus: true` family reserves its corridor - n pitches plus clearance -
    along one sketched centreline before its members route, and the reservation blocks
    every other net. Other families keep crossing-aware order (fewest airwire crossings,
    then shortest).
  * flow: a small cost per still-unrouted airwire passing a cell. It cannot override
    `fits`.
  * ground: routed as a net that may stay in groups, then a stitching via for each
    single-sided ground pad its tree did not reach, then a pour on every copper layer
    (written by `write`).
  * rescue: a failed connection's box (1.5, 3, 5 mm) is taken up - never locked copper,
    never a net with copper outside the fence - and kept only if fewer connections fail.
  * reroute(net, pull): the net routed again inside a corridor along its pads' line.
    A net in the way is SHOVED: laid again round the new run, near its old path, at most
    two deep; only if that fails is the net laid round everything as it stands.
  * slide_vias / uncross: an unlocked via slid along its two runs, kept only if `fits`
    passes, crossings do not rise and length falls; an up-then-down pair shorter than
    1.5 mm folded onto one face.
  * liquid: jogs coalesced (rubber band, 0/45/90 only), parallel gaps equalised (a capped
    fixed point with a monotone objective, in a fixed order, so the result does not
    depend on the machine), corners filleted into arcs.
"""
import heapq
import itertools
import math
import os
import sys
import time
from collections import defaultdict

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

LATTICE = 0.05                # every laid coordinate is on it
# mm: what fits adds to every clearance it tests. Shapely draws a circle (a via, a round
# track end) as a polygon INSIDE it - 32 sides here, short of the true radius by up to
# r (1 - cos(pi / 32)), 1.7 um on a 0.7 mm via - and KiCad's own pad polygons are drawn
# the same way, so a gap that fits passed at exactly the clearance could be 0.2 um to
# 2 um short in KiCad's DRC (the left key board's trial: 0.1988 against 0.2000). The
# margin makes the approximation err on the safe side.
EPS = -0.003
OWN_PAD_GAP = 0.05            # a via's ring to its own net's SMD pad: off it
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
TURN_MM = [0.0, 0.15, 0.6, 2.5, 6.0]      # by the turn, in 45-degree steps: cost, never a ban
SQ2 = math.sqrt(2.0)


def snap(v, q=LATTICE):
    return round(round(v / q) * q, 6)


class LockedError(Exception):
    pass


# ------------------------------------------------------------------ rules

class Rules:
    """One parse of layout.yaml's rules; every width, clearance and via size below asks it."""

    def __init__(self, lay):
        r = lay.get("rules") or {}
        fab = lay.get("fab") or {}
        self.track = float(r.get("track", 0.25))
        self.track_min = float(r.get("track_min", self.track))
        self.clearance = float(r.get("clearance", 0.2))
        self.via = float(r.get("via", 0.7))
        self.via_drill = float(r.get("via_drill", 0.3))
        self.edge = float(r.get("edge_clearance", 0.3))
        self.power_track = float(r.get("power_track", self.track))
        self.hole_to_hole = float(fab.get("hole_to_hole", 0.25))
        self.hole_clearance = float(fab.get("hole_clearance", self.clearance))
        self.power = set(lay.get("power_nets") or [])
        self.via_cost = float(lay.get("via_cost", 2.4))
        self.via_first_ratio = float(lay.get("via_first_ratio", 1.3))
        self.classes, self.of = {}, {}
        for name, c in (lay.get("net_classes") or {}).items():
            self.classes[name] = c
            for n in c.get("nets", []):
                self.of[n] = c

    def cls(self, net):
        return self.of.get(net, {})

    def width(self, net):
        c = self.cls(net)
        return float(c.get("track", self.power_track if net in self.power else self.track))

    def width_min(self, net):
        return max(self.track_min, float(self.cls(net).get("track_min", self.track_min)))

    def clear(self, net):
        return float(self.cls(net).get("clearance", self.clearance))

    def gap(self, a, b):
        return max(self.clear(a), self.clear(b) if b else self.clearance)

    def layers(self, net, names):
        ls = self.cls(net).get("layers")
        return [i for i, n in enumerate(names) if not ls or n in ls]

    def layer_cost(self, net, name):
        return float((self.cls(net).get("layer_cost") or {}).get(name, 1.0))

    def via_size(self, net):
        v = self.cls(net).get("via")
        return (float(v[0]), float(v[1])) if v else (self.via, self.via_drill)


# ------------------------------------------------------------------ the copper index

class Entry:
    __slots__ = ("id", "net", "layers", "geom", "kind", "locked", "run", "family", "drill", "smd",
                 "tracks", "vias", "item", "ref", "line")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


class CopperIndex:
    """Everything copper must keep clear of, in buckets of `bucket` mm. Mutable by add and
    remove only; a locked entry cannot be removed, and there is no move."""

    def __init__(self, bucket=2.0):
        self.bucket = bucket
        self.e = {}
        self.b = defaultdict(set)
        self.ids = itertools.count(1)

    def _keys(self, bounds):
        x0, y0, x1, y1 = bounds
        q = self.bucket
        for i in range(int(math.floor(x0 / q)), int(math.floor(x1 / q)) + 1):
            for j in range(int(math.floor(y0 / q)), int(math.floor(y1 / q)) + 1):
                yield (i, j)

    def add(self, **kw):
        e = Entry(**kw)
        e.id = next(self.ids)
        e.layers = frozenset(e.layers or ())
        self.e[e.id] = e
        for k in self._keys(e.geom.bounds):
            self.b[k].add(e.id)
        return e

    def remove(self, eid):
        e = self.e[eid]
        if e.locked:
            raise LockedError(f"entry {eid} ({e.kind} of {e.net}) is locked")
        for k in self._keys(e.geom.bounds):
            self.b[k].discard(eid)
        del self.e[eid]
        return e

    def query(self, bounds, margin=0.0):
        x0, y0, x1, y1 = bounds
        seen = set()
        for k in self._keys((x0 - margin, y0 - margin, x1 + margin, y1 + margin)):
            seen |= self.b.get(k, set())
        return [self.e[i] for i in sorted(seen)]

    def of_net(self, net, kinds=("track", "via")):
        return [e for e in self.e.values() if e.net == net and e.kind in kinds]


# ------------------------------------------------------------------ fields

class Field:
    """A rectangle (board mm) that steers the search and sets lay values inside it."""

    def __init__(self, rect, heading=None, weight=1.0, spread=0.0, clearance=None, track=None, taper=0.0,
                 power=False, nets=None, k=1.5, geom=None):
        # `geom`: a shape (shapely) the field covers instead of its rectangle - a corridor
        # along a polyline (Router.edit through:), whose bounding box would take in far more
        self.geom = geom
        if geom is not None:
            rect = geom.bounds
        x0, y0, x1, y1 = (float(v) for v in rect)
        self.rect = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        self.heading = None if heading is None else float(heading)
        self.weight, self.spread, self.k = float(weight), float(spread), float(k)
        self.clearance, self.track, self.taper = clearance, track, float(taper)
        self.power, self.nets = power, set(nets) if nets else None

    @classmethod
    def from_spec(cls, s):
        return cls(s["rect"], s.get("heading"), s.get("weight", 1.0), s.get("spread", 0.0), s.get("clearance"),
                   s.get("track"), s.get("taper", 0.0), s.get("power", False), s.get("nets"), s.get("k", 1.5))

    def applies(self, net):
        return self.nets is None or net in self.nets

    def depth(self, x, y):
        """How far inside the rectangle (x, y) is, in mm (negative outside)."""
        x0, y0, x1, y1 = self.rect
        return min(x - x0, x1 - x, y - y0, y1 - y)

    def blend(self, x, y):
        d = self.depth(x, y)
        if d < 0:
            return 0.0
        return 1.0 if self.taper <= 0 else min(1.0, d / self.taper)


def local_values(fields, rules, net, x, y):
    """The lay width and clearance at (x, y): the class's, moved toward each field's own."""
    w, c = rules.width(net), rules.clear(net)
    for f in fields:
        if not f.applies(net):
            continue
        t = f.blend(x, y)
        if t <= 0:
            continue
        if f.track is not None and (net not in rules.power or f.power):
            w = w + (float(f.track) - w) * t
        if f.clearance is not None:
            c = max(c, c + (float(f.clearance) - c) * t)
    return max(w, rules.width_min(net)), c


# ------------------------------------------------------------------ runs

class Run:
    """A route as a centreline. pts: [(x, y, layer)]; two consecutive points at one x, y
    on two layers are a via. widths: one per segment (None: the net's width)."""

    def __init__(self, net, pts, width, via=(0.7, 0.3), locked=False, fillet=0.0, widths=None):
        self.net, self.width, self.via = net, float(width), via
        self.pts = [(snap(x), snap(y), int(L)) for x, y, L in pts]
        self.locked, self.fillet = locked, float(fillet)
        self.widths = widths
        self.entries = []           # CopperIndex ids once laid
        self.items = []             # board items once written

    def copy(self, pts=None):
        r = Run(self.net, self.pts if pts is None else pts, self.width, self.via, self.locked, self.fillet)
        return r

    def seg_width(self, k):
        if self.widths and k < len(self.widths) and self.widths[k]:
            return self.widths[k]
        return self.width

    def legs(self):
        """[(layer, [points])]: the maximal same-layer pieces, split at vias."""
        out, cur = [], [self.pts[0]]
        for p in self.pts[1:]:
            if p[2] != cur[-1][2]:
                out.append((cur[-1][2], [(q[0], q[1]) for q in cur]))
                cur = [p]
            else:
                cur.append(p)
        out.append((cur[-1][2], [(q[0], q[1]) for q in cur]))
        return out

    def vias(self):
        return [(a[0], a[1]) for a, b in zip(self.pts, self.pts[1:]) if a[2] != b[2]]

    def segments(self):
        """[(layer, a, b, width)], zero-length ones dropped."""
        out, k = [], 0
        for a, b in zip(self.pts, self.pts[1:]):
            if a[2] != b[2]:
                continue
            if (a[0], a[1]) != (b[0], b[1]):
                out.append((a[2], (a[0], a[1]), (b[0], b[1]), self.seg_width(k)))
            k += 1
        return out

    def length(self):
        return sum(math.dist(a, b) for _, a, b, _ in self.segments())

    def prims(self):
        """('S', L, a, b, w) / ('A', L, start, mid, end, w) / ('V', x, y): what is written,
        and what fits tests. A fillet is cut into each corner where both runs either side
        are long enough; the arc stays inside the corner, so it never comes nearer the
        outside of the bend than the sharp corner did."""
        out = []
        for L, pts in self.legs():
            out += _fillet_leg(L, pts, self.fillet, self.width) if self.fillet > 0 and len(pts) > 2 \
                else [("S", L, a, b, self.width) for a, b in zip(pts, pts[1:]) if a != b]
        if self.widths:
            segs = self.segments()
            # per-segment widths survive only on unfilleted runs (fields set them at lay)
            if self.fillet <= 0:
                out = [("S", L, a, b, w) for (L, a, b, w) in segs]
        out += [("V", x, y) for x, y in self.vias()]
        return out


def _unit(dx, dy):
    n = math.hypot(dx, dy)
    return (dx / n, dy / n) if n else (0.0, 0.0)


def _fillet_leg(L, pts, r, w):
    pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
    n = len(pts)
    cut = [0.0] * n
    arcs = [None] * n
    for i in range(1, n - 1):
        u1 = _unit(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        u2 = _unit(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        th = math.atan2(u1[0] * u2[1] - u1[1] * u2[0], u1[0] * u2[0] + u1[1] * u2[1])
        if abs(th) < 1e-6:
            continue
        la, lb = math.dist(pts[i - 1], pts[i]), math.dist(pts[i], pts[i + 1])
        # each run gives at most half of itself to a corner (the other half to its other end)
        Lmax = min(la * (0.5 if i > 1 else 1.0), lb * (0.5 if i < n - 2 else 1.0))
        rr = min(r, Lmax / math.tan(abs(th) / 2)) if math.tan(abs(th) / 2) > 0 else 0
        if rr < max(w, 0.1):
            continue
        Lc = rr * math.tan(abs(th) / 2)
        s = (pts[i][0] - u1[0] * Lc, pts[i][1] - u1[1] * Lc)
        e = (pts[i][0] + u2[0] * Lc, pts[i][1] + u2[1] * Lc)
        sg = 1 if th > 0 else -1
        c = (s[0] - u1[1] * rr * sg, s[1] + u1[0] * rr * sg)
        # the mid point: on the bisector from the centre
        bx, by = _unit((s[0] + e[0]) / 2 - c[0], (s[1] + e[1]) / 2 - c[1])
        m = (c[0] + bx * rr, c[1] + by * rr)
        cut[i] = Lc
        arcs[i] = (s, m, e)
    out = []
    for i in range(n - 1):
        a, b = pts[i], pts[i + 1]
        u = _unit(b[0] - a[0], b[1] - a[1])
        a2 = (a[0] + u[0] * cut[i], a[1] + u[1] * cut[i])
        b2 = (b[0] - u[0] * cut[i + 1], b[1] - u[1] * cut[i + 1])
        if arcs[i]:
            out.append(("A", L, *arcs[i], w))
        if math.dist(a2, b2) > 1e-6:
            out.append(("S", L, a2, b2, w))
    if arcs[n - 1]:
        out.append(("A", L, *arcs[n - 1], w))
    return out


def arc_points(s, m, e, n=12):
    """Points along the circular arc s -> m -> e."""
    ax, ay = s
    bx, by = m
    cx, cy = e
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return [s, e]
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, a1, am = (math.atan2(p[1] - uy, p[0] - ux) for p in (s, e, m))
    sw = (a1 - a0) % (2 * math.pi)
    if (am - a0) % (2 * math.pi) > sw:
        sw -= 2 * math.pi
    return [(ux + r * math.cos(a0 + sw * k / n), uy + r * math.sin(a0 + sw * k / n)) for k in range(n + 1)]


def prim_line(p):
    if p[0] == "S":
        return LineString([p[2], p[3]]) if p[2] != p[3] else Point(p[2])
    return LineString(arc_points(p[2], p[3], p[4]))


# ------------------------------------------------------------------ the board model

class Pad:
    __slots__ = ("ref", "num", "net", "layers", "geom", "centre", "smd", "drill", "item", "tie", "face_of_hole")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))
        self.tie = bool(self.tie)

    @property
    def name(self):
        return f"{self.ref}.{self.num}"


class Model:
    """A board as the router sees it: outline, copper layers, rules, pads, holes, keep-outs
    and the copper already there, all in one CopperIndex."""

    def __init__(self, outline, layer_names, rules, pads=(), holes=(), keepouts=(), fence=None):
        self.outline, self.layer_names, self.rules = outline, list(layer_names), rules
        self.nl = len(self.layer_names)
        self.inside = outline.buffer(-rules.edge)
        self.fence = fence
        self.index = CopperIndex()
        self.pads = list(pads)
        self.removed_items = []         # board items rip-up took away, for write()
        for p in self.pads:
            self.index.add(net=p.net, layers=p.layers, geom=p.geom, kind="pad", locked=True, smd=p.smd,
                           drill=p.drill, ref=p.name, item=p.item)
        for g, drill in holes:
            self.index.add(net=None, layers=range(self.nl), geom=g, kind="hole", locked=True, drill=drill)
        for g, layers, tracks, vias in keepouts:
            self.index.add(net=None, layers=layers, geom=g, kind="keepout", locked=True, tracks=tracks, vias=vias)

    planes = None                       # a Planes, on a board with layout.yaml planes: / islands:

    def track_layers(self, net):
        """The layers `net` may run a track on: its class's `layers:` when it names them
        (an opt-in, a plane layer included - the main board's In2.Cu channels); else every
        layer that is no net's plane."""
        named = self.rules.cls(net).get("layers")
        if named:
            return [i for i, n in enumerate(self.layer_names) if n in named]
        closed = set(self.planes.layer_net) if self.planes else set()
        return [i for i in range(self.nl) if i not in closed]

    def via_ok_for(self, net):
        """A through via joins every layer; a net whose class pins it to one layer has none."""
        named = self.rules.cls(net).get("layers")
        return not named or len(named) > 1

    def pads_of(self, net):
        return [p for p in self.pads if p.net == net]

    def nets(self):
        return sorted({p.net for p in self.pads if p.net and not p.net.startswith("unconnected")})


class Planes:
    """A multi-layer board's planes as layout.yaml gives them, in board mm - the same reading
    pcb_main.check_planes makes, so what the router lays is what the check accepts.

      planes:  [{layer, net}]   a layer that is one net's plane: closed to every other net's
                                tracks (a class `layers:` may open it), and the reference of
                                the outer layer beside it (F.Cu over In1.Cu, B.Cu over In2.Cu)
      islands: [{net, layer, outline (BODY mm, as pcb_main), moat, tie / ties, tie_window,
                 windows, off_island, strip, foreign_ok}]
                                a net's island in another's plane, a moat round it. An island
                                net's via stands on its islands; another plane net's via on
                                that layer stands off the island and its moat
      fanout:  [nets]           each SMD pad of these nets gets its own via into its plane
                                (fanout_count: {pad: n}, fanout_through: [pads])

    The SPLITS - where a signal on an outer layer would cross a gap in its reference plane -
    are reservations on that outer layer: the moat round each island on the reference layer
    (but at its ties' windows; a declared pair may cross it), and wherever the reference
    layer has no plane copper drawn. Plane nets are exempt, as check_planes has them."""

    REF = {"F.Cu": "In1.Cu", "B.Cu": "In2.Cu"}

    def __init__(self, lay, model, board=None, to_pcb=None):
        if to_pcb is None:
            import pcb
            to_pcb = pcb.to_pcb
        names = model.layer_names
        self.layer_net = {names.index(p["layer"]): p["net"] for p in lay.get("planes") or [] if p["layer"] in names}
        self.pair_nets = {n for pr in lay.get("pairs") or [] for n in pr["nets"]}
        self.fanout_nets = list(lay.get("fanout") or [])
        self.fanout_count = dict(lay.get("fanout_count") or {})
        self.fanout_through = set(lay.get("fanout_through") or [])
        self.islands = []
        outline = model.outline
        for spec in lay.get("islands") or []:
            if spec["layer"] not in names:
                continue
            body = Polygon(spec["outline"])
            poly = Polygon([to_pcb(x, y) for x, y in spec["outline"]]).intersection(outline)
            moat = Polygon([to_pcb(x, y) for x, y in body.buffer(spec["moat"], join_style=2).exterior.coords])
            windows = []
            ties = spec["ties"] if "ties" in spec else ([spec["tie"]] if spec.get("tie") else [])
            if board is not None:
                for t in ties:
                    fp = board.FindFootprintByReference(t)
                    if fp:
                        c = fp.GetPosition()
                        windows.append(Point(_kicad().ToMM(c.x), _kicad().ToMM(c.y)).buffer(float(spec.get("tie_window", 0.0))))
            for x, y, r in spec.get("windows") or []:
                windows.append(Point(*to_pcb(x, y)).buffer(r))
            self.islands.append({"net": spec["net"], "layer": names.index(spec["layer"]), "poly": poly, "moat": moat,
                                 "ring": moat.difference(poly.buffer(-0.05, join_style=2)),
                                 "windows": unary_union(windows) if windows else None, "strip": bool(spec.get("strip")),
                                 "off_island": set(spec.get("off_island") or [])})
        self.plane_nets = set(self.layer_net.values()) | {i["net"] for i in self.islands}
        # where each plane net's copper is: its layer less the moats of the islands on it;
        # an island net's, its islands
        self.region = {}
        for L, net in self.layer_net.items():
            reg = outline
            for i in self.islands:
                if i["layer"] == L:
                    reg = reg.difference(i["moat"])
            self.region[net] = unary_union([self.region[net], reg]) if net in self.region else reg
        for i in self.islands:
            n = i["net"]
            if n in self.layer_net.values():
                continue            # a net that is a plane AND has islands: the plane region already holds it
            self.region[n] = unary_union([self.region[n], i["poly"]]) if n in self.region else i["poly"]
        self.island_union = {}
        for i in self.islands:
            if not i["strip"]:
                n = i["net"]
                self.island_union[n] = unary_union([self.island_union[n], i["poly"]]) if n in self.island_union else i["poly"]
        for i in self.islands:          # a net's strips count as its islands for its vias, as the check has it
            n = i["net"]
            if i["strip"] and n in self.island_union:
                self.island_union[n] = unary_union([self.island_union[n], i["poly"]])

    def splits(self, model, zones):
        """[(outer layer index, geometry, exempt nets)]: the reservations an outer layer's
        signals keep off. `zones`: [(layer index, outline polygon)] of the copper zones."""
        out = []
        for outer, ref in self.REF.items():
            if outer not in model.layer_names or ref not in model.layer_names:
                continue
            Lo, Lr = model.layer_names.index(outer), model.layer_names.index(ref)
            drawn = [g for L, g in zones if L == Lr]
            if not drawn:
                continue            # no plane beside it: nothing to cross
            bare = model.inside.difference(unary_union(drawn))
            if not bare.is_empty and bare.area > 1e-3:
                out.append((Lo, bare, set(self.plane_nets)))
            for i in self.islands:
                if i["layer"] != Lr:
                    continue
                ring = i["ring"] if i["windows"] is None else i["ring"].difference(i["windows"])
                if not ring.is_empty:
                    out.append((Lo, ring, set(self.plane_nets) | self.pair_nets))
        return out

    def via_zones(self, net, d):
        """[(geometry, inside)]: an island net's via must stand INSIDE its islands (shrunk by
        its radius); another plane net sharing an island's layer must stand OUTSIDE that
        island's moat (grown by its radius)."""
        out = []
        if net in self.island_union:
            out.append((self.island_union[net].buffer(-d / 2), True))
        for i in self.islands:
            if net != i["net"] and self.layer_net.get(i["layer"]) == net:
                out.append((i["moat"].buffer(d / 2), False))
        return out

    def via_faults(self, net, x, y, d):
        out = []
        c = Point(x, y)
        for geom, inside in self.via_zones(net, d):
            if inside and not geom.contains(c):
                out.append("off-island")
            if not inside and geom.contains(c):
                out.append("on-moat")
        return out


def fits(run, model, fields=(), fence=None, ignore=()):
    """Every reason `run` cannot be laid as it stands: [(what, where (x, y), entry id)].
    Empty means it fits. `ignore`: entry ids to leave out (the run's own old copper)."""
    R, net, idx = model.rules, run.net, model.index
    fence = fence if fence is not None else model.fence
    fbox = box(*fence) if fence else None
    allowed = set(model.track_layers(net))
    bad = []
    maxgap = max([R.clearance, R.hole_clearance, R.hole_to_hole] + [float(c.get("clearance", 0)) for c in R.classes.values()]
                 + [float(f.clearance or 0) for f in fields]) + 1.0
    for p in run.prims():
        if p[0] in "SA":
            L, w = p[1], p[-1]
            line = prim_line(p)
            mid = line.interpolate(0.5, normalized=True)
            _, lc = local_values(fields, R, net, mid.x, mid.y)
            w = max(w, R.width_min(net))
            body = line.buffer(w / 2, quad_segs=8)
            where = (round(mid.x, 3), round(mid.y, 3))
            if L not in allowed:
                bad.append(("layer", where, None))
            if not model.inside.contains(body):
                bad.append(("edge", where, None))
            if fbox is not None and not fbox.contains(body):
                bad.append(("fence", where, None))
            for e in idx.query(body.bounds, maxgap):
                if e.id in ignore or L not in e.layers:
                    continue
                if e.kind == "reserve":
                    if net not in e.family and body.intersects(e.geom):
                        bad.append(("reserved", where, e.id))
                elif e.kind == "keepout":
                    if e.tracks and body.intersects(e.geom):
                        bad.append(("keepout", where, e.id))
                elif e.kind == "hole":
                    if body.distance(e.geom) < R.hole_clearance - EPS:
                        bad.append(("hole", where, e.id))
                elif e.net != net:
                    if body.distance(e.geom) < max(R.gap(net, e.net), lc) - EPS:
                        bad.append(("clearance", where, e.id))
        else:
            x, y = p[1], p[2]
            d, drill = run.via
            disc = Point(x, y).buffer(d / 2, quad_segs=8)
            hole = Point(x, y).buffer(drill / 2, quad_segs=8)
            where = (x, y)
            if not model.via_ok_for(net):
                bad.append(("via-layer", where, None))
            if model.planes is not None:
                bad += [(w_, where, None) for w_ in model.planes.via_faults(net, x, y, d)]
            if not model.inside.contains(disc):
                bad.append(("edge", where, None))
            if fbox is not None and not fbox.contains(disc):
                bad.append(("fence", where, None))
            for e in idx.query(disc.bounds, maxgap):
                if e.id in ignore:
                    continue
                if e.kind == "reserve":
                    if net not in e.family and disc.intersects(e.geom):
                        bad.append(("reserved", where, e.id))
                    continue
                if e.kind == "keepout":
                    if e.vias and disc.intersects(e.geom):
                        bad.append(("keepout", where, e.id))
                    continue
                if e.drill:
                    dd = Point(*e.geom.centroid.coords[0]).buffer(e.drill / 2) if e.kind != "hole" else e.geom
                    if hole.distance(dd) < R.hole_to_hole - EPS:
                        bad.append(("hole-to-hole", where, e.id))
                if e.kind == "hole":
                    if disc.distance(e.geom) < R.hole_clearance - EPS:
                        bad.append(("hole", where, e.id))
                    continue
                if e.kind == "pad" and e.smd:
                    gap = OWN_PAD_GAP if e.net == net else R.gap(net, e.net)
                    if disc.distance(e.geom) < gap - EPS:
                        bad.append(("via-on-pad", where, e.id))
                    continue
                if e.net != net and disc.distance(e.geom) < R.gap(net, e.net) - EPS:
                    bad.append(("clearance", where, e.id))
    return bad


def lay(run, model):
    """Add a run that fits to the index. Returns the run."""
    for p in run.prims():
        if p[0] in "SA":
            g = prim_line(p).buffer(p[-1] / 2, quad_segs=8)
            e = model.index.add(net=run.net, layers=[p[1]], geom=g, kind="track", locked=run.locked, run=run)
        else:
            d, drill = run.via
            e = model.index.add(net=run.net, layers=range(model.nl), geom=Point(p[1], p[2]).buffer(d / 2, quad_segs=8),
                                kind="via", locked=run.locked, run=run, drill=drill)
        run.entries.append(e.id)
    return run


def unlay(run, model):
    if run.locked:
        raise LockedError(f"{run.net}: a locked run does not move")
    for eid in run.entries:
        model.index.remove(eid)
    run.entries = []


# ------------------------------------------------------------------ geometry helpers

def octilinear(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    return abs(dx) < 1e-6 or abs(dy) < 1e-6 or abs(abs(dx) - abs(dy)) < 1e-6


def simplify(pts):
    """Drop points that lie on the straight line between their neighbours (same layer)."""
    out = []
    for p in pts:
        if out and (p[0], p[1], p[2]) == out[-1]:
            continue
        out.append(p)
        while len(out) >= 3 and out[-1][2] == out[-2][2] == out[-3][2]:
            a, b, c = out[-3], out[-2], out[-1]
            cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            dot = (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1])
            if abs(cross) < 1e-9:
                # straight on, or a spike - a run that doubles back along itself (a pad stub
                # returning over the cell it came from): one segment either way, never two
                # tracks meeting at 0 degrees (pcb.py check's acid trap)
                out.pop(-2)
                if dot < 0 and (out[-1][0], out[-1][1]) == (out[-2][0], out[-2][1]):
                    out.pop()
            else:
                break
    return out


def crossings(runs):
    """How many times two different nets' runs cross in plan, on any layers: the bench's
    crossing count."""
    lines = []
    for r in runs:
        for L, a, b, _ in r.segments():
            lines.append((r.net, LineString([a, b])))
    n = 0
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            if lines[i][0] != lines[j][0] and lines[i][1].crosses(lines[j][1]):
                n += 1
    return n


def airwire_crossings(conns):
    """For each connection (net, a, b): how many other nets' airwires its straight line crosses."""
    ls = [LineString([a, b]) for _, a, b in conns]
    return [sum(1 for j, m in enumerate(conns) if m[0] != conns[i][0] and ls[i].crosses(ls[j])) for i in range(len(conns))]


# ------------------------------------------------------------------ the router

class Router:
    def __init__(self, model, pitch=0.2, fields=(), flow=0.0, budget=600000, time_s=None, fence=None):
        self.m, self.R = model, model.rules
        self.pitch = pitch
        self.fields = [f if isinstance(f, Field) else Field.from_spec(f) for f in fields]
        # SOFT copper: [(geometry, layers, weight)] - not an obstacle, but dear to cross (a
        # push's ideal path keeps off what it is about to shove, where it can)
        self.soft = []
        self.flow_w = flow
        self.budget, self.time_s = budget, time_s
        self.fence = fence if fence is not None else model.fence
        x0, y0, x1, y1 = model.outline.bounds
        self.x0, self.y0 = x0, y0
        self.nx, self.ny = int((x1 - x0) / pitch) + 2, int((y1 - y0) / pitch) + 2
        xs = x0 + np.arange(self.nx) * pitch
        ys = y0 + np.arange(self.ny) * pitch
        self.X, self.Y = np.meshgrid(xs, ys, indexing="ij")
        self.runs = []
        self.stats = defaultdict(int)
        self.log = []
        self._buf = {}
        self.flow = np.zeros((self.nx, self.ny))

    # ---- cells
    def xy(self, i, j):
        return (snap(self.x0 + i * self.pitch), snap(self.y0 + j * self.pitch))

    def ij(self, x, y):
        return (int(round((x - self.x0) / self.pitch)), int(round((y - self.y0) / self.pitch)))

    def _window(self, bounds, r):
        x0, y0, x1, y1 = bounds
        i0 = max(0, int((x0 - r - self.x0) / self.pitch))
        i1 = min(self.nx - 1, int((x1 + r - self.x0) / self.pitch) + 1)
        j0 = max(0, int((y0 - r - self.y0) / self.pitch))
        j1 = min(self.ny - 1, int((y1 + r - self.y0) / self.pitch) + 1)
        return i0, i1, j0, j1

    def _mark(self, mask, geom, r):
        if r > 0:
            key = (id(geom), round(r, 4))
            g = self._buf.get(key)
            if g is None:
                g = self._buf[key] = (geom, geom.buffer(r, quad_segs=6))
            g = g[1]
        else:
            g = geom
        i0, i1, j0, j1 = self._window(geom.bounds, r)
        if i1 < i0 or j1 < j0:
            return
        sub = shapely.contains_xy(g, self.X[i0:i1 + 1, j0:j1 + 1], self.Y[i0:i1 + 1, j0:j1 + 1])
        mask[i0:i1 + 1, j0:j1 + 1] |= sub

    def blocked(self, net, width, avoid_runs=()):
        """Track-centre grids per layer, and the via grid, for `net` at `width`: optimistic
        (no slack) - fits decides."""
        R, nl = self.R, self.m.nl
        g = np.zeros((nl, self.nx, self.ny), dtype=bool)
        v = np.zeros((self.nx, self.ny), dtype=bool)
        d, drill = R.via_size(net)
        allowed = set(self.m.track_layers(net))
        for L in range(nl):
            if L not in allowed:
                g[L] |= True
        skip = set()
        for r in avoid_runs:
            skip |= set(r.entries)
        for e in self.m.index.e.values():
            if e.id in skip:
                continue
            if e.kind == "reserve":
                if net in e.family:
                    continue
                for L in e.layers:
                    self._mark(g[L], e.geom, width / 2)
                self._mark(v, e.geom, d / 2)
                continue
            if e.kind == "keepout":
                if e.tracks:
                    for L in e.layers:
                        self._mark(g[L], e.geom, width / 2)
                if e.vias:
                    self._mark(v, e.geom, d / 2)
                continue
            if e.kind == "hole":
                for L in e.layers:
                    self._mark(g[L], e.geom, width / 2 + R.hole_clearance)
                self._mark(v, e.geom, max(d / 2 + R.hole_clearance, drill / 2 + R.hole_to_hole))
                continue
            if e.drill and e.kind != "hole":
                c = e.geom.centroid
                self._mark(v, Point(c.x, c.y), e.drill / 2 + drill / 2 + R.hole_to_hole)
            if e.net == net:
                if e.kind == "pad" and e.smd:
                    self._mark(v, e.geom, d / 2 + OWN_PAD_GAP)
                continue
            gap = R.gap(net, e.net)
            for L in e.layers:
                self._mark(g[L], e.geom, width / 2 + gap)
            self._mark(v, e.geom, d / 2 + gap)
        inner = self.m.inside.buffer(-width / 2)
        out = ~shapely.contains_xy(inner, self.X, self.Y)
        g |= out[None, :, :]
        vin = self.m.inside.buffer(-d / 2)
        v |= ~shapely.contains_xy(vin, self.X, self.Y)
        if self.fence:
            fx0, fy0, fx1, fy1 = self.fence
            fin = (self.X >= fx0 + width / 2) & (self.X <= fx1 - width / 2) & (self.Y >= fy0 + width / 2) & (self.Y <= fy1 - width / 2)
            g |= ~fin[None, :, :]
            vfin = (self.X >= fx0 + d / 2) & (self.X <= fx1 - d / 2) & (self.Y >= fy0 + d / 2) & (self.Y <= fy1 - d / 2)
            v |= ~vfin
        if not self.m.via_ok_for(net):
            v[:] = True
        if self.m.planes is not None:
            # where this net's via may not stand: an island net's off its islands, another plane
            # net's on an island of its own layer or that island's moat
            for geom, inside in self.m.planes.via_zones(net, d):
                if inside:
                    v |= ~shapely.contains_xy(geom, self.X, self.Y)
                else:
                    self._mark(v, geom, 0.0)
        return g, v

    def costs(self, net, width):
        """Per-layer move multipliers, heading arrays and the spread halo, from the fields
        and the class's layer costs."""
        nl = self.m.nl
        M = np.ones((nl, self.nx, self.ny))
        for L, name in enumerate(self.m.layer_names):
            M[L] *= self.R.layer_cost(net, name)
        H = []          # (mask, ux, uy, k)
        halo = np.zeros((nl, self.nx, self.ny))
        for f in self.fields:
            if not f.applies(net):
                continue
            x0, y0, x1, y1 = f.rect
            if f.geom is not None:
                mask = np.zeros((self.nx, self.ny), dtype=bool)
                self._mark(mask, f.geom, 0.0)
            else:
                mask = (self.X >= x0) & (self.X <= x1) & (self.Y >= y0) & (self.Y <= y1)
            if f.heading is None:
                M[:, mask] *= f.weight
            else:
                a = math.radians(f.heading)
                H.append((mask, math.cos(a), math.sin(a), f.k))
                if f.weight != 1.0:
                    M[:, mask] *= f.weight
            if f.spread > 0:
                for e in self.m.index.e.values():
                    if e.kind in ("track", "via") and e.net != net:
                        for L in e.layers:
                            m2 = np.zeros((self.nx, self.ny), dtype=bool)
                            self._mark(m2, e.geom, width / 2 + self.R.gap(net, e.net) + f.spread)
                            halo[L][m2 & mask] = 1.0
        for g, layers, w in self.soft:
            m2 = np.zeros((self.nx, self.ny), dtype=bool)
            self._mark(m2, g, width / 2 + self.R.clear(net))
            for L in layers:
                M[L][m2] *= w
        return M, H, halo

    # ---- the search
    def _distance(self, targets, free):
        """Distance transform (mm) from the target cells over cells free on any layer."""
        dist = np.full((self.nx, self.ny), np.inf)
        q = []
        for (_, i, j) in targets:
            if dist[i, j] > 0:
                dist[i, j] = 0.0
                q.append((0.0, i, j))
        heapq.heapify(q)
        step = [(di, dj, self.pitch * (SQ2 if di and dj else 1.0)) for di, dj in DIRS]
        while q:
            d, i, j = heapq.heappop(q)
            if d > dist[i, j]:
                continue
            for di, dj, c in step:
                a, b = i + di, j + dj
                if 0 <= a < self.nx and 0 <= b < self.ny and free[a, b]:
                    nd = d + c
                    if nd < dist[a, b]:
                        dist[a, b] = nd
                        heapq.heappush(q, (nd, a, b))
        return dist

    def search(self, net, sources, targets, grids, vgrid, costs, allow_vias=True, bound=None):
        """A*: (path, cost, reason). reason: None on success, 'none' when the search was
        exhausted (no path exists on this grid), 'budget' when it was stopped.

        The grids are read as flat Python lists and a state is one int,
        ((L * nx + i) * ny + j) * 9 + heading: numpy's per-element access was most of the
        time. The arithmetic is the same, term for term, so the result is too."""
        M, H, halo = costs
        nl, nx, ny = self.m.nl, self.nx, self.ny
        free_any = ~np.all(grids, axis=0)
        for (L, i, j) in targets:
            free_any[i, j] = True
        dist = self._distance(targets, free_any).ravel().tolist()
        minm = float(M.min()) if M.size else 1.0
        minm = max(0.05, min(minm, 1.0))
        blk = [grids[L].ravel().tolist() for L in range(nl)]
        vblk = vgrid.ravel().tolist()
        mul = [M[L].ravel().tolist() for L in range(nl)]
        hal = [halo[L].ravel().tolist() for L in range(nl)]
        flo = self.flow.ravel().tolist()
        hm = [(mask.ravel().tolist(), ux, uy, k) for (mask, ux, uy, k) in H]
        targ = {(L * nx + i) * ny + j for (L, i, j) in targets}
        via_mm = self.R.via_cost
        flow_w = self.flow_w
        pitch = self.pitch
        nxy = nx * ny
        moves = []
        for nd, (di, dj) in enumerate(DIRS):
            diag = bool(di and dj)
            moves.append((nd, di, dj, di * ny + dj, pitch * (SQ2 if diag else 1.0), diag, math.hypot(di, dj)))
        INF = float("inf")
        cnt = itertools.count()
        openq, best, came = [], {}, {}
        for (L, i, j) in sources:
            st = ((L * nx + i) * ny + j) * 9 + 8
            best[st] = 0.0
            h = dist[i * ny + j] * minm
            if h != INF:
                heapq.heappush(openq, (h, 0.0, next(cnt), st))
        t0 = time.monotonic()
        nodes = 0
        closed = set()
        push = heapq.heappush
        pop = heapq.heappop
        while openq:
            f, g, _, st = pop(openq)
            if st in closed:
                continue
            closed.add(st)
            nodes += 1
            if nodes > self.budget or (self.time_s and nodes % 2000 == 0 and time.monotonic() - t0 > self.time_s):
                self.stats["nodes"] += nodes
                return None, None, "budget"
            cell, d = divmod(st, 9)
            L, ij = divmod(cell, nxy)
            if cell in targ:
                path = []
                k = st
                while True:
                    c_ = k // 9
                    LL, ij_ = divmod(c_, nxy)
                    q = (LL, ij_ // ny, ij_ % ny)
                    if not path or path[-1] != q:
                        path.append(q)
                    if k not in came:
                        break
                    k = came[k]
                self.stats["nodes"] += nodes
                return path[::-1], g, None
            i, j = divmod(ij, ny)
            bl = blk[L]
            ml = mul[L]
            hl = hal[L]
            for nd, di, dj, off, step, diag, ln in moves:
                a, b = i + di, j + dj
                if not (0 <= a < nx and 0 <= b < ny):
                    continue
                n2 = ij + off
                if bl[n2]:
                    continue
                if diag and (bl[ij + di * ny] or bl[ij + dj]):
                    continue
                mult = ml[n2]
                for (mask, ux, uy, k) in hm:
                    if mask[n2]:
                        cos = (di * ux + dj * uy) / ln
                        mult *= 1.0 + k * (1.0 - cos * cos)
                c = step * mult + step * 2.0 * hl[n2] + step * flow_w * flo[n2]
                if d != 8:
                    t = abs(nd - d)
                    c += TURN_MM[min(t, 8 - t)]
                ng = g + c
                if bound is not None and ng > bound:
                    continue
                ns = ((L * nxy) + n2) * 9 + nd
                if ng < best.get(ns, 1e18):
                    best[ns] = ng
                    came[ns] = st
                    push(openq, (ng + dist[n2] * minm, ng, next(cnt), ns))
            if allow_vias and not vblk[ij]:
                for O in range(nl):
                    if O == L or blk[O][ij]:
                        continue
                    ng = g + via_mm
                    if bound is not None and ng > bound:
                        continue
                    ns = ((O * nxy) + ij) * 9 + d            # the heading carries through the via
                    if ng < best.get(ns, 1e18):
                        best[ns] = ng
                        came[ns] = st
                        push(openq, (ng + dist[ij] * minm, ng, next(cnt), ns))
        self.stats["nodes"] += nodes
        return None, None, "none"

    # ---- pads and laying
    def pad_cells(self, pad, grids):
        """Cells a route may end in for this pad: centres inside its copper, on its layers;
        if none (a pad smaller than the grid), the nearest cell to its centre."""
        out = set()
        g = pad.geom.buffer(-0.02)
        x0, y0, x1, y1 = pad.geom.bounds
        i0, i1, j0, j1 = self._window((x0, y0, x1, y1), 0)
        inside = shapely.contains_xy(g, self.X[i0:i1 + 1, j0:j1 + 1], self.Y[i0:i1 + 1, j0:j1 + 1])
        for a, b in zip(*np.nonzero(inside)):
            for L in pad.layers:
                out.add((L, i0 + int(a), j0 + int(b)))
        if not out:
            i, j = self.ij(*pad.centre)
            for L in pad.layers:
                out.add((L, i, j))
        return out

    def open_pad(self, pad, grids):
        """A pad's cells a route may end in: those inside its copper that the obstacle map
        leaves free - a cell inside the pad can still be too near a neighbour's pad for this
        net's track (a 0.5 mm rail between the pins of a 1.27 mm header). Only if none is
        free is the cell nearest its centre opened, so the pad can be reached at all."""
        cs = self.pad_cells(pad, grids)
        free = {c for c in cs if not grids[c[0]][c[1], c[2]]}
        if free:
            return free
        c = min(cs, key=lambda q: math.dist(self.xy(q[1], q[2]), pad.centre))
        near = {q for q in cs if (q[1], q[2]) == (c[1], c[2])}
        for q in near:
            grids[q[0]][q[1], q[2]] = False
        return near

    def _stub(self, pad, cell_xy, L):
        """Off-grid points from the pad's centre to the path's end cell: straight if that
        is octilinear, else along the pad's longer axis and then octilinear."""
        c = (snap(pad.centre[0]), snap(pad.centre[1]))
        if c == cell_xy:
            return [(c[0], c[1], L)]
        if octilinear(c, cell_xy):
            return [(c[0], c[1], L)]
        x0, y0, x1, y1 = pad.geom.bounds
        dx, dy = cell_xy[0] - c[0], cell_xy[1] - c[1]
        cands = []
        if (x1 - x0) >= (y1 - y0):
            # along x first, then a 45 to the cell
            cands.append((snap(cell_xy[0] - math.copysign(abs(dy), dx)), c[1]))
            cands.append((cell_xy[0], c[1]))
            cands.append((c[0], cell_xy[1]))
        else:
            cands.append((c[0], snap(cell_xy[1] - math.copysign(abs(dx), dy))))
            cands.append((c[0], cell_xy[1]))
            cands.append((cell_xy[0], c[1]))
        for k in cands:
            if octilinear(c, k) and octilinear(k, cell_xy):
                return [(c[0], c[1], L), (k[0], k[1], L)]
        return [(c[0], c[1], L)]

    def build_run(self, net, path, width, pad_of):
        pts = [(*self.xy(i, j), L) for (L, i, j) in path]
        s, e = path[0], path[-1]
        head = []
        if s in pad_of:
            head = self._stub(pad_of[s], pts[0][:2], s[0])
        tail = []
        if e in pad_of:
            tail = [(x, y, L) for (x, y, L) in reversed(self._stub(pad_of[e], pts[-1][:2], e[0]))]
        pts = simplify(head + pts + tail)
        run = Run(net, pts, width, self.R.via_size(net))
        self.apply_field_widths(run)
        return run

    def apply_field_widths(self, run):
        if not any(f.track is not None for f in self.fields):
            return
        ws = []
        for a, b in zip(run.pts, run.pts[1:]):
            if a[2] != b[2]:
                continue
            w, _ = local_values(self.fields, self.R, run.net, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            ws.append(snap(w, 0.01))
        run.widths = ws

    def connect(self, net, sources, targets, pad_of, width, grids, vgrid, costs, extra_block=()):
        """One connection: sketch, then lay what fits; a rejected sketch blocks the cells
        round what failed and searches again (counted: sketch-to-lay rejections)."""
        grids = grids.copy()
        vgrid = vgrid.copy()
        last = None
        for attempt in range(8):
            path, cost, why = self.search(net, sources, targets, grids, vgrid, costs)
            if path is None:
                return None, why
            # single-layer first: a via-free path within via_first_ratio of this one
            if any(a[0] != b[0] for a, b in zip(path, path[1:])):
                p1, c1, _ = self.search(net, {s for s in sources}, targets, grids, vgrid, costs,
                                        allow_vias=False, bound=cost * self.R.via_first_ratio)
                if p1 is not None:
                    self.stats["single_layer_taken"] += 1
                    path, cost = p1, c1
            run = self.build_run(net, path, width, pad_of)
            bad = fits(run, self.m, self.fields, self.fence)
            if not bad:
                return run, None
            last = bad
            self.stats["rejected"] += 1
            for what, (x, y), _ in bad:
                i, j = self.ij(x, y)
                for a in range(max(0, i - 1), min(self.nx, i + 2)):
                    for b in range(max(0, j - 1), min(self.ny, j + 2)):
                        if (0, a, b) in targets or any((L, a, b) in targets or (L, a, b) in sources for L in range(self.m.nl)):
                            continue
                        for L in range(self.m.nl):
                            grids[L][a, b] = True
                        vgrid[a, b] = True
        return None, "lay: " + "; ".join(f"{w} at {p}" for w, p, _ in last[:3])

    def route_net(self, net, pads=None, partial=False):
        """A net as a tree: from the pad nearest the middle, each time the nearest pad not
        yet joined. Returns (ok, [runs], reason). With `pads`, only those are joined (a
        connect_first pair); without, every pad AND every fragment of the net's copper."""
        whole = pads is None
        pads = pads if pads is not None else self.m.pads_of(net)
        if len(pads) < 2:
            return True, [], None
        width = self.R.width(net)
        grids, vgrid = self.blocked(net, width)
        costs = self.costs(net, width)
        cells = {}
        pad_of = {}
        for p in pads:
            cs = self.open_pad(p, grids)
            cells[p.name] = cs
            for c in cs:
                pad_of[c] = p
        # the net's copper already on the board (a connect_first run, a locked hand route, an
        # escape stub) and its pads, in GROUPS of what really touches - a via, or a plated
        # pad, joining its layers. Two fragments of a net are two groups even when each
        # touches a pad: they are joined only by a route between them.
        own = self.m.index.of_net(net)
        items = [("pad", p, set(p.layers), p.geom) for p in pads] + [("cu", e, set(e.layers), e.geom) for e in own]
        parent = list(range(len(items)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if items[i][2] & items[j][2] and items[i][3].intersects(items[j][3]):
                    parent[find(i)] = find(j)
        bunch = {}
        for i in range(len(items)):
            bunch.setdefault(find(i), []).append(i)
        groups_ = []                    # [(pads, cells)]: a fragment with no pad is a group too -
        for idx in bunch.values():      # left unjoined it is a dangling piece of the net
            gp = [items[i][1] for i in idx if items[i][0] == "pad"]
            gc = set().union(*(cells[p.name] for p in gp)) if gp else set()
            cu = [items[i][1] for i in idx if items[i][0] == "cu"]
            if cu:
                gc |= self._cells_of(cu)
            groups_.append((gp, gc))
        groups_ = [g for g in groups_ if g[1] and (g[0] or whole)]
        cx = sum(p.centre[0] for p in pads) / len(pads)
        cy = sum(p.centre[1] for p in pads) / len(pads)
        groups_.sort(key=lambda g: (-len(g[0]), min((math.hypot(p.centre[0] - cx, p.centre[1] - cy) for p in g[0]), default=1e9)))
        joined, tree = list(groups_[0][0]), set(groups_[0][1])
        todo = groups_[1:]
        runs, groups = [], []
        while todo:
            targets = set()
            owner = {}
            for k, (gp, gc) in enumerate(todo):
                targets |= gc
                for c in gc:
                    owner[c] = k
            run, why = self.connect(net, tree, targets, pad_of, width, grids, vgrid, costs)
            if run is None:
                if not partial:
                    return False, runs, why
                groups.append(joined)
                gp, gc = todo.pop(0)
                joined, tree = list(gp), set(gc)
                continue
            lay(run, self.m)
            runs.append(run)
            self.runs.append(run)
            # the group it reached: the one owning the cell the path ended in
            end = run.pts[-1]
            k = owner.get((end[2], *self.ij(end[0], end[1])))
            if k is None:
                k = min(range(len(todo)), key=lambda q: min((math.dist(self.xy(c[1], c[2]), end[:2]) for c in todo[q][1]), default=1e9))
            gp, gc = todo.pop(k)
            joined += gp
            tree |= gc | self._run_cells(run)
            # the new copper is this net's own: unblock its cells
            for c in self._run_cells(run):
                grids[c[0]][c[1], c[2]] = False
        groups.append(joined)
        self.groups = getattr(self, "groups", {})
        self.groups[net] = groups
        return len(groups) == 1, runs, None if len(groups) == 1 else f"{len(groups)} group(s)"

    def _touches(self, e, pad):
        return e.geom.intersects(pad.geom)

    def _cells_of(self, entries):
        out = set()
        for e in entries:
            i0, i1, j0, j1 = self._window(e.geom.bounds, 0)
            sub = shapely.contains_xy(e.geom, self.X[i0:i1 + 1, j0:j1 + 1], self.Y[i0:i1 + 1, j0:j1 + 1])
            for a, b in zip(*np.nonzero(sub)):
                for L in e.layers:
                    out.add((L, i0 + int(a), j0 + int(b)))
        return out

    def _run_cells(self, run):
        out = set()
        for L, a, b, _ in run.segments():
            n = max(1, int(math.dist(a, b) / (self.pitch / 2)))
            for k in range(n + 1):
                x = a[0] + (b[0] - a[0]) * k / n
                y = a[1] + (b[1] - a[1]) * k / n
                i, j = self.ij(x, y)
                if 0 <= i < self.nx and 0 <= j < self.ny:
                    out.add((L, i, j))
        for x, y in run.vias():
            i, j = self.ij(x, y)
            for L in range(self.m.nl):
                out.add((L, i, j))
        return out

    # ---- order and flow
    def airwires(self, nets):
        """Each net's minimum spanning tree over its pad centres: [(net, a, b)]."""
        out = []
        for n in nets:
            ps = [p.centre for p in self.m.pads_of(n)]
            if len(ps) < 2:
                continue
            inn, rest = [ps[0]], ps[1:]
            while rest:
                a, b = min(((a, b) for a in inn for b in rest), key=lambda ab: math.dist(*ab))
                out.append((n, a, b))
                inn.append(b)
                rest.remove(b)
        return out

    def order(self, nets, first=()):
        """route_first, then power, then fewest airwire crossings, then shortest."""
        aw = self.airwires(nets)
        cr = airwire_crossings(aw)
        per, span = defaultdict(int), defaultdict(float)
        for (n, a, b), c in zip(aw, cr):
            per[n] += c
            span[n] += math.dist(a, b)
        first = list(first)
        return sorted(nets, key=lambda n: (n not in first, first.index(n) if n in first else 0,
                                          n not in self.R.power, per[n], span[n], n))

    def set_flow(self, pending):
        self.flow[:] = 0
        if not self.flow_w:
            return
        for n, a, b in self.airwires(pending):
            ln = LineString([a, b]).buffer(0.75)
            m = np.zeros((self.nx, self.ny), dtype=bool)
            self._mark(m, ln, 0)
            self.flow[m] += 1.0

    # ---- families: a bus reserves its corridor
    def reserve_bus(self, fam):
        """Sketch one centreline for the family's corridor - n pitches plus clearance wide -
        and reserve it for the family's nets. Returns the reservation entry, or None."""
        nets = fam["nets"]
        pitch = float(fam.get("pitch", self.R.width(nets[0]) + self.R.clear(nets[0])))
        ends = []
        for n in nets:
            ps = self.m.pads_of(n)
            if len(ps) != 2:
                return None
            ends.append(sorted(ps, key=lambda p: (p.centre[0], p.centre[1])))
        A = (sum(e[0].centre[0] for e in ends) / len(ends), sum(e[0].centre[1] for e in ends) / len(ends))
        B = (sum(e[1].centre[0] for e in ends) / len(ends), sum(e[1].centre[1] for e in ends) / len(ends))
        width = len(nets) * pitch
        tag = "family:" + fam.get("name", "bus")
        grids, vgrid = self.blocked(tag, width)
        layer = self.m.layer_names.index(fam.get("layer", self.m.layer_names[0]))
        costs = self.costs(tag, width)
        # the corridor runs between the two pad groups' fronts: start and end just outside them
        # the lanes start clear of the pads: past the wider pad group's spread, so each lead-in
        # has room to fan from its pad's pitch to the lane's
        spread = max(max(math.dist(e[0].centre, f[0].centre) for e in ends for f in ends),
                     max(math.dist(e[1].centre, f[1].centre) for e in ends for f in ends))
        gap = float(fam.get("lead", spread + 1.5))
        u = _unit(B[0] - A[0], B[1] - A[1])
        A2 = (A[0] + u[0] * gap, A[1] + u[1] * gap)
        B2 = (B[0] - u[0] * gap, B[1] - u[1] * gap)
        sa, sb = self.ij(*A2), self.ij(*B2)
        src, dst = {(layer, *sa)}, {(layer, *sb)}
        for (L, i, j) in src | dst:
            grids[L][i, j] = False
        path, _, why = self.search(tag, src, dst, grids, vgrid, costs, allow_vias=False)
        if path is None:
            self.log.append(f"family {tag}: no corridor ({why})")
            return None
        pts = [self.xy(i, j) for (_, i, j) in path]
        line = LineString(pts).simplify(0) if len(pts) > 1 else Point(pts[0])
        corridor = line.buffer(width / 2, cap_style="flat")
        e = self.m.index.add(net=None, layers=[layer], geom=corridor, kind="reserve", locked=False, family=set(nets))
        self.corridors = getattr(self, "corridors", {})
        self.corridors[tag] = (line, width, pitch, layer)
        return e

    # ---- whole boards
    def route(self, nets=None, first=(), families=(), ground=None, connect_first=(), rescue=True):
        """Route every net (or `nets`): families first, then the rest in crossing-aware
        order, then ground. Returns {net: reason} for every net that failed."""
        P = self.m.planes
        # a plane net is joined by its plane: its pads get their vias (fanout), not tracks
        nets = list(nets) if nets is not None else [n for n in self.m.nets() if n != ground
                                                    and not (P and n in P.plane_nets)]
        failed = {}
        done = set()
        if P is not None and P.fanout_nets:
            self.fanout()
        # layout.yaml connect_first: pad-to-pad connections laid before anything else, each in
        # its own track (pcb.py check holds each to its max_mm); the net's own route joins them
        for spec in connect_first:
            pa, pb = (next((p for p in self.m.pads if p.name == n), None) for n in spec["pads"])
            if pa is None or pb is None or pa.net != pb.net:
                self.log.append(f"connect_first {spec['pads']}: not two pads of one net")
                continue
            ok, _, why = self.route_net(pa.net, pads=[pa, pb])
            self.log.append(f"connect_first {pa.name} - {pb.name}: {'ok' if ok else 'FAILED ' + str(why)}")
        for fam in families:
            res = None
            fields_before = list(self.fields)
            if fam.get("bus"):
                res = self.reserve_bus(fam)
                if res is not None:
                    line, width, pitch, layer = self.corridors["family:" + fam.get("name", "bus")]
                    x0, y0, x1, y1 = res.geom.bounds
                    # members prefer their corridor
                    self.fields.append(Field((x0, y0, x1, y1), weight=0.6, nets=fam["nets"]))
            fnets = [n for n in self.order(fam["nets"], first) if n in nets]
            if fam.get("bus") and res is not None:
                # across the corridor in the order their pads stand
                line = self.corridors["family:" + fam.get("name", "bus")][0]
                fnets = sorted(fnets, key=lambda n: self._side(line, n))
            for k, n in enumerate(fnets):
                self.set_flow([m for m in nets if m not in done and m != n])
                ok = False
                if fam.get("bus") and res is not None:
                    ok = self.route_bus_member(n, "family:" + fam.get("name", "bus"), k, len(fnets))
                    why = None if ok else "off its lane"
                if not ok:
                    ok, _, why = self.route_net(n)
                done.add(n)
                if not ok:
                    failed[n] = why
            if res is not None:
                self.m.index.remove(res.id)
            self.fields = fields_before
        rest = [n for n in self.order(nets, first) if n not in done]
        for n in rest:
            self.set_flow([m for m in nets if m not in done and m != n])
            ok, _, why = self.route_net(n)
            done.add(n)
            if not ok:
                failed[n] = why
                self.log.append(f"route: {n} failed - {why}")
        # rescue BEFORE the ground: ground is routed last, may stay in groups and is stitched -
        # a rescue that took it up and laid it again as a plain net would wall the rest in
        if rescue:
            self.ground = ground
            for n in list(failed):
                if self.rescue(n):
                    failed.pop(n)
        if ground:
            self.route_ground(ground)
        return failed

    def route_bus_member(self, net, tag, k, n):
        """Member k of n laid on its own lane: the corridor's centreline offset by
        (k - (n - 1) / 2) pitches (members ordered across it as their pads stand), joined to
        its two pads by short searches. False (and nothing laid) if the lane does not fit."""
        line, width, pitch, layer = self.corridors[tag]
        if line.geom_type != "LineString" or line.length < 1e-6:
            return False
        d = (k - (n - 1) / 2) * pitch
        lane = line if abs(d) < 1e-9 else line.offset_curve(d, join_style="mitre")
        if lane.is_empty or lane.geom_type != "LineString":
            self.log.append(f"bus {tag}: {net} has no lane at offset {d:+.2f}")
            return False
        lpts = [(snap(x), snap(y)) for x, y in lane.coords]
        pads = self.m.pads_of(net)
        if len(pads) != 2:
            return False
        pa = min(pads, key=lambda p: math.dist(p.centre, lpts[0]))
        pb = [p for p in pads if p is not pa][0]
        w = self.R.width(net)
        grids, vgrid = self.blocked(net, w)
        costs = self.costs(net, w)
        pad_of = {}
        for p in (pa, pb):
            for c in self.open_pad(p, grids):
                pad_of[c] = p
        pieces = []
        for pad, end in ((pa, lpts[0]), (pb, lpts[-1])):
            i, j = self.ij(*end)
            if not (0 <= i < self.nx and 0 <= j < self.ny):
                return False
            grids[layer][i, j] = False
            src = {c for c in pad_of if pad_of[c] is pad}
            path, _, why = self.search(net, src, {(layer, i, j)}, grids, vgrid, costs, allow_vias=False)
            if path is None:
                self.log.append(f"bus {tag}: {net} cannot reach its lane from {pad.name} ({why})")
                return False
            pieces.append(path)
        lead_in = [(*self.xy(i, j), L) for (L, i, j) in pieces[0]]
        lead_out = [(*self.xy(i, j), L) for (L, i, j) in reversed(pieces[1])]
        head = self._stub(pa, lead_in[0][:2], lead_in[0][2]) if pieces[0][0] in pad_of else []
        tail = list(reversed(self._stub(pb, lead_out[-1][:2], lead_out[-1][2]))) if pieces[1][0] in pad_of else []
        pts = simplify(head + lead_in[:-1] + [(x, y, layer) for x, y in lpts] + lead_out[1:] + tail)
        run = Run(net, pts, w, self.R.via_size(net))
        bad = fits(run, self.m, self.fields, self.fence)
        if bad:
            self.log.append(f"bus {tag}: {net} off its lane - {bad[0][0]} at {bad[0][1]}")
            return False
        lay(run, self.m)
        self.runs.append(run)
        return True

    def _side(self, line, net):
        ps = self.m.pads_of(net)
        p = min(ps, key=lambda q: line.project(Point(q.centre)))
        a = line.interpolate(0)
        b = line.interpolate(min(line.length, 1.0))
        return (b.x - a.x) * (p.centre[1] - a.y) - (b.y - a.y) * (p.centre[0] - a.x)

    # ---- ground: route as a net, stitch, pour (the pour is written by write())
    def route_ground(self, gnd):
        ok, runs, why = self.route_net(gnd, partial=True)
        groups = self.groups.get(gnd, [])
        main = set(p.name for p in max(groups, key=len)) if groups else set()
        n = 0
        for p in self.m.pads_of(gnd):
            if len(p.layers) != 1 or p.name in main:
                continue
            if self.stitch(p):
                n += 1
        # the pours on the two faces are one net only if something joins them: a via of the
        # net, or a plated pad. A tree with neither (all on one face) gets one stitching via.
        # (the main group's own copper: its tree runs, not the other groups' stitches)
        joined = any(r.vias() for r in runs) or any(len(p.layers) > 1 for p in self.m.pads_of(gnd) if p.name in main)
        if not joined and self.m.nl > 1:
            for p in sorted(self.m.pads_of(gnd), key=lambda q: q.name):
                if p.name in main and len(p.layers) == 1 and self.stitch(p):
                    n += 1
                    break
        self.log.append(f"ground {gnd}: {'one tree' if ok else why}, {n} stitching via(s)")
        self.ground = gnd
        return ok

    def stitch(self, pad):
        """A via beside a single-sided pad, joined by a short stub, into the other layers."""
        L = next(iter(pad.layers))
        d, _ = self.R.via_size(pad.net)
        w = self.R.width(pad.net)
        c = pad.centre
        x0, y0, x1, y1 = pad.geom.bounds
        reach = max(x1 - x0, y1 - y0) / 2
        for r in [reach + d / 2 + k * LATTICE * 2 for k in range(0, 30)]:
            for a in range(0, 360, 45):
                x, y = snap(c[0] + r * math.cos(math.radians(a))), snap(c[1] + r * math.sin(math.radians(a)))
                run = Run(pad.net, [(snap(c[0]), snap(c[1]), L), (x, y, L), (x, y, 1 - L if self.m.nl == 2 else self.m.nl - 1)],
                          w, self.R.via_size(pad.net))
                if not fits(run, self.m, self.fields, self.fence):
                    lay(run, self.m)
                    self.runs.append(run)
                    return run
        return None

    # ---- family by family, with a review between
    def stage(self, families, board=None, checkpoint=None, ground=None, connect_first=(), first=(),
              detour=1.8, pull=1.0, fillet=0.0, liquid=True, plot=None, edits=None, start=1, stop=None, pause=False):
        """Route a board in FAMILIES, one at a time, each reviewed and adjusted before the next
        is let near it (the owner, 2026-10-05 and 2026-10-10: "do families of traces... then
        the next ones", "review it and push the traces around with the liquid tools, then hand
        it off to the next family"). Each family:
          1. routed alone - every earlier family is LOCKED, so neither its rip-up nor its
             rescue can touch them;
          2. a net still open is PUSHED in: routed again past this family's copper, which is
             shoved aside (Router.reroute), before anything is given up;
          3. reviewed: each net longer than `detour` x its airwires routed again with a `pull`
             corridor, kept only if shorter;
          4. EDITED: `edits[family]`, the reviewer's own moves (Router.edit), in order;
          5. the liquid pass (rubber band, fold, slide, equalise, fillet) over this family;
          6. locked, written to `board` and saved as a checkpoint (checkpoint(k, name) ->
             path), with a plot if `plot(k, name, nets, path) -> png` is given.
        `start`/`stop`: route families start..stop only (1-based) - to stop at a family for
        review, and to go on from its checkpoint in a later run (the model built from the
        checkpoint board, whose families' copper it reads as locked). `pause`: stop after the
        first family whose `review` is not empty - what it could not settle itself (a net
        open, a net pushed in or rescued - other copper moved for it -, a detour not cured,
        an edit that failed): the point to hand
        the board to a reviewer. Unlocked copper the board came with (Router.adopt) is
        routed, liquid-passed and written with the family that owns its net.
        `families`: [{name, nets: [names or fnmatch globs], first?, layers?}] - a net claimed
        by an earlier family is not routed again; whatever no family names goes last, as
        "rest". Returns [{family, nets, failed, pushed, rerouted, edits, liquid, runs,
        length_mm, vias, review, paused?}] for the families routed."""
        import fnmatch
        P = self.m.planes
        allnets = [n for n in self.m.nets() if n != ground and not (P and n in P.plane_nets)]
        claimed, plan = set(), []
        for fam in families:
            pats = fam["nets"]
            mine = [n for n in allnets if n not in claimed and any(n == p_ or fnmatch.fnmatch(n, p_) for p_ in pats)]
            claimed |= set(mine)
            plan.append((fam, mine))
        rest = [n for n in allnets if n not in claimed]
        if rest:
            plan.append(({"name": "rest"}, rest))
        if P is not None and P.fanout_nets:
            self.fanout()               # a pad that has its via already (a checkpoint's) is skipped
        for spec in connect_first:
            pa, pb = (next((p for p in self.m.pads if p.name == n), None) for n in spec["pads"])
            if pa is not None and pb is not None and pa.net == pb.net:
                ok, runs, _ = self.route_net(pa.net, pads=[pa, pb])
                for r_ in runs:
                    self._lock(r_)
                self.log.append(f"connect_first {pa.name} - {pb.name}: {'ok' if ok else 'FAILED'}")
        # what came before the families - the plane fanout, the connect_first runs - is fixed
        # and written first
        pre = [r_ for r_ in self.runs if not getattr(r_, "adopted", False)]
        for r_ in pre:
            self._lock(r_)
        if board is not None and pre:
            write(board, self.m, pre)
        report = []
        edits = edits or {}
        for k, (fam, nets) in enumerate(plan, 1):
            name = fam.get("name", f"family {k}")
            if k < start or (stop is not None and k > stop):
                continue
            before = set(id(r_) for r_ in self.runs)
            saved_cls = {}
            if fam.get("layers"):           # a family's layers narrow its nets' own
                for n in nets:
                    saved_cls[n] = self.R.of.get(n)
                    self.R.of[n] = dict(self.R.cls(n), layers=list(fam["layers"]))
            # a family's own `first:` leads it (the chain's clock before the lines beside it:
            # laid last, the longest tree found its corridor taken - the main board, run 3)
            lead = [n for p_ in fam.get("first") or [] for n in nets if n == p_ or fnmatch.fnmatch(n, p_)]
            log0 = len(self.log)
            failed = self.route(nets, first=lead + [n for n in first if n in nets and n not in lead], rescue=True)
            rescued = [l_[len("rescue: "):] for l_ in self.log[log0:] if l_.startswith("rescue: ")]
            # 2. pushed in: past this family's copper, shoved aside (earlier families are locked)
            pushed = []
            for n in list(failed):
                rep = self.reroute(n)
                if rep["mode"] in ("shove", "direct", "walkaround"):
                    failed.pop(n)
                    pushed.append((n, rep["mode"], rep["shoved"]))
                self.log.append(f"stage {name}: {n} pushed in - {rep['mode']}" + (f", shoved {rep['shoved']}" if rep["shoved"] else ""))
            # 3. the review: detours routed again with a pull
            rerouted = []
            for n in nets:
                if n in failed:
                    continue
                aw = sum(math.dist(a, b) for _, a, b in self.airwires([n]))
                ln = sum(r_.length() for r_ in self.runs_of(n))
                if aw > 0 and ln > detour * aw:
                    rep = self.reroute(n, pull=pull)
                    after = sum(r_.length() for r_ in self.runs_of(n))
                    rerouted.append((n, round(ln, 1), round(after, 1), rep.get("mode")))
            # 4. the reviewer's own moves
            done_edits = []
            for spec in edits.get(name, []):
                rep = self.edit(spec)
                done_edits.append(rep)
                self.log.append(f"stage {name}: edit {rep}")
                if rep.get("ok"):
                    # the reviewer's move stands: pinned now, so the liquid pass that follows
                    # cannot straighten it back (it took M back through the rectangle it had
                    # been moved out of - the edits test board)
                    for r_ in self.runs_of(rep["net"]):
                        self._lock(r_)
                    failed.pop(rep["net"], None)
            # 5. the liquid pass, over this family alone (everything earlier is locked)
            liq = self.liquid(fillet) if liquid else None
            for n, saved in saved_cls.items():
                if saved is None:
                    self.R.of.pop(n, None)
                else:
                    self.R.of[n] = saved
            # this family's copper: what it laid (a later family's net it shoved included), and
            # every adopted piece of each of those nets - a net's board copper is replaced whole,
            # by the family that writes it
            new = [r_ for r_ in self.runs if id(r_) not in before]
            wnets = set(nets) | {r_.net for r_ in new}
            mine = new + [r_ for r_ in self.runs if id(r_) in before and getattr(r_, "adopted", False) and r_.net in wnets]
            for r_ in mine:
                self._lock(r_)
                r_.adopted = False
            gone_items = [it for n in sorted(wnets) for it in getattr(self, "_adopted_items", {}).pop(n, [])]
            rec = {"family": name, "nets": len(nets), "failed": dict(failed), "pushed": pushed, "rerouted": rerouted,
                   "edits": done_edits, "liquid": liq, "runs": len(mine),
                   "length_mm": round(sum(r_.length() for r_ in mine), 1), "vias": sum(len(r_.vias()) for r_ in mine)}
            # WHEN A REVIEWER IS WANTED: what the family could not settle itself - a net still
            # open, a net pushed in (others moved for it), a detour the pull did not cure,
            # an edit that failed. Empty: the family needs no one.
            why = [f"open: {n}" for n in failed] + [f"pushed in: {n} (shoved {', '.join(sh) or 'nothing'})" for n, _, sh in pushed]
            why += [f"rescued: {x}" for x in rescued]          # copper ripped up and laid again
            why += [f"still long: {n} {a} mm" for n, b_, a, _ in rerouted if a > b_ - 1e-6]
            why += [f"edit failed: {e['edit']} {e['net']} - {e.get('why') or e.get('mode')}" for e in done_edits if not e["ok"]]
            rec["review"] = why
            report.append(rec)
            self.log.append(f"stage {k} {name}: {rec['nets']} net(s), {rec['runs']} run(s), {rec['length_mm']} mm, "
                            f"{rec['vias']} via(s); failed {list(failed) or 'none'}; pushed in {len(pushed)}; "
                            f"detours re-routed {len(rerouted)}; edits {len(done_edits)}; liquid {liq}")
            if board is not None:
                for it in gone_items:
                    board.Delete(it)
                write(board, self.m, mine)
                if checkpoint:
                    path = checkpoint(k, name)
                    _kicad().SaveBoard(path, board)
                    rec["checkpoint"] = path
                    if plot:
                        rec["plot"] = plot(k, name, nets, path)
            if pause and rec["review"]:
                rec["paused"] = True
                self.log.append(f"stage {k} {name}: paused for review - {'; '.join(rec['review'])}")
                return report
        if ground and (stop is None or stop >= len(plan)):
            before = set(id(r_) for r_ in self.runs)
            self.route_ground(ground)
            if board is not None:
                write(board, self.m, [r_ for r_ in self.runs if id(r_) not in before])
        return report

    def adopt(self, nets=None):
        """The board's UNLOCKED copper made this router's own: each track segment and via a
        Run of its own, laid in its place, its board item deleted at write. A partly routed
        board keeps what it has, yet a push may shove it - board copper the router did not
        lay was an obstacle nothing could move (the partial test board). A piece that does
        not fit as a Run (off the lattice into a clearance) stays as it was. Returns how
        many pieces were adopted."""
        pcbnew = _kicad()
        n = 0
        if not hasattr(self, "_adopted_items"):
            self._adopted_items = {}
        for e in sorted(self.m.index.e.values(), key=lambda e: e.id):
            if e.kind not in ("track", "via") or e.locked or e.run is not None or e.item is None:
                continue
            if nets is not None and e.net not in nets:
                continue
            t = e.item
            if e.kind == "via":
                c = e.geom.centroid
                run = Run(e.net, [(c.x, c.y, 0), (c.x, c.y, self.m.nl - 1)], self.R.width(e.net),
                          via=(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)), e.drill))
            else:
                (x0, y0), (x1, y1) = list(e.line.coords)[0], list(e.line.coords)[-1]
                L = next(iter(e.layers))
                run = Run(e.net, [(x0, y0, L), (x1, y1, L)], pcbnew.ToMM(t.GetWidth()), via=self.R.via_size(e.net))
            self.m.index.remove(e.id)
            if fits(run, self.m, self.fields, self.fence):
                self.m.index.add(net=e.net, layers=e.layers, geom=e.geom, kind=e.kind, locked=False, drill=e.drill,
                                 item=t, line=e.line)
                continue
            lay(run, self.m)
            run.adopted = True
            self.runs.append(run)
            # its board item goes when the family that writes this net's copper writes it -
            # not at the first write, or a run stopped before that family would lose it
            self._adopted_items.setdefault(e.net, []).append(t)
            n += 1
        self.log.append(f"adopt: {n} piece(s) of the board's unlocked copper")
        return n

    def edit(self, spec):
        """One reviewer's move on an unlocked net - the liquid tools by hand. Each re-routes
        the net with a shove (Router.reroute: what stands in its way is laid again near its
        old path), all or nothing; a failed edit leaves the board as it was.
          {reroute: net, pull?: mm}           - again, kept to a corridor `pull` wide
          {through: net, points: [[x, y]..], width?: mm}
                                              - by those points in order: cheap inside a
                                                corridor `width` either side of the
                                                pad-points-pad line, dear outside it
          {clear: net, rect: [x0, y0, x1, y1]} - out of that rectangle (dear inside it)
        Returns {edit, net, ok, mode, shoved, before, after, why?}."""
        net = spec.get("reroute") or spec.get("through") or spec.get("clear")
        kind = "reroute" if "reroute" in spec else "through" if "through" in spec else "clear" if "clear" in spec else None
        out = {"edit": kind, "net": net, "ok": False}
        if kind is None or net not in self.m.nets():
            out["why"] = "no such edit or net"
            return out
        if any(r.locked for r in self.runs_of(net)):
            out["why"] = "locked"
            return out
        saved = list(self.fields)
        try:
            if kind == "through":
                w = float(spec.get("width", 1.0))
                ps = self.m.pads_of(net)
                pts = [tuple(p) for p in spec["points"]]
                a = min(ps, key=lambda p: math.dist(p.centre, pts[0])).centre
                b = min(ps, key=lambda p: math.dist(p.centre, pts[-1])).centre
                line = [a] + pts + [b]
                xs = [x for x, _ in line]
                ys = [y for _, y in line]
                self.fields.append(Field((min(xs) - 50, min(ys) - 50, max(xs) + 50, max(ys) + 50), weight=6.0, nets=[net]))
                # the corridor: the pad-points-pad line, `w` either side (not each leg's
                # bounding box: a diagonal leg's box takes in the straight way it is to leave)
                self.fields.append(Field(None, weight=1.0 / 6.0, nets=[net], geom=LineString(line).buffer(w)))
            elif kind == "clear":
                self.fields.append(Field(spec["rect"], weight=40.0, nets=[net]))
            rep = self.reroute(net, pull=spec.get("pull"))
        finally:
            self.fields = saved
        out.update(mode=rep["mode"], shoved=rep["shoved"], before=round(rep.get("before", 0.0), 2),
                   after=round(rep.get("after", 0.0), 2))
        ok = rep["mode"] in ("shove", "direct", "walkaround")
        # verified on the COPPER, not the centreline: a track half its width into the
        # rectangle is in it
        geo = [(LineString([(x, y) for x, y, _ in r.pts]) if len(r.pts) > 1 else Point(r.pts[0][:2])).buffer(r.width / 2)
               for r in self.runs_of(net)]
        if ok and kind == "through":
            far = [p for p in spec["points"] if min(g.distance(Point(p)) for g in geo) > float(spec.get("width", 1.0)) + 1e-6]
            if far:
                ok, out["why"] = False, f"routed, but not by {far}"
        if ok and kind == "clear":
            if any(g.intersects(box(*spec["rect"])) for g in geo):
                ok, out["why"] = False, "routed, but still in the rectangle"
        out["ok"] = ok
        return out

    def _unlock(self, run):
        run.locked = False
        for eid in run.entries:
            if eid in self.m.index.e:
                self.m.index.e[eid].locked = False

    def _lock(self, run):
        """A run made fixed: no later rip-up, rescue, shove or liquid pass moves it."""
        run.locked = True
        for eid in run.entries:
            if eid in self.m.index.e:
                self.m.index.e[eid].locked = True

    # ---- four layers: each plane pad's own via
    def fanout(self, only=None, region=None):
        """Every SMD pad of a layout.yaml `fanout:` net gets its own via into its plane on a
        short straight stub from the pad's centre: the nearest spot, searching away from the
        part first, where the via stands inside the net's plane region (by its radius and
        0.3 mm), keeps every via rule of the Planes, and the stub and via pass `fits`. A
        through-hole pad meets the plane itself (unless `fanout_through:` names it), and so
        does a plated hole's face pad; an island's `off_island:` pad is left to the route
        that serves it. The vias and stubs are LOCKED: nothing after moves them. `only`:
        these pads ("REF.NUM"); `region`: {net: geometry} to stand in instead (the orphan
        pass: the body of the fill). Returns the pads no via fits by."""
        P = self.m.planes
        if P is None:
            return []
        skip = {n for i in P.islands for n in i["off_island"]}
        missed, n = [], 0
        for pad in sorted(self.m.pads, key=lambda p: (p.ref, p.num)):
            name = pad.name
            if pad.net not in P.fanout_nets or (only is not None and name not in only) or name in skip:
                continue
            through = name in P.fanout_through or (only is not None and not pad.smd)
            if (not pad.smd and not through) or pad.face_of_hole or len(pad.layers) != 1:
                continue
            if only is None and any(e.net == pad.net and e.kind in ("track", "via") and e.geom.intersects(pad.geom)
                                    for e in self.m.index.query(pad.geom.bounds)):
                continue            # already has its copper (a locked fanout, a hand route)
            L = next(iter(pad.layers))
            reg = (region or {}).get(pad.net, P.region.get(pad.net))
            if reg is None:
                missed.append(f"{name} ({pad.net}): no plane region")
                continue
            d, drill = self.R.via_size(pad.net)
            room = reg.buffer(-(d / 2 + 0.3))
            w = self.R.width(pad.net)
            plane_L = next((k for k, v in P.layer_net.items() if v == pad.net), None)
            if plane_L is None:
                plane_L = next((i["layer"] for i in P.islands if i["net"] == pad.net), (L + 1) % self.m.nl)
            c = (snap(pad.centre[0]), snap(pad.centre[1]))
            fp = [q for q in self.m.pads if q.ref == pad.ref]
            fx, fy = (sum(q.centre[0] for q in fp) / len(fp), sum(q.centre[1] for q in fp) / len(fp))
            away = math.atan2(c[1] - fy, c[0] - fx) if math.dist(c, (fx, fy)) > 0.05 else 0.0
            # where the stub may start: the pad's centre, else inside it on the side away from
            # its part (a net tie's two pads touch: a stub from the centre passes too near the
            # other's copper for KiCad's DRC, which grants a tie no clearance exemption)
            x0, y0, x1, y1 = pad.geom.bounds
            ext = max(0.0, min(x1 - x0, y1 - y0) / 2 - w / 2 - 0.02)
            starts = [c] + ([(snap(c[0] + math.cos(away) * ext), snap(c[1] + math.sin(away) * ext))] if ext > 0.05 else [])
            for _ in range(int(P.fanout_count.get(name, 1))):
                found = None
                for k in range(3, 41):
                    r = k * 0.1
                    for da in range(0, 181, 15):
                        for sgn in ((1,) if da in (0, 180) else (1, -1)):
                            a = away + sgn * math.radians(da)
                            x, y = snap(c[0] + r * math.cos(a)), snap(c[1] + r * math.sin(a))
                            pt = Point(x, y)
                            if pad.geom.buffer(d / 2 + OWN_PAD_GAP).contains(pt) or not room.contains(pt):
                                continue
                            for s0 in starts:
                                run = Run(pad.net, [(s0[0], s0[1], L), (x, y, L), (x, y, plane_L)], w, (d, drill), locked=True)
                                if not fits(run, self.m, self.fields, self.fence):
                                    found = run
                                    break
                            if found:
                                break
                        if found:
                            break
                    if found:
                        break
                if not found:
                    missed.append(f"{name} ({pad.net}): no legal via within 4 mm")
                    break
                lay(found, self.m)
                self.runs.append(found)
                n += 1
        self.log.append(f"fanout: {n} plane via(s); {len(missed)} pad(s) without one" + ("".join("\n  " + m_ for m_ in missed)))
        return missed

    # ---- rescue
    def rescue(self, net, radii=(1.5, 3.0, 5.0), orders=4):
        """Take up the unlocked copper of other nets in a box round the failed net's pads and
        lay the set again: the failed net first, then the taken-up ones, and whatever fails
        moves to the front for the next order, up to `orders` orders. Kept only if every net
        of the set routes; else all put back. Never locked copper, never a net with copper
        outside the fence, never the ground."""
        ps = self.m.pads_of(net)
        xs = [p.centre[0] for p in ps]
        ys = [p.centre[1] for p in ps]
        for r in radii:
            bx = box(min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r)
            victims = sorted({e.run.net for e in self.m.index.query(bx.bounds) if e.kind in ("track", "via") and e.run
                              and e.net != net and not e.locked and e.geom.intersects(bx)})
            victims = [v for v in victims if not self._fixed(v) and v != getattr(self, "ground", None)]
            victims = self.order(victims)           # laid again in the router's own order: power first
            if not victims:
                self.log.append(f"rescue {net}, {r} mm box: nothing that may be taken up")
                continue
            saved = {v: [r_ for r_ in self.runs if r_.net == v] for v in victims}
            for v in victims:
                for r_ in saved[v]:
                    unlay(r_, self.m)
                    self.runs.remove(r_)
            # the failed net first, then the taken-up ones; whatever fails moves to the front
            # and the set is laid again - up to `orders` orders (the rip-up's negotiation)
            order = [net] + victims
            for attempt in range(orders):
                laid, failed_now, whys = [], [], []
                for n_ in order:
                    ok_, rv, why_ = self.route_net(n_)
                    laid += rv
                    if not ok_:
                        failed_now.append(n_)
                        whys.append(f"{n_}: {why_}")
                if not failed_now:
                    self.log.append(f"rescue {net}, {r} mm box: took up {', '.join(victims)}; all routed"
                                    + (f" in order {attempt + 1}" if attempt else ""))
                    self.log.append(f"rescue: {net} routed after taking up {', '.join(victims)} in a {r} mm box")
                    return True
                self.log.append(f"rescue {net}, {r} mm box, order {attempt + 1}: took up {', '.join(victims)}; "
                                f"then failed {'; '.join(whys)}")
                for rr in laid:
                    if rr.entries:
                        unlay(rr, self.m)
                    if rr in self.runs:
                        self.runs.remove(rr)
                promoted = [n_ for n_ in failed_now if n_ not in order[:len(failed_now)]]
                if not promoted and attempt:
                    break                   # the same nets fail in front: another order changes nothing
                order = failed_now + [n_ for n_ in order if n_ not in failed_now]
            # put everything back
            for v in victims:
                for r_ in saved[v]:
                    lay(r_, self.m)
                    self.runs.append(r_)
            self.log.append(f"rescue {net}, {r} mm box: put back")
        return False

    def _fixed(self, net):
        """A net no rip-up may take: any locked copper, or copper outside the fence."""
        for e in self.m.index.of_net(net):
            if e.locked:
                return True
            if self.fence and not box(*self.fence).contains(e.geom):
                return True
        return False

    # ---------------------------------------------------------------- the tools

    def runs_of(self, net):
        return [r for r in self.runs if r.net == net]

    def cross_count(self, run):
        """Plan crossings between this run and every other net's runs."""
        mine = [LineString([a, b]) for _, a, b, _ in run.segments()]
        if not mine:
            return 0
        u = box(*unary_union(mine).bounds)
        n = 0
        for r in self.runs:
            if r.net == run.net or r is run:
                continue
            for _, a, b, _ in r.segments():
                s = LineString([a, b])
                if s.intersects(u):
                    n += sum(1 for m_ in mine if m_.crosses(s))
        # and the copper that came with the board (a hand route, an earlier family read back
        # from its checkpoint): no Run of this router's, but crossed all the same - without it
        # a resumed family's liquid pass judged crossings against less than one run would
        # (the resume test board)
        for e in self.m.index.query(u.bounds):
            if e.kind == "track" and getattr(e, "run", None) is None and e.net != run.net and hasattr(e, "line"):
                n += sum(1 for m_ in mine if m_.crosses(e.line))
        return n

    def replace(self, old, new_pts, keep_crossings=True):
        """Swap a run's points if the new run fits (against everything but its own old
        copper) and, with keep_crossings, crosses no more other nets than the old one did;
        returns the new run or None. A locked run is refused."""
        if old.locked:
            return None
        new = old.copy(new_pts)
        new.fillet = old.fillet
        if fits(new, self.m, self.fields, self.fence, ignore=set(old.entries)):
            return None
        if keep_crossings and self.cross_count(new) > self.cross_count(old):
            self.stats["crossing_refused"] += 1
            return None
        # what the old run touched of its own net - another run's tee, a via, a pad, locked
        # copper - the new one must still touch: a liquid move that straightens a run off the
        # point where a branch tees into it leaves the branch hanging (the channel board:
        # the rubber band took CLK's trunk off its branch's tee, and DRC found it open)
        before = self._touching(old)
        unlay(old, self.m)
        lay(new, self.m)
        if not before <= self._touching(new):
            unlay(new, self.m)
            lay(old, self.m)
            self.stats["tee_refused"] += 1
            return None
        # nor may it meet its own net's copper under 90 degrees where the old run did not -
        # pcb.py check's acid trap: the rubber band cut the corner of a square tee into a 45
        # (the partial board's C, a branch onto an adopted trunk)
        if self._acute_ends(new, skip=old) > self._acute_ends(old):
            unlay(new, self.m)
            lay(old, self.m)
            self.stats["acid_refused"] += 1
            return None
        self.runs[self.runs.index(old)] = new
        return new

    def _acute_ends(self, run, skip=None):
        """How many of the run's two ends meet a same-net track of its layer under 90
        degrees: its end segment, from the junction, against each way the other track
        leaves the junction. `skip`: a run not to count (the one `run` would replace)."""
        segs = run.segments()
        if not segs:
            return 0
        others = [(L, a, b) for r in self.runs if r.net == run.net and r is not run and r is not skip
                  for (L, a, b, _) in r.segments()]
        n = 0
        for (L, a, b, _), at in ((segs[0], 0), (segs[-1], 1)):
            j, far = (a, b) if at == 0 else (b, a)
            u = _unit(far[0] - j[0], far[1] - j[1])
            if u == (0.0, 0.0):
                continue
            cands = others + [(next(iter(e.layers)), *list(e.line.coords)[::max(1, len(e.line.coords) - 1)][:2])
                              for e in self.m.index.query((j[0] - 0.01, j[1] - 0.01, j[0] + 0.01, j[1] + 0.01))
                              if e.kind == "track" and e.net == run.net and e.run is None and e.line is not None]
            for (L2, p, q) in cands:
                if L2 != L or LineString([p, q]).distance(Point(j)) > 1e-3:
                    continue
                for o in (p, q):
                    if math.dist(o, j) < 1e-3:
                        continue
                    v = _unit(o[0] - j[0], o[1] - j[1])
                    if u[0] * v[0] + u[1] * v[1] > 1e-6:        # under 90 degrees
                        n += 1
                        break
        return n

    def _touching(self, run):
        """The entries of the run's own net, not its own, that its copper touches."""
        mine = [self.m.index.e[eid] for eid in run.entries if eid in self.m.index.e]
        out = set()
        for oe in mine:
            for e in self.m.index.query(oe.geom.bounds):
                if e.id in run.entries or e.net != run.net or not (e.layers & oe.layers):
                    continue
                if e.kind in ("track", "via", "pad") and oe.geom.intersects(e.geom):
                    out.add(e.id)
        return out

    def reroute(self, net, pull=None, shove_depth=2):
        """The net routed again. With `pull` (mm), inside a corridor that wide either side of
        its pads' line, preferred strongly. A net whose copper stands in the way is shoved:
        laid again round the new run, near its old path, at most `shove_depth` deep. Only
        if that fails is the net laid round everything as it stands. Returns a report."""
        rep = {"net": net, "shoved": [], "mode": None}
        old = [r for r in self.runs_of(net)]
        if any(r.locked for r in old):
            rep["mode"] = "refused: locked"
            return rep
        before = sum(r.length() for r in old)
        for r in old:
            unlay(r, self.m)
            self.runs.remove(r)
        saved_fields = list(self.fields)
        if pull:
            ps = self.m.pads_of(net)
            xs = [p.centre[0] for p in ps]
            ys = [p.centre[1] for p in ps]
            self.fields.append(Field((min(xs) - pull, min(ys) - pull, max(xs) + pull, max(ys) + pull), weight=0.5, nets=[net]))
        try:
            # 1. the ideal: past every net that may be shoved
            movable = [r for r in self.runs if r.net != net and not r.locked and not self._fixed(r.net)]
            ideal = self._route_ignoring(net, movable)
            if ideal is not None:
                hit = sorted({r.net for r in movable if self._conflicts(ideal, r)})
                if self._shove(net, ideal, hit, shove_depth, rep):
                    rep["mode"] = "shove" if hit else "direct"
                    rep["before"], rep["after"] = before, sum(r.length() for r in self.runs_of(net))
                    return rep
            # 2. round everything as it stands
            ok, runs, why = self.route_net(net)
            if ok:
                rep["mode"] = "walkaround"
            else:
                rep["mode"] = f"failed: {why}"
                for r in runs:
                    if r.entries:
                        unlay(r, self.m)
                    self.runs.remove(r)
                for r in old:
                    lay(r, self.m)
                    self.runs.append(r)
            rep["before"], rep["after"] = before, sum(r.length() for r in self.runs_of(net))
            return rep
        finally:
            self.fields = saved_fields

    def _route_ignoring(self, net, movable):
        """The net's runs routed as if `movable` were not there (not laid); None if none."""
        hidden = []
        for r in movable:
            for eid in r.entries:
                hidden.append(self.m.index.remove(eid))
            r._hidden = r.entries
            r.entries = []
        # what is hidden is SOFT, not gone: the ideal path pays to cross it, so it leaves the
        # shoved copper room beside it where there is room (a channel: hug the far wall, not
        # its middle - the channel test board)
        saved_soft = list(self.soft)
        self.soft += [(e.geom, e.layers, 4.0) for e in hidden if e.kind in ("track", "via")]
        try:
            ok, runs, _ = self.route_net(net)
            for r in runs:
                unlay(r, self.m)
                self.runs.remove(r)
            return runs if ok else None
        finally:
            self.soft = saved_soft
            for r in movable:
                r.entries = []
                lay(r, self.m)

    def _conflicts(self, runs, other):
        for r in runs:
            fake = Model.__new__(Model)
            fake.__dict__ = dict(self.m.__dict__)
            idx = CopperIndex()
            for eid in other.entries:
                e = self.m.index.e[eid]
                idx.add(net=e.net, layers=e.layers, geom=e.geom, kind=e.kind, drill=e.drill, smd=e.smd)
            fake.index = idx
            if fits(r, fake, self.fields, None):
                return True
        return False

    def _shove(self, net, ideal, hit, depth, rep):
        """Lay `ideal` for `net`, then each net in `hit` again near its old path; recursive
        to `depth`. All or nothing."""
        old = {h: [r for r in self.runs_of(h)] for h in hit}
        for h in hit:
            for r in old[h]:
                unlay(r, self.m)
                self.runs.remove(r)
        laid = []
        for r in ideal:
            if fits(r, self.m, self.fields, self.fence):
                break
            lay(r, self.m)
            self.runs.append(r)
            laid.append(r)
        ok = len(laid) == len(ideal)
        redone = []
        if ok:
            for h in hit:
                saved = list(self.fields)
                xs = [x for r in old[h] for x, _, _ in r.pts]
                ys = [y for r in old[h] for _, y, _ in r.pts]
                self.fields.append(Field((min(xs) - 3, min(ys) - 3, max(xs) + 3, max(ys) + 3), weight=0.6, nets=[h]))
                okh, runs, _ = self.route_net(h)
                self.fields = saved
                redone += runs
                if not okh:
                    if depth > 1:
                        movable = [r for r in self.runs if r.net not in (net, h) and not r.locked and not self._fixed(r.net)]
                        for r in runs:
                            if r.entries:
                                unlay(r, self.m)
                            self.runs.remove(r)
                            redone.remove(r)
                        ih = self._route_ignoring(h, movable)
                        if ih is not None:
                            hit2 = sorted({r.net for r in movable if self._conflicts(ih, r)})
                            if self._shove(h, ih, hit2, depth - 1, rep):
                                rep["shoved"].append(h)
                                continue
                    ok = False
                    break
                rep["shoved"].append(h)
        if ok:
            return True
        for r in laid + redone:
            if r.entries:
                unlay(r, self.m)
            if r in self.runs:
                self.runs.remove(r)
        for h in hit:
            for r in self.runs_of(h):
                if r.entries:
                    unlay(r, self.m)
                self.runs.remove(r)
            for r in old[h]:
                lay(r, self.m)
                self.runs.append(r)
        rep["shoved"] = [s for s in rep["shoved"] if s not in hit]
        return False

    def slide_vias(self, step=None, reach=3.0):
        """Each unlocked via slid along the run either side of it: kept where `fits` passes,
        plan crossings do not rise and the run gets shorter. Returns how many moved."""
        step = step or self.pitch
        moved = 0
        for run in sorted(list(self.runs), key=lambda r: (r.net, r.pts)):
            if run.locked or run not in self.runs:
                continue
            k = 0
            while k < len(run.pts) - 1:
                a, b = run.pts[k], run.pts[k + 1]
                if a[2] == b[2] or (a[0], a[1]) != (b[0], b[1]) or k == 0 or k + 2 >= len(run.pts):
                    k += 1
                    continue
                prev, nxt = run.pts[k - 1], run.pts[k + 2]
                base_len, base_x = run.length(), crossings(self.runs)
                best = None
                for tgt in (prev, nxt):
                    d = math.dist(a[:2], tgt[:2])
                    u = _unit(tgt[0] - a[0], tgt[1] - a[1])
                    for s in np.arange(step, min(d, reach) + 1e-9, step):
                        x, y = snap(a[0] + u[0] * s), snap(a[1] + u[1] * s)
                        pts = list(run.pts)
                        pts[k] = (x, y, a[2])
                        pts[k + 1] = (x, y, b[2])
                        pts = simplify(pts)
                        if not all(octilinear(p[:2], q[:2]) for p, q in zip(pts, pts[1:]) if p[2] == q[2]) and \
                                not self._ends_offgrid(pts, run):
                            continue
                        cand = run.copy(pts)
                        if cand.length() >= base_len - 1e-6:
                            continue
                        if fits(cand, self.m, self.fields, self.fence, ignore=set(run.entries)):
                            continue
                        if best is None or cand.length() < best[0]:
                            best = (cand.length(), pts)
                if best:
                    new = self.replace(run, best[1])
                    if new is not None and crossings(self.runs) <= base_x:
                        run = new
                        moved += 1
                    elif new is not None:
                        self.replace(new, run.pts)
                k += 1
        return moved

    def _ends_offgrid(self, pts, run):
        # pad stubs are allowed off octilinear only at the run's two ends
        inner = [(p, q) for p, q in zip(pts[1:-1], pts[2:-1]) if p[2] == q[2]]
        return all(octilinear(p[:2], q[:2]) for p, q in inner)

    def uncross(self, fold=1.5):
        """Fold an up-then-down pair shorter than `fold` mm onto one face, where it fits.
        Returns how many."""
        n = 0
        for run in sorted(list(self.runs), key=lambda r: (r.net, r.pts)):
            if run.locked or run not in self.runs:
                continue
            changed = True
            while changed:
                changed = False
                pts = run.pts
                vi = [k for k in range(len(pts) - 1) if pts[k][2] != pts[k + 1][2]]
                for a, b in zip(vi, vi[1:]):
                    piece = pts[a + 1:b + 1]
                    ln = sum(math.dist(p[:2], q[:2]) for p, q in zip(piece, piece[1:]))
                    if ln > fold or pts[a][2] != pts[b + 1][2]:
                        continue
                    L = pts[a][2]
                    new = simplify(pts[:a + 1] + [(p[0], p[1], L) for p in piece] + pts[b + 2:])
                    r2 = self.replace(run, new)
                    if r2 is not None:
                        run = r2
                        n += 1
                        changed = True
                        break
        return n

    def rubber_band(self):
        """Coalesce jogs: on each leg, a point joined to a later one by a straight or a
        two-piece 0/45/90 path where that is shorter and fits. Returns runs changed."""
        changed = 0
        for run in sorted(list(self.runs), key=lambda r: (r.net, r.pts)):
            if run.locked or run not in self.runs:
                continue
            improved = True
            while improved:
                improved = False
                pts = run.pts
                for i in range(len(pts) - 2):
                    for j in range(len(pts) - 1, i + 1, -1):
                        if any(pts[k][2] != pts[i][2] for k in range(i, j + 1)):
                            continue
                        a, b = pts[i], pts[j]
                        old = sum(math.dist(p[:2], q[:2]) for p, q in zip(pts[i:j], pts[i + 1:j + 1]))
                        for mid in self._elbows(a, b):
                            seg = [a] + ([(mid[0], mid[1], a[2])] if mid else []) + [b]
                            new_len = sum(math.dist(p[:2], q[:2]) for p, q in zip(seg, seg[1:]))
                            if new_len >= old - 1e-6:
                                continue
                            npts = simplify(pts[:i] + seg + pts[j + 1:])
                            r2 = self.replace(run, npts)
                            if r2 is not None:
                                run = r2
                                improved = True
                                changed += 1
                                break
                        if improved:
                            break
                    if improved:
                        break
        return changed

    def _elbows(self, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        if octilinear(a[:2], b[:2]):
            return [None]
        out = []
        m = min(abs(dx), abs(dy))
        sx, sy = math.copysign(1, dx), math.copysign(1, dy)
        out.append((snap(a[0] + sx * m), snap(a[1] + sy * m)))          # diagonal first
        out.append((snap(b[0] - sx * m), snap(b[1] - sy * m)))          # diagonal last
        return out

    def equalise(self, rounds=8, tol=0.02):
        """Parallel neighbours of different nets on one layer, a middle one between two
        others, moved toward the middle of its gap: a capped fixed point, in a fixed order,
        each move kept only if it fits and the total gap imbalance falls."""
        moves = 0
        for _ in range(rounds):
            any_move = False
            segs = []
            for r in sorted(self.runs, key=lambda r: (r.net, r.pts)):
                if r.locked:
                    continue
                for k in range(1, len(r.pts) - 2):
                    a, b = r.pts[k], r.pts[k + 1]
                    if a[2] == b[2] and (a[0], a[1]) != (b[0], b[1]):
                        segs.append((r, k))
            for r, k in segs:
                if r not in self.runs or k + 1 >= len(r.pts) - 1:
                    continue
                a, b = r.pts[k], r.pts[k + 1]
                if a[2] != b[2]:
                    continue
                u = _unit(b[0] - a[0], b[1] - a[1])
                nrm = (-u[1], u[0])
                line = LineString([a[:2], b[:2]])
                left, right = self._neighbour(line, a[2], r.net, nrm, +1), self._neighbour(line, a[2], r.net, nrm, -1)
                if left is None or right is None:
                    continue
                shift = (left - right) / 2           # + moves toward +nrm
                if abs(shift) < tol:
                    continue
                shift = snap(shift)
                if shift == 0:
                    continue
                new = self._shift_segment(r.pts, k, nrm, shift)
                if new is None:
                    continue
                r2 = self.replace(r, new)
                if r2 is not None:
                    moves += 1
                    any_move = True
            if not any_move:
                break
        return moves

    def _neighbour(self, line, L, net, nrm, sgn):
        """The free gap (mm, edge to edge) from this segment to the nearest other net's
        copper on that side, along the normal at its middle; None if nothing within 3 mm."""
        mid = line.interpolate(0.5, normalized=True)
        probe = LineString([(mid.x, mid.y), (mid.x + nrm[0] * sgn * 3.0, mid.y + nrm[1] * sgn * 3.0)])
        best = None
        for e in self.m.index.query(probe.bounds):
            if L not in e.layers or e.net == net or e.kind in ("reserve",):
                continue
            if e.kind not in ("track", "via", "pad"):
                continue
            if e.geom.intersects(probe):
                d = Point(mid.x, mid.y).distance(e.geom)
                best = d if best is None else min(best, d)
        return best

    def _shift_segment(self, pts, k, nrm, s):
        """Move segment k..k+1 by s along nrm; its neighbours' lines are kept, so each
        joint slides along the neighbour (0/45/90 kept)."""
        a, b = pts[k], pts[k + 1]
        a2 = (a[0] + nrm[0] * s, a[1] + nrm[1] * s)
        b2 = (b[0] + nrm[0] * s, b[1] + nrm[1] * s)
        p, q = pts[k - 1], pts[k + 2]
        ja = _intersect(p[:2], a[:2], a2, b2)
        jb = _intersect(b[:2], q[:2], a2, b2)
        if ja is None or jb is None:
            return None
        new = list(pts)
        new[k] = (snap(ja[0]), snap(ja[1]), a[2])
        new[k + 1] = (snap(jb[0]), snap(jb[1]), b[2])
        segs = [(x, y) for x, y in zip(new[k - 1:k + 3], new[k:k + 3])]
        if not all(octilinear(x[:2], y[:2]) for x, y in segs if x[2] == y[2]):
            return None
        # the joint must stay on the neighbour's own run (not overshoot past its far end)
        for (x0, y0, _), (x1, y1, _), (jx, jy, _) in ((p, a, new[k]), (q, b, new[k + 1])):
            if (jx - x0) * (x1 - x0) + (jy - y0) * (y1 - y0) <= 0:
                return None
        return new

    def liquid(self, fillet=0.0):
        """Coalesce jogs, equalise gaps, slide vias, fold short via pairs, and fillet."""
        rep = {"rubber_band": self.rubber_band(), "uncross": self.uncross(), "slide": self.slide_vias(),
               "equalise": self.equalise(), "rubber_band_2": self.rubber_band()}
        rep["filleted"] = self.fillet_all(fillet) if fillet > 0 else 0
        return rep

    def fillet_all(self, r):
        n = 0
        for run in sorted(list(self.runs), key=lambda x: (x.net, x.pts)):
            if run.locked:
                continue
            cand = run.copy()
            cand.fillet = r
            if not any(p[0] == "A" for p in cand.prims()):
                continue
            if fits(cand, self.m, self.fields, self.fence, ignore=set(run.entries)):
                continue
            unlay(run, self.m)
            lay(cand, self.m)
            self.runs[self.runs.index(run)] = cand
            n += 1
        return n

    def summary(self):
        segs = [s for r in self.runs for s in r.segments()]
        return {"runs": len(self.runs), "length_mm": round(sum(r.length() for r in self.runs), 2),
                "vias": sum(len(r.vias()) for r in self.runs), "crossings": crossings(self.runs),
                "segments": len(segs), "rejected": self.stats["rejected"], "nodes": self.stats["nodes"],
                "single_layer_taken": self.stats["single_layer_taken"]}


def _intersect(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(d) < 1e-12:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


# ------------------------------------------------------------------ KiCad boards

def _kicad():
    import pcbnew
    return pcbnew


def outline_of(board):
    """The board's outline from KiCad's own polygon (one outline reader, A7)."""
    pcbnew = _kicad()
    ol = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(ol):
        raise SystemExit("route2: the board outline is not closed")
    polys = []
    for i in range(ol.OutlineCount()):
        o = ol.Outline(i)
        ext = [(pcbnew.ToMM(o.CPoint(j).x), pcbnew.ToMM(o.CPoint(j).y)) for j in range(o.PointCount())]
        holes = []
        for h in range(ol.HoleCount(i)):
            hh = ol.Hole(i, h)
            holes.append([(pcbnew.ToMM(hh.CPoint(j).x), pcbnew.ToMM(hh.CPoint(j).y)) for j in range(hh.PointCount())])
        polys.append(Polygon(ext, holes))
    return unary_union(polys)


def _poly_of(ps):
    """A KiCad SHAPE_POLY_SET as one shapely geometry, holes kept (a moat ring is a ring)."""
    pcbnew = _kicad()
    pts = lambda c: [(pcbnew.ToMM(c.CPoint(j).x), pcbnew.ToMM(c.CPoint(j).y)) for j in range(c.PointCount())]
    out = []
    for i in range(ps.OutlineCount()):
        out.append(Polygon(pts(ps.Outline(i)), [pts(ps.Hole(i, h)) for h in range(ps.HoleCount(i))]))
    return unary_union(out)


def _frame(lay):
    """How layout.yaml's island outlines and windows are written: the body frame (every real
    board, as pcb_main reads them) unless `outline_frame: board` (a constructed board)."""
    if lay.get("outline_frame") == "board":
        return lambda x, y: (x, y)
    return None


def model_from_board(board, lay, fence=None, via_off_silk=True):
    """The Model of a KiCad board, with its existing tracks and vias as copper entries
    (locked as KiCad has them) and Run-less: rip-up of existing copper is by entry. With
    via_off_silk, every silkscreen item's box is a keep-out for vias, as tools/pcb_route.py
    has it: a via under a legend prints it onto a tented hole, and pcb.py check fails it."""
    pcbnew = _kicad()
    rules = Rules(lay)
    names = [board.GetLayerName(l) for l in board.GetEnabledLayers().CuStack()]
    lids = list(board.GetEnabledLayers().CuStack())
    pads, holes, keeps = [], [], []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            on = [k for k, l in enumerate(lids) if pad.IsOnLayer(l)]
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                c = pad.GetPosition()
                holes.append((Point(pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)).buffer(pcbnew.ToMM(pad.GetDrillSize().x) / 2), pcbnew.ToMM(pad.GetDrillSize().x)))
                continue
            if not on:
                continue
            g = _poly_of(pad.GetEffectivePolygon(lids[on[0]]))
            c = pad.GetPosition()
            pads.append(Pad(ref=fp.GetReference(), num=pad.GetNumber(), net=pad.GetNetname(), layers=set(on), geom=g,
                            centre=(pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)), smd=not pad.HasHole(),
                            drill=pcbnew.ToMM(pad.GetDrillSize().x) if pad.HasHole() else None, item=pad,
                            tie=fp.IsNetTie(),
                            face_of_hole=not pad.HasHole() and any(q.HasHole() and q.GetNumber() == pad.GetNumber()
                                                                   for q in fp.Pads())))
    for z in board.Zones():
        if z.GetIsRuleArea():
            g = _poly_of(z.Outline())
            ls = [k for k, l in enumerate(lids) if z.IsOnLayer(l)]
            keeps.append((g, ls, z.GetDoNotAllowTracks(), z.GetDoNotAllowVias()))
    if via_off_silk:
        silk = (pcbnew.F_SilkS, pcbnew.B_SilkS)
        items = [d for d in board.GetDrawings() if d.GetLayer() in silk]
        for fp in board.GetFootprints():
            items += [g for g in fp.GraphicalItems() if g.GetLayer() in silk]
            items += [f for f in fp.GetFields() if f.GetLayer() in silk and f.IsVisible()]
        for it in items:
            bb = it.GetBoundingBox()
            keeps.append((box(pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()),
                              pcbnew.ToMM(bb.GetBottom())), list(range(len(lids))), False, True))
    m = Model(outline_of(board), names, rules, pads, holes, keeps, fence)
    m.lids = lids
    m.board = board
    # layout.yaml pairs: guard - no other net's track on the pair's layer, and no other net's
    # via anywhere, within the clearance plus the guard of a locked pair leg (#8-4; held by
    # pcb.py check_pair_guard, whose reading this is): a reservation round the legs
    for pr in lay.get("pairs") or []:
        if not pr.get("guard") or pr.get("layer", "F.Cu") not in names:
            continue
        g, w = float(pr["guard"]), float(pr["width"])
        own = set(pr["nets"]) | {(pr.get("guard_traces") or {}).get("net")}
        Lid = board.GetLayerID(pr.get("layer", "F.Cu"))
        legs = []
        for t in board.GetTracks():
            if type(t) in (pcbnew.PCB_TRACK, pcbnew.PCB_ARC) and t.IsLocked() and t.GetNetname() in pr["nets"] \
                    and t.GetLayer() == Lid and abs(pcbnew.ToMM(t.GetWidth()) - w) < 1e-3 and t.GetStart() != t.GetEnd():
                a, b = t.GetStart(), t.GetEnd()
                if type(t) is pcbnew.PCB_ARC:
                    mm = t.GetMid()
                    line = LineString(arc_points((pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)), (pcbnew.ToMM(mm.x), pcbnew.ToMM(mm.y)),
                                                 (pcbnew.ToMM(b.x), pcbnew.ToMM(b.y))))
                else:
                    line = LineString([(pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)), (pcbnew.ToMM(b.x), pcbnew.ToMM(b.y))])
                legs.append(line.buffer(w / 2))
        if legs:
            zone_ = unary_union(legs).buffer(rules.clearance + g - EPS)
            m.index.add(net=None, layers=[lids.index(Lid)], geom=zone_, kind="reserve", locked=True,
                        family={n for n in own if n})
    if lay.get("planes") or lay.get("islands"):
        m.planes = Planes(lay, m, board, to_pcb=_frame(lay))
        zones = []
        for z in board.Zones():
            if z.GetIsRuleArea():
                continue
            for k, lid in enumerate(lids):
                if z.IsOnLayer(lid):
                    zones.append((k, _poly_of(z.Outline())))
        for L, geom, exempt in m.planes.splits(m, zones):
            m.index.add(net=None, layers=[L], geom=geom, kind="reserve", locked=True, family=exempt)
    for t in board.GetTracks():
        net = t.GetNetname()
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition()
            m.index.add(net=net, layers=range(m.nl), geom=Point(pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)).buffer(pcbnew.ToMM(t.GetWidth(lids[0])) / 2, quad_segs=8),
                        kind="via", locked=t.IsLocked(), drill=pcbnew.ToMM(t.GetDrillValue()), item=t)
        else:
            if t.GetLayer() not in lids:
                continue
            a, b = t.GetStart(), t.GetEnd()
            if type(t) is pcbnew.PCB_ARC:
                mm = t.GetMid()
                line = LineString(arc_points((pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)), (pcbnew.ToMM(mm.x), pcbnew.ToMM(mm.y)),
                                             (pcbnew.ToMM(b.x), pcbnew.ToMM(b.y))))
            else:
                line = LineString([(pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)), (pcbnew.ToMM(b.x), pcbnew.ToMM(b.y))])
            e = m.index.add(net=net, layers=[lids.index(t.GetLayer())], geom=line.buffer(pcbnew.ToMM(t.GetWidth()) / 2, quad_segs=8),
                            kind="track", locked=t.IsLocked(), item=t)
            e.line = line           # its centreline: Router.cross_count counts crossings of it
    return m


def take_up(model, nets):
    """Take up the unlocked existing copper of `nets` (entries carrying a board item);
    write() deletes the items. Locked copper stays and stays an obstacle - and so does
    what locked copper DEPENDS on, though KiCad holds it unlocked: a via that meets its
    net's locked tracks (a hand route locked track by track, its layer changes not), or a
    track both of whose ends meet locked copper. Taking those up would cut a locked route
    in two (found on the main board: #45's /IO2 route). They are marked locked here."""
    pcbnew = _kicad()
    locked = {}
    for e in model.index.e.values():
        if e.kind in ("track", "via") and e.locked:
            locked.setdefault(e.net, []).append(e)

    def ends(e):
        t = e.item
        if t is None or isinstance(t, pcbnew.PCB_VIA):
            return []
        return [Point(pcbnew.ToMM(v.x), pcbnew.ToMM(v.y)) for v in (t.GetStart(), t.GetEnd())]
    n, kept = 0, 0
    for e in list(model.index.e.values()):
        if e.net not in nets or e.kind not in ("track", "via") or e.item is None or e.locked:
            continue
        mine = locked.get(e.net, [])
        if e.kind == "via" and any(l.kind == "track" and e.geom.intersects(l.geom) for l in mine):
            e.locked = True
            kept += 1
            continue
        if e.kind == "track":
            pe = ends(e)
            if pe and all(any(l.geom.buffer(1e-3).contains(q) and l.layers & e.layers for l in mine) for q in pe):
                e.locked = True
                kept += 1
                continue
        model.index.remove(e.id)
        model.removed_items.append(e.item)
        n += 1
    model.kept_for_locked = kept
    return n


def write(board, model, runs, pour=None):
    """Delete what take_up removed (Delete, never Remove), add every run's tracks, arcs and
    vias, and with `pour` a zone of that net on every copper layer over the outline."""
    pcbnew = _kicad()
    for it in model.removed_items:
        board.Delete(it)
    model.removed_items = []
    lids = model.lids
    V = lambda p: pcbnew.VECTOR2I(pcbnew.FromMM(p[0]), pcbnew.FromMM(p[1]))

    added = []

    def add(t, net, locked):
        t.SetNet(board.FindNet(net))
        t.SetLocked(locked)
        board.Add(t)
        added.append(t)
        return t
    # straight copper, merged per net, layer and width: two runs of one net that overlap
    # (a pad stub in, the next branch of the tree out along the same line) would meet at
    # 0 degrees - pcb.py check's acid trap. The union covers exactly the same copper.
    from shapely.ops import linemerge
    straight = {}
    for run in runs:
        for p in run.prims():
            if p[0] == "S":
                straight.setdefault((run.net, p[1], round(p[4], 4), run.locked), []).append(LineString([p[2], p[3]]))
    for (net, L, w, locked), lines in sorted(straight.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
        u = unary_union(lines)
        merged = linemerge(u) if u.geom_type == "MultiLineString" else u      # one line: nothing to merge
        for ls in (list(merged.geoms) if hasattr(merged, "geoms") else [merged]):
            pts = [(snap(x), snap(y), L) for x, y in ls.coords]
            pts = simplify(pts)
            for q0, q1 in zip(pts, pts[1:]):
                if (q0[0], q0[1]) == (q1[0], q1[1]):
                    continue
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(V(q0))
                t.SetEnd(V(q1))
                t.SetWidth(pcbnew.FromMM(w))
                t.SetLayer(lids[L])
                add(t, net, locked)
    for run in runs:
        for p in run.prims():
            if p[0] == "A":
                t = pcbnew.PCB_ARC(board)
                t.SetStart(V(p[2]))
                t.SetMid(V(p[3]))
                t.SetEnd(V(p[4]))
                t.SetWidth(pcbnew.FromMM(p[5]))
                t.SetLayer(lids[p[1]])
                run.items.append(add(t, run.net, run.locked))
            elif p[0] == "V":
                t = pcbnew.PCB_VIA(board)
                t.SetPosition(V((p[1], p[2])))
                t.SetWidth(pcbnew.FromMM(run.via[0]))
                t.SetDrill(pcbnew.FromMM(run.via[1]))
                run.items.append(add(t, run.net, run.locked))
    if pour:
        for L in lids:
            z = pcbnew.ZONE(board)
            z.SetLayer(L)
            z.SetNet(board.FindNet(pour))
            z.SetLocalClearance(pcbnew.FromMM(model.rules.clearance))
            z.SetMinThickness(pcbnew.FromMM(0.25))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
            z.SetThermalReliefGap(pcbnew.FromMM(0.3))
            z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.4))
            ol = z.Outline()
            ol.NewOutline()
            geom = model.outline if model.outline.geom_type == "Polygon" else max(model.outline.geoms, key=lambda g: g.area)
            for x, y in list(geom.exterior.coords)[:-1]:
                ol.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
            z.SetIsFilled(False)
            board.Add(z)
    return added


def fill_zones(path):
    """Fill every zone of a SAVED board in its own load (KiCad 9 crashes filling a board
    built in the same process)."""
    pcbnew = _kicad()
    board = pcbnew.LoadBoard(path)
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(path, board)


def tie_pour_islands(path, lay, net, rounds=3, step=0.25):
    """`fits` cannot see a pour: a legal route can cut a zone of `net` into pieces, and a
    piece kept alive by one pad of the net is still cut off from the rest. On a SAVED board,
    in its own load: fill; join every filled piece, pad, track and via of the net that touch
    on a layer (a via or a plated pad joins its layers) into groups; for each group but the
    main one (the most pads), put a via inside one of its pieces over the main group's fill
    on another layer, where `fits` passes; refill; repeat. Saves the board. Returns
    (vias added, groups still apart as [(layer, point)])."""
    pcbnew = _kicad()
    added, left = 0, []
    for _ in range(rounds):
        board = pcbnew.LoadBoard(path)
        board.BuildConnectivity()
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        m = model_from_board(board, lay)
        nodes = []             # (layers, geom, kind)
        for z in board.Zones():
            if z.GetIsRuleArea() or z.GetNetname() != net:
                continue
            for k, lid in enumerate(m.lids):
                if z.IsOnLayer(lid):
                    ps = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lid))
                    ps.Unfracture()
                    g = _poly_of(ps)
                    for piece in (list(g.geoms) if g.geom_type == "MultiPolygon" else [g]):
                        if not piece.is_empty:
                            nodes.append(({k}, piece, "fill"))
        for e in m.index.e.values():
            if e.net == net and e.kind in ("pad", "track", "via"):
                nodes.append((set(e.layers), e.geom, e.kind))
        parent = list(range(len(nodes)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if nodes[i][0] & nodes[j][0] and nodes[i][1].intersects(nodes[j][1]):
                    parent[find(i)] = find(j)
        groups = {}
        for i in range(len(nodes)):
            groups.setdefault(find(i), []).append(i)
        if len(groups) <= 1:
            break
        main = max(groups.values(), key=lambda g: (sum(1 for i in g if nodes[i][2] == "pad"), len(g)))
        d, drill = m.rules.via_size(net)
        new, left = 0, []
        for g in groups.values():
            if g is main:
                continue
            fills = sorted((i for i in g if nodes[i][2] == "fill"), key=lambda i: -nodes[i][1].area)
            done = False
            for i in fills:
                k = next(iter(nodes[i][0]))
                over = unary_union([nodes[j][1] for j in main if nodes[j][2] == "fill" and k not in nodes[j][0]])
                if over.is_empty:
                    continue
                room = nodes[i][1].buffer(-(d / 2 + 0.05)).intersection(over.buffer(-(d / 2 + 0.05)))
                if room.is_empty:
                    continue
                x0, y0, x1, y1 = room.bounds
                c = room.representative_point()
                pts = [(snap(x0 + a * step), snap(y0 + b_ * step)) for a in range(int((x1 - x0) / step) + 1)
                       for b_ in range(int((y1 - y0) / step) + 1)]
                pts = sorted((p for p in pts if room.contains(Point(p))), key=lambda p: math.dist(p, (c.x, c.y)))
                for x, y in pts[:400]:
                    run = Run(net, [(x, y, k), (x, y, (k + 1) % m.nl)], m.rules.width(net), (d, drill))
                    if not fits(run, m):
                        v = pcbnew.PCB_VIA(board)
                        v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
                        v.SetWidth(pcbnew.FromMM(d))
                        v.SetDrill(pcbnew.FromMM(drill))
                        v.SetNet(board.FindNet(net))
                        board.Add(v)
                        new += 1
                        done = True
                        break
                if done:
                    break
            if not done:
                i = g[0]
                left.append((sorted(nodes[i][0])[0], tuple(round(v, 2) for v in nodes[i][1].representative_point().coords[0])))
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(path, board)
        added += new
        if not new:
            break
    return added, left


def fix_plane_orphans(path, lay, rounds=3):
    """A plane is one piece only until vias and pins of other nets cut it: antipads in a row
    can leave a FRAGMENT holding some of the net's pads and vias, joined to nothing else.
    On a SAVED board, in its own load: fill; for each `fanout:` net, group its fill pieces,
    pads, tracks and vias by contact (a via or a plated pad joins its layers); for each
    group but the main one (the most pads), give one of its SMD pads a new fanout via into
    the main group's fill on the plane layer (the main group: the one holding the most of
    the net's fill); refill; repeat. Saves the board. Returns
    (vias added, [pads still apart])."""
    pcbnew = _kicad()
    added, left = 0, []
    for _ in range(rounds):
        board = pcbnew.LoadBoard(path)
        board.BuildConnectivity()
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        m = model_from_board(board, lay)
        if m.planes is None:
            return 0, []
        r = Router(m)
        new, left = 0, []
        for net in m.planes.fanout_nets:
            nodes = []
            for z in board.Zones():
                if z.GetIsRuleArea() or z.GetNetname() != net:
                    continue
                for k, lid in enumerate(m.lids):
                    if z.IsOnLayer(lid):
                        ps = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lid))
                        ps.Unfracture()
                        g = _poly_of(ps)
                        for piece in (list(g.geoms) if g.geom_type == "MultiPolygon" else [g]):
                            if not piece.is_empty:
                                nodes.append(({k}, piece, "fill", None))
            if not nodes:
                continue
            for e in m.index.e.values():
                if e.net == net and e.kind in ("pad", "track", "via"):
                    nodes.append((set(e.layers), e.geom, e.kind, e.ref))
            parent = list(range(len(nodes)))

            def find(i):
                while parent[i] != i:
                    parent[i] = parent[parent[i]]
                    i = parent[i]
                return i
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    if nodes[i][0] & nodes[j][0] and nodes[i][1].intersects(nodes[j][1]):
                        parent[find(i)] = find(j)
            groups = {}
            for i in range(len(nodes)):
                groups.setdefault(find(i), []).append(i)
            if len(groups) <= 1:
                continue
            # the plane's BODY is the group holding the most of its fill - not the most pads: a
            # fragment cut off round one pad has as many pads as a sparse plane's body
            main = max(groups.values(), key=lambda g: (sum(nodes[i][1].area for i in g if nodes[i][2] == "fill"),
                                                       sum(1 for i in g if nodes[i][2] == "pad")))
            body = unary_union([nodes[i][1] for i in main if nodes[i][2] == "fill"])
            for g in groups.values():
                if g is main:
                    continue
                pads = [nodes[i][3] for i in g if nodes[i][2] == "pad" and nodes[i][3]]
                smd = [p for p in pads if any(q.name == p and q.smd for q in m.pads)]
                if not smd:
                    if pads:
                        left.append(f"{net}: {', '.join(pads)} - no SMD pad to fan out again")
                    continue
                miss = r.fanout(only=[smd[0]], region={net: body.intersection(m.planes.region.get(net, body))})
                if miss:
                    left.append(f"{net}: {smd[0]} - {miss[0]}")
                else:
                    new += 1
        if new:
            write(board, m, r.runs)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(path, board)
        added += new
        if not new:
            break
    return added, left


def drc(path, fill=True):
    """KiCad's own DRC on a saved board: (errors [(type, description, items)], unconnected
    count). With `fill`, on a copy whose zones were filled in a fresh process first (KiCad
    9's command line does not refill), so a pour that lost a pad shows as unconnected."""
    import json
    import shutil
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "drc.json")
        if fill:
            cp = os.path.join(t, os.path.basename(path))
            shutil.copy(path, cp)
            pro = os.path.splitext(path)[0] + ".kicad_pro"
            if os.path.exists(pro):         # the board's own rules, or KiCad checks its defaults
                shutil.copy(pro, os.path.splitext(cp)[0] + ".kicad_pro")
            here = os.path.dirname(os.path.abspath(__file__))
            subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {here!r}); import pcb_route2; "
                            f"pcb_route2.fill_zones({cp!r})"], check=True, capture_output=True)
            path = cp
        subprocess.run(["kicad-cli", "pcb", "drc", "--severity-error", "--format", "json", "-o", out, path],
                       capture_output=True, text=True)
        if not os.path.exists(out):
            raise SystemExit(f"route2: KiCad's DRC did not run on {path}")
        j = json.load(open(out))
    errs = [(v["type"], v["description"], [i.get("description", "") for i in v.get("items", [])])
            for v in j.get("violations", []) if v.get("severity") == "error"]
    return errs, len(j.get("unconnected_items", []))


# ------------------------------------------------------------------ command line

def _layout(path):
    import yaml
    return yaml.safe_load(open(path)) if path else {}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["route", "reroute", "tidy"])
    ap.add_argument("board")
    ap.add_argument("--layout")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--nets")
    ap.add_argument("--net")
    ap.add_argument("--ground")
    ap.add_argument("--pull", type=float)
    ap.add_argument("--fence")
    ap.add_argument("--pitch", type=float, default=0.2)
    ap.add_argument("--liquid", action="store_true")
    ap.add_argument("--fillet", type=float, default=0.0)
    a = ap.parse_args(argv)
    if os.path.abspath(a.out) == os.path.abspath(a.board):
        raise SystemExit("route2: -o must not be the source board; this tool writes a copy")
    pcbnew = _kicad()
    lay = _layout(a.layout)
    board = pcbnew.LoadBoard(a.board)
    fence = tuple(float(v) for v in a.fence.split(",")) if a.fence else None
    m = model_from_board(board, lay, fence)
    r = Router(m, pitch=a.pitch, fields=lay.get("fields") or [], time_s=lay.get("time_s"), flow=float(lay.get("flow", 0.0)))
    if a.cmd == "route":
        nets = a.nets.split(",") if a.nets else [n for n in m.nets() if n != a.ground]
        take_up(m, set(nets) | ({a.ground} if a.ground else set()))
        failed = r.route(nets, first=lay.get("route_first") or [], families=lay.get("families") or [], ground=a.ground,
                         connect_first=lay.get("connect_first") or [])
        print(f"route2: {len(failed)} net(s) failed" + (": " + ", ".join(f"{n} ({w})" for n, w in failed.items()) if failed else ""))
    else:
        # the board's own unlocked copper becomes runs the tools can move: it is taken up
        # and routed again by this router first (a tool moves only what it laid)
        nets = [a.net] if a.cmd == "reroute" else [n for n in m.nets()]
        take_up(m, set(n for n in m.nets() if n != a.ground))
        r.route([n for n in m.nets() if n != a.ground])
        if a.cmd == "reroute":
            print(f"route2: reroute {r.reroute(a.net, pull=a.pull)}")
    if a.liquid or a.cmd == "tidy":
        print(f"route2: liquid {r.liquid(a.fillet)}")
    write(board, m, r.runs, pour=a.ground)
    pcbnew.SaveBoard(a.out, board)
    if a.ground:
        fill_zones(a.out)
    print(f"route2: {r.summary()}")
    for line in r.log:
        print("route2: " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
