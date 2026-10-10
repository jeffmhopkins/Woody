"""The cluster packer (issue #46): seats passives round an anchor someone already placed.
Not a board placer, not a force-directed blob, not a wire-length optimiser: it searches
ROWS - one per side of the anchor the parts' far ends leave toward - and scores what the
cluster's airwires cross, with length only as the tiebreak.

    python3 tools/pcb_pack.py pack   BOARD.kicad_pcb -o OUT.kicad_pcb --anchor J7 [--parts R50,R51,FB3,FB4]
                                     [--outside AGND] [--side E,N] [--grow MM] [--rotations 90] [--body J1,SW1,...]
    python3 tools/pcb_pack.py report BOARD.kicad_pcb [--anchors J7,U2] [--island AGND] [--body ...]

THE RULES (`RULES`) are one list of named placement predicates, iterated by the search's
final check and by `report`: courtyard overlap, the board edge, unplaced footprints'
rule areas (the moat keep-out), unplated holes, island containment, and the stay-out of
a foreign island. The search uses them through `seat_ok`, the fast form of the same
geometry on a blocked field built once per cluster; the chosen rows are then checked
against the full list, once, and finally by KiCad's own DRC (pcb_pack_test). It never
writes the source board: -o is a copy, and it refuses to be the source.

INVARIANTS
  * Body-owned parts (`--body`, and every footprint KiCad has locked unless named in
    --parts) do not move. Naming a locked ref in --parts releases ITS lock and the report
    says so; a body-owned ref named there is refused.
  * Moves are by pad centroid: a part's pads land where the seat says, whatever its
    footprint origin.
  * Island containment is geometric. A part with a pad on the island's net may move only
    to a seat whose courtyard lies wholly inside the island polygon; any other part may
    not touch it. The island does not grow.
  * Rotation stays as placed unless --rotations allows 90.
"""
import itertools
import math
import os
import re
import sys

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.prepared import prep

SIDES = {"E": (1, 0), "W": (-1, 0), "S": (0, 1), "N": (0, -1)}   # KiCad frame: y grows down
LATTICE = 0.05
IRON = 0.4          # mm between courtyards in a row: room for an iron


def snap(v, q=LATTICE):
    return round(round(v / q) * q, 6)


# ------------------------------------------------------------------ the board as the packer sees it

class Part:
    def __init__(self, ref, pads, court, rot, locked, item=None, side="F", copper=None, height=None):
        self.ref, self.pads, self.court, self.rot, self.locked = ref, pads, court, rot, locked
        self.item, self.side = item, side
        self.height = height
        # {"F": polygon, "B": polygon}: the part's pad copper on each face. A through-hole
        # pin is on both, so a switch drawn on the top still blocks the bottom under its pins
        self.copper = copper or {}

    @property
    def centroid(self):
        xs = [p[1][0] for p in self.pads] or [self.court.centroid.x]
        ys = [p[1][1] for p in self.pads] or [self.court.centroid.y]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def nets(self):
        return {n for n, _ in self.pads if n}

    def moved(self, dx, dy):
        from shapely import affinity
        return Part(self.ref, [(n, (x + dx, y + dy)) for n, (x, y) in self.pads], affinity.translate(self.court, dx, dy),
                    self.rot, self.locked, self.item, self.side,
                    {k: affinity.translate(g, dx, dy) for k, g in self.copper.items()}, self.height)

    def turned(self, deg):
        """The part turned by `deg` as KiCad turns it: a positive orientation is
        counter-clockwise ON SCREEN, where y grows downward - so in these coordinates the
        geometry turns by -deg. (It turned by +deg until the main board's work: a 90 or 270
        degree turn scored the mirror of the real pin layout. Legality was unaffected - a
        courtyard is symmetric under a half turn - the scores were not.)"""
        from shapely import affinity
        cx, cy = self.centroid
        a = math.radians(-deg)
        pads = [(n, (cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a), cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)))
                for n, (x, y) in self.pads]
        return Part(self.ref, pads, affinity.rotate(self.court, -deg, origin=(cx, cy)), (self.rot + deg) % 360,
                    self.locked, self.item, self.side,
                    {k: affinity.rotate(g, -deg, origin=(cx, cy)) for k, g in self.copper.items()}, self.height)


class Board:
    """Outline, parts, rule-area keep-outs (no footprints), holes, and islands (net -> polygon)."""

    def __init__(self, outline, parts, keepouts=(), holes=(), islands=None, edge=0.3, rails=(), rooms=(), room_default=None,
                 iron=()):
        self.outline, self.parts, self.keepouts, self.holes = outline, {p.ref: p for p in parts}, list(keepouts), list(holes)
        # height rooms: [(rectangle, height, name)] - a part stands no taller than the lowest
        # room its courtyard reaches into (else room_default); a part's height is Part.height
        self.rooms, self.room_default = list(rooms), room_default
        # iron room: [(ref, face, zone, min)] - a hand-soldered part's pads on the face it is
        # soldered on, grown 0.25 mm; every other courtyard on that face keeps `min` off it
        self.iron = list(iron)
        # the LEDs' cone, a COST not a rule (no seat on a narrow board takes a tall part out of
        # a wide cone): (LED courtyards, LED height, tan(half angle), mm of airwire per mm into
        # it) - a part h tall is in it by (h - LED height) - d / tan, d its gap to the LEDs
        self.cone = None
        # power nets (the layer-limited rails): attract as signals do, but a part on nothing
        # else is a bulk or decoupling part for the cone's purposes
        self.power = set()
        # ground and power nets: they do not attract (a pour or a rail reaches every pad), so
        # no airwire of theirs is scored
        self.rails = set(rails)
        # parts not seated yet (a cold placement): no seat keeps off them, no airwire ends on them
        self.unplaced = set()
        self.islands = dict(islands or {})
        self.edge = edge
        self.inside = outline.buffer(-edge)

    def far_ends(self, part, cluster):
        """Each pad of `part`: the nearest pad of the same net on a part outside the cluster."""
        out = []
        for n, xy in part.pads:
            if not n or n.startswith("unconnected") or n in self.rails:
                continue
            cand = [q for r, p in self.parts.items() if r not in cluster and r not in self.unplaced for (m, q) in p.pads if m == n]
            if cand:
                out.append((n, xy, min(cand, key=lambda q: math.dist(q, xy))))
        return out


def courtyard_of(fp, pcbnew):
    """The footprint's courtyard (F or B) as a polygon; else its pads' hull, 0.25 out."""
    ps = []
    for g in fp.GraphicalItems():
        if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            if g.GetShape() == pcbnew.SHAPE_T_CIRCLE:
                c = g.GetCenter()
                ps.append(Point(pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)).buffer(pcbnew.ToMM(g.GetRadius())))
            elif g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                a, b = g.GetStart(), g.GetEnd()
                ps.append(LineString([(pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)), (pcbnew.ToMM(b.x), pcbnew.ToMM(b.y))]))
            elif g.GetShape() in (pcbnew.SHAPE_T_RECT, pcbnew.SHAPE_T_POLY):
                poly = g.GetPolyShape() if g.GetShape() == pcbnew.SHAPE_T_POLY else None
                if poly is None:
                    a, b = g.GetStart(), g.GetEnd()
                    ps.append(box(pcbnew.ToMM(a.x), pcbnew.ToMM(a.y), pcbnew.ToMM(b.x), pcbnew.ToMM(b.y)))
                else:
                    o = poly.Outline(0)
                    ps.append(Polygon([(pcbnew.ToMM(o.CPoint(j).x), pcbnew.ToMM(o.CPoint(j).y)) for j in range(o.PointCount())]))
    polys = [p for p in ps if p.geom_type == "Polygon"]
    lines = [p for p in ps if p.geom_type == "LineString"]
    if lines:
        from shapely.ops import polygonize
        polys += list(polygonize(unary_union(lines)))
    if polys:
        return unary_union(polys)
    pts = []
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        pts += [(pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())), (pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))]
    from shapely.geometry import MultiPoint
    return MultiPoint(pts).envelope.buffer(0.25, join_style="mitre")


def board_of(kboard, islands=(), edge=0.3, rails=()):
    """The packer's Board from a KiCad board. islands: net names whose copper zones are islands;
    rails: ground and power nets, which are not scored."""
    import pcbnew
    import pcb_route2
    parts = []
    for fp in kboard.GetFootprints():
        pads = []
        cop = {"F": [], "B": []}
        for pad in fp.Pads():
            c = pad.GetPosition()
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            pads.append((pad.GetNetname(), (pcbnew.ToMM(c.x), pcbnew.ToMM(c.y))))
            for face, lid in (("F", pcbnew.F_Cu), ("B", pcbnew.B_Cu)):
                if pad.IsOnLayer(lid):
                    cop[face].append(pcb_route2._poly_of(pad.GetEffectivePolygon(lid)))
        parts.append(Part(fp.GetReference(), pads, courtyard_of(fp, pcbnew), fp.GetOrientationDegrees(), fp.IsLocked(), fp,
                          "B" if fp.IsFlipped() else "F", {k: unary_union(v) for k, v in cop.items() if v}))
    keep, holes, isl = [], [], {}
    for z in kboard.Zones():
        g = pcb_route2._poly_of(z.Outline())
        if z.GetIsRuleArea() and z.GetDoNotAllowFootprints():
            keep.append(g)
        elif not z.GetIsRuleArea() and z.GetNetname() in islands:
            isl[z.GetNetname()] = unary_union([isl[z.GetNetname()], g]) if z.GetNetname() in isl else g
    for fp in kboard.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                c = pad.GetPosition()
                holes.append(Point(pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)).buffer(pcbnew.ToMM(pad.GetDrillSize().x) / 2))
    return Board(pcb_route2.outline_of(kboard), parts, keep, holes, isl, edge, rails)


# ------------------------------------------------------------------ the rules: one list

def _r_courtyard(bd, part, placed):
    hit = [r for r, q in placed.items() if r != part.ref and r not in bd.unplaced and q.side == part.side
           and part.court.intersection(q.court).area > 1e-6]
    return [f"courtyard overlaps {', '.join(hit)}"] if hit else []


def _r_edge(bd, part, placed):
    return [] if bd.inside.contains(part.court) or bd.outline.buffer(-0.0).contains(part.court) and \
        part.court.distance(bd.outline.exterior) >= bd.edge - 1e-6 else ["courtyard over the board edge clearance"]


def _r_keepout(bd, part, placed):
    return ["courtyard on a footprint keep-out (moat)"] if any(part.court.intersects(k) and part.court.intersection(k).area > 1e-6
                                                               for k in bd.keepouts) else []


def _r_holes(bd, part, placed):
    return ["courtyard over an unplated hole"] if any(part.court.intersects(h) for h in bd.holes) and part.ref not in \
        getattr(bd, "hole_owners", set()) else []


def room_of(bd, part):
    """(the room's height, its name) for a part's courtyard: the lowest it reaches into."""
    room, where = bd.room_default, "where no room is lower"
    for rect, h, name in bd.rooms:
        if part.court.intersects(rect) and part.court.intersection(rect).area > 1e-3 and (room is None or h < room):
            room, where = h, name
    return room, where


def _r_height(bd, part, placed):
    if part.height is None or part.side != "F":
        return []
    room, where = room_of(bd, part)
    return [f"stands {part.height:g} mm; its room ({where}) is {room:g}"] if room is not None and part.height > room + 1e-6 else []


def _r_iron(bd, part, placed):
    out = []
    for ref, face, zone, mn in bd.iron:
        if ref != part.ref and face == part.side and part.court.distance(zone) < mn - 1e-3:
            out.append(f"within {mn:g} mm of {ref}'s pads (iron room)")
    return out


def _r_island(bd, part, placed):
    out = []
    for net, poly in bd.islands.items():
        if net in part.nets():
            if not poly.buffer(1e-6).contains(part.court):
                out.append(f"on {net} but its courtyard is not wholly inside the island")
        elif part.court.intersection(poly).area > 1e-6:
            out.append(f"not on {net} but its courtyard is over the island")
    return out


def _r_pads(bd, part, placed):
    """A courtyard over another part's pad on its own face: a through-hole pin standing out
    of the bottom, under a part placed there."""
    hit = [r for r, q in placed.items() if r != part.ref and r not in bd.unplaced and part.side in q.copper
           and part.court.intersection(q.copper[part.side]).area > 1e-6]
    return [f"courtyard over a pad of {', '.join(hit)}"] if hit else []


RULES = [("courtyard", _r_courtyard), ("edge", _r_edge), ("keepout", _r_keepout), ("hole", _r_holes), ("pads", _r_pads),
         ("height", _r_height), ("iron", _r_iron), ("island", _r_island)]


def violations(bd, part, placed):
    return [(name, msg) for name, f in RULES for msg in f(bd, part, placed)]


# ------------------------------------------------------------------ scoring

def airwires(bd, cluster, placed):
    """The cluster's airwires: from each moved part's pads to their far ends, and from the
    anchor's pads to the cluster parts on their nets."""
    out = []
    for r in cluster:
        p = placed[r]
        for n, a, b in bd.far_ends(p, set(cluster)):
            out.append((n, a, b))
        # inside the cluster too: pad to nearest same-net pad of another cluster part
        for n, a in p.pads:
            if not n or n in bd.rails:
                continue
            cand = [q for s in cluster if s != r for m, q in placed[s].pads if m == n]
            if cand:
                out.append((n, a, min(cand, key=lambda q: math.dist(q, a))))
    return out


def score(bd, cluster, placed):
    """(detours, crossings, length): `detours` - airwires with BOTH ends off every island that
    still pass over an island or a footprint keep-out (the moat), the shape of the main
    board's MIDI fault; an airwire into an island is how its parts are wired, not a detour.
    `crossings` - pairs of different nets' airwires that cross. `length` - the tiebreak."""
    aw = airwires(bd, cluster, placed)
    ls = [LineString([a, b]) if a != b else None for _, a, b in aw]
    x = 0
    for i in range(len(aw)):
        for j in range(i + 1, len(aw)):
            if ls[i] is not None and ls[j] is not None and aw[i][0] != aw[j][0] and ls[i].crosses(ls[j]):
                x += 1
    bad = 0
    for (n, a, b), l in zip(aw, ls):
        if l is None:
            continue
        if any(poly.buffer(1e-6).contains(Point(p)) for poly in bd.islands.values() for p in (a, b)):
            continue
        if any(l.intersects(k) for k in bd.keepouts) or any(l.intersection(poly).length > 0.5 for poly in bd.islands.values()):
            bad += 1
    length = sum(l.length for l in ls if l is not None)
    if bd.cone is not None:
        length += bd.cone[3] * sum(cone_depth(bd, placed[r]) for r in cluster)
    return (bad, x, round(length, 3))


def cone_depth(bd, part):
    """How far (mm) a top part's top rises into the LEDs' cone (Board.cone); 0 if not."""
    if bd.cone is None or part.height is None or part.side != "F":
        return 0.0
    leds, led_h, t, _ = bd.cone
    if part.height <= led_h or part.court.intersects(leds):
        return 0.0
    return max(0.0, (part.height - led_h) - part.court.distance(leds) / t)


# ------------------------------------------------------------------ the search

class Packer:
    def __init__(self, bd, body=(), log=None, spacing=IRON, escape=None):
        """spacing: the DENSITY knob - the least air (mm) between a seated part's courtyard and
        any other's, and between neighbours in a row. Raising it spreads every cluster
        deterministically; it is a minimum gap, never a force. escape: {ref: (side, depth)} -
        a band `depth` mm deep along that side of that part's courtyard where no part may sit,
        left for its pins' tracks to fan out (a 1.27 mm header's)."""
        self.bd = bd
        self.body = set(body)
        self.placed = dict(bd.parts)
        self.log = log if log is not None else []
        self.frozen = set()
        self.spacing = float(spacing)
        self.escape = dict(escape or {})

    def escape_bands(self):
        out = []
        for ref, (side, depth) in self.escape.items():
            x0, y0, x1, y1 = self.placed[ref].court.bounds
            d = float(depth)
            out.append({"E": box(x1, y0, x1 + d, y1), "W": box(x0 - d, y0, x0, y1),
                        "S": box(x0, y1, x1, y1 + d), "N": box(x0, y0 - d, x1, y0)}[side])
        return out

    def movable(self, anchor, parts=None):
        a = self.placed[anchor]
        if parts:
            out = []
            for r in parts:
                if r not in self.placed:
                    raise SystemExit(f"pack: {r} is not on the board")
                if r == anchor:
                    raise SystemExit(f"pack: {r} is the anchor - the anchor does not move")
                if r in self.body:
                    raise SystemExit(f"pack: {r} is placed by the body CAD - nothing moves it")
                if self.placed[r].locked:
                    self.log.append(f"place lock released: {r} (named by operator)")
                out.append(r)
            return out
        nets = a.nets() - {"GND", ""}
        return sorted(r for r, p in self.placed.items() if r != anchor and r not in self.body and not p.locked
                      and r not in self.frozen and p.nets() & nets and len(p.pads) <= 3)

    def sides_for(self, anchor, cluster):
        """The sides of the anchor each part's far ends leave on: {ref: side}."""
        a = self.placed[anchor]
        ax, ay = a.court.centroid.x, a.court.centroid.y
        out = {}
        for r in cluster:
            p = self.placed[r]
            fe = self.bd.far_ends(p, set(cluster) | {anchor})
            if fe:
                fx = sum(q[0] for _, _, q in fe) / len(fe)
                fy = sum(q[1] for _, _, q in fe) / len(fe)
            else:
                # nothing placed to reach: toward the board's interior (a part at an edge
                # connector has nowhere else to go)
                c = self.bd.outline.representative_point() if not self.bd.outline.contains(self.bd.outline.centroid) \
                    else self.bd.outline.centroid
                fx, fy = (c.x, c.y) if math.dist((c.x, c.y), (ax, ay)) > 1e-6 else (ax + 1, ay)
            # the pad on the anchor this part joins sets where it sits along the side
            out[r] = max(SIDES, key=lambda s: SIDES[s][0] * (fx - ax) + SIDES[s][1] * (fy - ay))
        return out

    def _side_order(self, anchor, refs):
        """The four sides of the anchor, best first for these parts: toward their far ends
        (or the board's interior), then the two across, then away."""
        a = self.placed[anchor]
        ax, ay = a.court.centroid.x, a.court.centroid.y
        s0 = self.sides_for(anchor, refs)
        ux, uy = 0.0, 0.0
        for r in refs:
            ux, uy = ux + SIDES[s0[r]][0], uy + SIDES[s0[r]][1]
        c = self.bd.outline.centroid
        return sorted(SIDES, key=lambda s: (-(SIDES[s][0] * ux + SIDES[s][1] * uy),
                                            -(SIDES[s][0] * (c.x - ax) + SIDES[s][1] * (c.y - ay))))

    def anchor_pin(self, anchor, part):
        """Where along the anchor the part joins it: the anchor pad on its nets (or None)."""
        a = self.placed[anchor]
        hits = [q for n, q in a.pads if n and n in part.nets() and n != "GND"]
        if not hits:
            hits = [q for n, q in a.pads if n and n in part.nets()]
        return hits[0] if hits else None

    def _blocked(self, cluster):
        """Everything a seat must keep off, fixed for this cluster's search: the other parts'
        courtyards (per side), the footprint keep-outs and the unplated holes."""
        per = {}
        for r, p in self.placed.items():
            if r not in cluster and r not in self.bd.unplaced:
                per.setdefault(p.side, []).append(p.court)
                for face, g in p.copper.items():          # pads on each face, through-hole pins on both
                    if face != p.side:
                        per.setdefault(face, []).append(g)
        # the density knob: other parts' courtyards grown by the spacing (less a hair, so a seat
        # exactly `spacing` away is legal)
        grow = max(0.0, self.spacing - 1e-3)
        side = {k: (unary_union(v).buffer(grow, join_style="mitre"), None) for k, v in per.items()}
        side = {k: (g, prep(g)) for k, (g, _) in side.items()}
        bands = self.escape_bands()
        hard = unary_union(self.bd.keepouts + self.bd.holes + bands) if (self.bd.keepouts or self.bd.holes or bands) else None
        return {"side": side, "hard": (hard, prep(hard)) if hard is not None else None}

    def seat_ok(self, part, fixed, row):
        """The fast form of RULES for one seat, against a field built once per cluster."""
        if not self.bd.inside.contains(part.court):
            return False
        s = fixed["side"].get(part.side)
        if s is not None and s[1].intersects(part.court) and part.court.intersection(s[0]).area > 1e-6:
            return False
        h = fixed["hard"]
        if h is not None and h[1].intersects(part.court) and (part.court.intersection(h[0]).area > 1e-6
                                                              or any(part.court.intersects(x) for x in self.bd.holes)):
            return False
        for q in row.values():
            if q.ref != part.ref and q.side == part.side and \
                    part.court.intersection(q.court.buffer(max(0.0, self.spacing - 1e-3), join_style="mitre")).area > 1e-6:
                return False
        for net, poly in self.bd.islands.items():
            if net in part.nets():
                if not poly.buffer(1e-6).contains(part.court):
                    return False
            elif part.court.intersection(poly).area > 1e-6:
                return False
        if part.height is not None and part.side == "F" and (self.bd.rooms or self.bd.room_default is not None):
            room, _ = room_of(self.bd, part)
            if room is not None and part.height > room + 1e-6:
                return False
        for ref, face, zone, mn in self.bd.iron:
            if ref != part.ref and face == part.side and part.court.distance(zone) < mn - 1e-3:
                return False
        return True

    def _row(self, anchor, o, protos, side, off, start, pitch, fixed, chosen):
        """The row: parts `o` in order, `off` mm beyond the anchor's courtyard on `side`,
        centred `start` mm along it, at `pitch`. (row, None) or (None, (ref, seat)) - the
        first part with no seat, and the seat it was refused."""
        a = self.placed[anchor]
        x0, y0, x1, y1 = a.court.bounds
        acx, acy = a.court.centroid.x, a.court.centroid.y
        ux, uy = SIDES[side]
        depth = max((p.court.bounds[2] - p.court.bounds[0]) if ux else (p.court.bounds[3] - p.court.bounds[1])
                    for p in protos.values())
        span = pitch * (len(o) - 1)
        row = {}
        for k, r in enumerate(o):
            t = start - span / 2 + k * pitch
            if ux:          # an east or west row runs along y
                cx, cy = ((x1 + off + depth / 2) if ux > 0 else (x0 - off - depth / 2)), acy + t
            else:           # a north or south row runs along x
                cx, cy = acx + t, ((y1 + off + depth / 2) if uy > 0 else (y0 - off - depth / 2))
            p = protos[r]
            px, py = p.centroid
            cand = p.moved(snap(cx - px), snap(cy - py))
            if not self.seat_ok(cand, fixed, {**chosen, **row}):
                return None, (r, cand)
            row[r] = cand
        return row, None

    def _search_side(self, anchor, cluster, refs, side, protos, orders, offs, starts, pitches, fixed, chosen):
        best = None
        for o in orders:
            for off in offs:
                for pitch in pitches:
                    for start in starts:
                        row, _ = self._row(anchor, o, protos, side, off, start, pitch, fixed, chosen)
                        if row is None:
                            continue
                        trial = dict(self.placed)
                        trial.update(chosen)
                        trial.update(row)
                        key = (score(self.bd, cluster, trial), off, abs(start))
                        if best is None or key < best[0]:
                            best = (key, row, (o, off, start, pitch))
                if best is not None and best[0][1] <= off - 2.0:
                    break           # the nearest legal rows win: further out cannot be shorter
        return best

    def pack(self, anchor, parts=None, side=None, grow=None, rotations=(0,), step=0.25, coarse=1.0):
        """Seat `parts` (default: the anchor's passives) in rows round `anchor`, one row per
        side the parts' far ends leave on. Each side is searched at `coarse` mm, then at
        `step` mm round the best. Returns a report; the seats are applied to self.placed
        only if every part passes the full rule list."""
        if anchor not in self.placed:
            raise SystemExit(f"pack: anchor {anchor} is not on the board")
        cluster = self.movable(anchor, parts)
        if not cluster:
            raise SystemExit(f"pack: nothing to pack round {anchor}")
        before = score(self.bd, cluster, self.placed)
        sides = self.sides_for(anchor, cluster)
        if side:
            allowed = list(side)
            sides = {r: (s if s in allowed else allowed[0]) for r, s in sides.items()}
        fixed = self._blocked(set(cluster))
        groups = {}
        for r, s in sides.items():
            groups.setdefault(s, []).append(r)
        reach = grow if grow else 12.0
        chosen = {}
        rep = {"anchor": anchor, "parts": cluster, "sides": sides, "before": before}
        tried = {}
        queue = sorted(groups, key=lambda s: (-len(groups[s]), s))
        failure = None
        while queue:
            s = queue.pop(0)
            refs = groups.pop(s)
            tried.setdefault(s, set()).update(refs)
            ux, uy = SIDES[s]
            vx, vy = -uy, ux
            def along(r):
                q = self.anchor_pin(anchor, self.placed[r])
                c = q if q else self.placed[r].centroid
                return c[0] * vx + c[1] * vy
            base = sorted(refs, key=along)
            orders = [base, base[::-1]] + ([list(p) for p in itertools.permutations(base)] if len(base) <= 4 else [])
            orders = [o for i, o in enumerate(orders) if o not in orders[:i]]
            best = None
            for rot in rotations:
                protos = {r: (self.placed[r].turned(rot) if rot else self.placed[r]) for r in refs}
                widths = [(p.court.bounds[3] - p.court.bounds[1]) if ux else (p.court.bounds[2] - p.court.bounds[0])
                          for p in protos.values()]
                pitch0 = max(widths) + self.spacing
                pitches = (pitch0, pitch0 + 0.5, pitch0 + 1.0)
                b1 = self._search_side(anchor, cluster, refs, s, protos, orders, _frange(0.0, reach, coarse),
                                       _frange2(-reach, reach, coarse), pitches, fixed, chosen)
                if b1 is None:
                    continue
                o, off, start, pitch = b1[2]
                b2 = self._search_side(anchor, cluster, refs, s, protos, [o], _frange2(max(0.0, off - coarse), off + coarse, step),
                                       _frange2(start - coarse, start + coarse, step), pitches, fixed, chosen)
                cand = min([b for b in (b1, b2) if b is not None], key=lambda b: b[0])
                if best is None or cand[0] < best[0]:
                    best = cand
            if best is None:
                # the failure path: the nearest row, and what refused its first part
                protos = {r: self.placed[r] for r in refs}
                pitch0 = max((p.court.bounds[3] - p.court.bounds[1]) if ux else (p.court.bounds[2] - p.court.bounds[0])
                             for p in protos.values()) + self.spacing
                _, why = self._row(anchor, base, protos, s, 0.0, 0.0, pitch0, fixed, chosen)
                trial = dict(self.placed)
                trial.update(chosen)
                if why:
                    trial[why[0]] = why[1]
                    v = violations(self.bd, why[1], trial) or [("box", "outside the board's edge clearance")]
                    reason = f"; the nearest row's {why[0]}: " + "; ".join(m for _, m in v)
                else:
                    reason = ""
                failure = failure or f"no legal row on side {s} for {', '.join(refs)} within {reach} mm of {anchor}{reason}"
                # the other sides, in the order the anchor's own side preference gives (not
                # with side=: the caller pinned it)
                nxt = [t for t in self._side_order(anchor, refs) if refs[0] not in tried.get(t, set())] if not side else []
                if not nxt:
                    rep["result"] = failure
                    return rep
                self.log.append(f"pack: {', '.join(refs)} - no row on side {s} of {anchor}, trying side {nxt[0]}")
                groups.setdefault(nxt[0], []).extend(refs)
                if nxt[0] not in queue:
                    queue.append(nxt[0])
                continue
            chosen.update(best[1])
        trial = dict(self.placed)
        trial.update(chosen)
        bad = {r: violations(self.bd, trial[r], trial) for r in cluster}
        bad = {r: v for r, v in bad.items() if v}
        if bad:
            rep["result"] = "rows found but the full rule list refuses: " + "; ".join(f"{r}: {v}" for r, v in bad.items())
            return rep
        self.placed.update(chosen)
        self.frozen |= set(cluster)
        self.bd.unplaced -= set(cluster)
        rep["after"] = score(self.bd, cluster, self.placed)
        rep["seats"] = {r: (round(self.placed[r].centroid[0], 3), round(self.placed[r].centroid[1], 3), self.placed[r].rot)
                        for r in cluster}
        rep["result"] = "packed"
        return rep

    def pattern(self, anchors, roles, axis=("x", "y"), step=0.25, reach=12.0, pitch_extra=(0.0, 0.5, 1.0), coarse=1.0,
                rotations=(0,)):
        """One arrangement, searched once and stamped at every anchor: `roles` maps each
        anchor to its parts in role order (the same roles at every anchor). The row's
        offset from the anchor, its axis and its pitch are shared; every instance must be
        legal, and the score is the sum over instances. Searched at `coarse` mm over the
        whole reach, then at `step` mm within one coarse step of the best. `rotations`: the
        turns (degrees, the same for every part) tried."""
        first = self._pattern(anchors, roles, axis, coarse, (-reach, reach), (-reach, reach), pitch_extra, rotations=rotations)
        if first.get("result") != "packed-pending":
            return first
        ax_, order, dx, dy, extra, rot = first["_best"][2]
        fine = self._pattern(anchors, roles, (ax_,), step, (dx - coarse, dx + coarse), (dy - coarse, dy + coarse),
                             (extra,), orders=[order], rotations=(rot,))
        fine["configurations"] += first["configurations"]
        return self._commit_pattern(anchors, roles, fine if fine.get("result") == "packed-pending" else first)

    def _pattern(self, anchors, roles, axis, step, xr, yr, pitch_extra, orders=None, rotations=(0,)):
        anchors = list(anchors)
        for a in anchors:
            for r in roles[a]:
                if r in self.body:
                    raise SystemExit(f"pack: {r} is placed by the body CAD - nothing moves it")
        allp = [r for a in anchors for r in roles[a]]
        fixed = self._blocked(set(allp))
        best = None
        n = len(roles[anchors[0]])
        orders = orders or list(itertools.permutations(range(n)))
        tried = 0
        # each anchor's turn against the first's: the arrangement turns with its anchor (a
        # switch at 180 degrees carries the same T turned 180 - the main board's networks:)
        a0 = self.placed[anchors[0]].rot
        dturn = {a: round(((self.placed[a].rot - a0) % 360) / 90) * 90 % 360 for a in anchors}
        for ax_, rot in itertools.product(axis, rotations):
            turned = {r: self.placed[r].turned((rot + dturn[a]) % 360) if (rot + dturn[a]) % 360 else self.placed[r]
                      for a in anchors for r in roles[a]}
            for order in orders:
                for dx in _frange2(xr[0], xr[1], step):
                    for dy in _frange2(yr[0], yr[1], step):
                        for extra in pitch_extra:
                            seats = {}
                            ok = True
                            for a in anchors:
                                A = self.placed[a]
                                acx, acy = A.court.centroid.x, A.court.centroid.y
                                parts = [turned[roles[a][k]] for k in order]
                                # the pitch from the first anchor's parts: one spacing for every
                                # instance, whatever its turn
                                p0 = [turned[roles[anchors[0]][k]] for k in order]
                                ws = [(p.court.bounds[2] - p.court.bounds[0]) if ax_ == "x" else (p.court.bounds[3] - p.court.bounds[1])
                                      for p in p0]
                                pitch = max(ws) + self.spacing + extra
                                span = pitch * (len(parts) - 1)
                                for k, p in enumerate(parts):
                                    t = -span / 2 + k * pitch
                                    ox, oy = (dx + t, dy) if ax_ == "x" else (dx, dy + t)
                                    ox, oy = _kturn(ox, oy, dturn[a])
                                    cx, cy = acx + ox, acy + oy
                                    px, py = p.centroid
                                    cand = p.moved(snap(cx - px), snap(cy - py))
                                    if not self.seat_ok(cand, fixed, seats):
                                        ok = False
                                        break
                                    seats[p.ref] = cand
                                if not ok:
                                    break
                            tried += 1
                            if not ok:
                                continue
                            trial = dict(self.placed)
                            trial.update(seats)
                            sc = [score(self.bd, roles[a], trial) for a in anchors]
                            key = (sum(s[0] for s in sc), sum(s[1] for s in sc), round(sum(s[2] for s in sc), 2),
                                   abs(dx) + abs(dy))
                            if best is None or key < best[0]:
                                best = (key, seats, (ax_, order, dx, dy, extra, rot))
        rep = {"anchors": anchors, "configurations": tried}
        if best is None:
            rep["result"] = f"no arrangement legal at all {len(anchors)} anchors within the search window"
            return rep
        rep.update(result="packed-pending", _best=best)
        return rep

    def _commit_pattern(self, anchors, roles, rep):
        if rep.get("result") != "packed-pending":
            return rep
        best = rep.pop("_best")
        allp = [r for a in anchors for r in roles[a]]
        trial = dict(self.placed)
        trial.update(best[1])
        bad = {r: violations(self.bd, trial[r], trial) for r in allp}
        bad = {r: v for r, v in bad.items() if v}
        if bad:
            rep["result"] = "the arrangement fails the full rule list: " + "; ".join(f"{r}: {v}" for r, v in bad.items())
            return rep
        self.placed.update(best[1])
        self.frozen |= set(allp)
        self.bd.unplaced -= set(allp)
        ax_, order, dx, dy, extra, rot = best[2]
        rep.update(result="packed", arrangement={"axis": ax_, "order": [roles[anchors[0]][k] for k in order],
                                                 "offset": (dx, dy), "pitch_extra": extra, "turn": rot},
                   score=best[0][:3], seats={r: (round(best[1][r].centroid[0], 3), round(best[1][r].centroid[1], 3)) for r in allp})
        return rep

    def cold(self, sheets, patterns=(), turns=(0, 90, 180, 270), reaches=(12.0, 20.0)):
        """Seat every part still in self.bd.unplaced, in the order each has an anchor:
          1. `patterns`: [(anchors, roles)] - one arrangement stamped at every anchor;
          2. each unplaced IC or semiconductor (more than three pads, or U/Q/L/NT): round the
             placed part it shares the most signal nets with (its own sheet first), any of
             `turns`;
          3. the passives: each round the placed part it shares the most signal nets with,
             a rail-only part (a decoupler) round the part on its own sheet with the most pads
             on its nets - grouped by anchor, a group that cannot be seated tried part by part.
        `sheets`: {ref: sheet name}. A part with no seat within the last of `reaches` stays
        unplaced and is reported by name. Returns [(what, refs, result)]."""
        rep = []
        rails = self.bd.rails

        def signal(r):
            return {n for n, _ in self.placed[r].pads if n and not n.startswith("unconnected") and n not in rails}

        def all_nets(r):
            return {n for n, _ in self.placed[r].pads if n and not n.startswith("unconnected")}
        for anchors, roles in patterns:
            # one arrangement at every anchor if it fits; else one per set of anchors at the
            # same turn; else each anchor its own - the same T where the board allows it,
            # the nearest legal one where it does not, each step logged
            sets = [list(anchors)]
            while sets:
                grp = sets.pop(0)
                r_ = self.pattern(grp, roles, rotations=(0, 90))
                rep.append((f"pattern at {', '.join(grp)}", [x for a in grp for x in roles[a]], r_.get("result")))
                if r_.get("result") == "packed":
                    continue
                self.log.append(f"cold: the pattern at {', '.join(grp)} - {r_.get('result')}")
                if len(grp) == 1:
                    continue
                turns_ = {}
                for a in grp:
                    turns_.setdefault(round(self.placed[a].rot) % 360, []).append(a)
                sets = (list(turns_.values()) if len(turns_) > 1 else [[a] for a in grp]) + sets
        big = lambda r: len(self.placed[r].pads) > 3 or re.match(r"^(U|Q|L|NT)\d", r) is not None
        progress = True
        while progress:
            progress = False
            todo = sorted((r for r in self.bd.unplaced if big(r)),
                          key=lambda r: -max([len(signal(r) & signal(q)) for q in self.placed if q not in self.bd.unplaced] + [0]))
            for r in todo:
                placed = [q for q in self.placed if q not in self.bd.unplaced and q != r]
                cand = sorted(placed, key=lambda q: (-len(signal(r) & signal(q)), sheets.get(q) != sheets.get(r),
                                                     -len(self.placed[q].pads), q))
                if not cand or (not signal(r) & signal(cand[0]) and sheets.get(cand[0]) != sheets.get(r)):
                    continue            # no anchor yet: a later round, once its neighbours are seated
                res = None
                for reach in reaches:
                    res = self.pack(cand[0], [r], rotations=turns, grow=reach)
                    if res["result"] == "packed":
                        break
                rep.append((f"round {cand[0]}", [r], res["result"]))
                progress |= res["result"] == "packed"
        # the tall rail-only passives, where the LEDs' cone is a cost: each on its own, tried round every
        # placed part on its own sheet or sharing its nets (the nearest eight), kept where it
        # rises least into the cone, then by the score - a row round its group's anchor
        # would hold it beside that anchor whatever the cone
        if self.bd.cone is not None:
            led_h = self.bd.cone[1]
            # rail-only parts (bulk and decoupling): a part on a signal net, or on a connector's
            # net - a clamp across its pins - is held by its loop, not moved off for the light
            conn = {n for q in self.placed if q.startswith("J") and q not in self.bd.unplaced for n in signal(q)}
            for r in sorted(x for x in self.bd.unplaced if not big(x) and not (signal(x) - self.bd.power)
                            and not signal(x) & conn and (self.placed[x].height or 0) > led_h):
                own = all_nets(r) - rails
                cands = [q for q in self.placed if q not in self.bd.unplaced and q != r and not q.startswith("H")
                         and (own & all_nets(q) or sheets.get(r) and sheets.get(q) == sheets.get(r))]
                cands = sorted(cands, key=lambda q: (-len(own & all_nets(q)), -len(self.placed[q].pads), q))[:8]
                best = None
                for q in cands:
                    state = (dict(self.placed), set(self.frozen), set(self.bd.unplaced), len(self.log))
                    res = self.pack(q, [r], rotations=(0, 90), grow=reaches[-1])
                    if res["result"] == "packed":
                        key = (round(cone_depth(self.bd, self.placed[r]), 2), res["after"])
                        if best is None or key < best[0]:
                            best = (key, q, self.placed[r])
                    self.placed, self.frozen, self.bd.unplaced = state[0], state[1], state[2]
                    del self.log[state[3]:]
                if best is not None:
                    self.placed[r] = best[2]
                    self.frozen.add(r)
                    self.bd.unplaced.discard(r)
                    rep.append((f"round {best[1]} (least into the LEDs' cone, {best[0][0]:g} mm)", [r], "packed"))
                else:
                    self.log.append(f"cold: {r} (tall) found no seat round any of {len(cands)} anchor(s)")
        # the passives, grouped by their anchor
        groups = {}
        for r in sorted(self.bd.unplaced):
            if big(r):
                continue
            placed = [q for q in self.placed if q not in self.bd.unplaced]
            if signal(r):
                # a connector its net enters by beats a part on its own sheet: a clamp or a
                # series part belongs at the pin it guards
                key = lambda q: (-len(signal(r) & signal(q)), not q.startswith("J"), sheets.get(q) != sheets.get(r),
                                 -len(self.placed[q].pads), q)
            else:
                key = lambda q: (sheets.get(q) != sheets.get(r), -len(all_nets(r) & all_nets(q)), -len(self.placed[q].pads), q)
            a = min(placed, key=key)
            groups.setdefault(a, []).append(r)
        for a, refs in sorted(groups.items()):
            res = self.pack(a, refs, rotations=(0, 90), grow=reaches[0])
            if res["result"] == "packed":
                rep.append((f"round {a}", refs, "packed"))
                continue
            for r in refs:              # the group did not fit as rows: one by one, further out
                res1 = None
                for reach in reaches:
                    res1 = self.pack(a, [r], rotations=(0, 90), grow=reach)
                    if res1["result"] == "packed":
                        break
                rep.append((f"round {a}", [r], res1["result"]))
        if self.bd.unplaced:
            self.log.append(f"cold: NOT placed - {', '.join(sorted(self.bd.unplaced))}")
        return rep

    def apply(self, kboard):
        """Move each footprint by its pad centroid to its seat (and turn it), on `kboard`."""
        import pcbnew
        n = 0
        for r, p in self.placed.items():
            orig = self.bd.parts[r]
            if p is orig:
                continue
            fp = kboard.FindFootprintByReference(r)
            if p.rot != orig.rot:
                fp.SetOrientationDegrees(p.rot)
            cur = [pad.GetPosition() for pad in fp.Pads() if pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
            cx = sum(pcbnew.ToMM(c.x) for c in cur) / len(cur)
            cy = sum(pcbnew.ToMM(c.y) for c in cur) / len(cur)
            tx, ty = p.centroid
            pos = fp.GetPosition()
            fp.SetPosition(pcbnew.VECTOR2I(pos.x + pcbnew.FromMM(tx - cx), pos.y + pcbnew.FromMM(ty - cy)))
            n += 1
        return n


def _kturn(x, y, deg):
    """A vector turned as KiCad turns a part by `deg` (counter-clockwise on screen, y down)."""
    if not deg:
        return x, y
    a = math.radians(-deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def _frange2(a, b, s):
    """a..b in steps of s, nearest zero first."""
    out, k = [], 0
    while a + k * s <= b + 1e-9:
        out.append(round(a + k * s, 6))
        k += 1
    return sorted(out, key=lambda v: (abs(v), v))


def _frange(a, b, s):
    out, k = [], 0
    while a + k * s <= b + 1e-9:
        out.append(round(a + k * s, 6))
        k += 1
    # nearest first: the search prefers the nearest legal seat
    return sorted(out, key=lambda v: (abs(v), v))


# ------------------------------------------------------------------ the place report

def report(bd, anchors, body=()):
    """Per anchor: its cluster (the passives on its nets), their airwires, how many cross
    each other, how many cross a keep-out or a foreign island, and every rule broken.
    Returns (text, problems)."""
    lines, problems = [], 0
    for a in anchors:
        cl = [r for r, p in bd.parts.items() if r != a and r not in body and p.nets() & (bd.parts[a].nets() - {"GND", ""})
              and len(p.pads) <= 3]
        sc = score(bd, cl, bd.parts)
        bad = {r: violations(bd, bd.parts[r], bd.parts) for r in cl}
        bad = {r: v for r, v in bad.items() if v}
        problems += sc[0] + len(bad)
        lines.append(f"{a}: cluster {', '.join(cl) or '-'}; airwire crossings {sc[1]}, detours over a keep-out or island {sc[0]}, "
                     f"length {sc[2]:.1f} mm")
        for r, v in bad.items():
            lines.append(f"  {r}: " + "; ".join(m for _, m in v))
    return "\n".join(lines), problems


# ------------------------------------------------------------------ command line

def main(argv=None):
    import argparse
    import pcbnew
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["pack", "report"])
    ap.add_argument("board")
    ap.add_argument("-o", "--out")
    ap.add_argument("--anchor")
    ap.add_argument("--anchors")
    ap.add_argument("--parts")
    ap.add_argument("--outside", help="an island net: its zones are islands")
    ap.add_argument("--island", help="same as --outside, for report")
    ap.add_argument("--side")
    ap.add_argument("--grow", type=float)
    ap.add_argument("--rotations", default="0")
    ap.add_argument("--body", default="")
    ap.add_argument("--rails", default="", help="ground and power nets: not scored")
    ap.add_argument("--spacing", type=float, default=IRON, help="density: least air between courtyards, mm")
    ap.add_argument("--escape", default="", help="REF:SIDE:MM[,...] - a fan-out band no part may sit in")
    a = ap.parse_args(argv)
    kb = pcbnew.LoadBoard(a.board)
    isl = [x for x in (a.outside, a.island) if x]
    bd = board_of(kb, isl, rails=[r for r in a.rails.split(",") if r])
    body = [r for r in a.body.split(",") if r]
    if a.cmd == "report":
        anchors = a.anchors.split(",") if a.anchors else sorted(r for r in bd.parts if r[0] in "JU")
        text, n = report(bd, anchors, body)
        print(text)
        return 1 if n else 0
    if not a.out or os.path.abspath(a.out) == os.path.abspath(a.board):
        raise SystemExit("pack: -o is required and must not be the source board")
    esc = {e.split(":")[0]: (e.split(":")[1], float(e.split(":")[2])) for e in a.escape.split(",") if e}
    pk = Packer(bd, body, spacing=a.spacing, escape=esc)
    rep = pk.pack(a.anchor, a.parts.split(",") if a.parts else None, a.side.split(",") if a.side else None, a.grow,
                  tuple(int(r) for r in a.rotations.split(",")))
    for k, v in rep.items():
        print(f"pack: {k}: {v}")
    for line in pk.log:
        print("pack: " + line)
    if rep.get("result") != "packed":
        return 1
    pk.apply(kb)
    pcbnew.SaveBoard(a.out, kb)
    print(f"pack: wrote {a.out}; its copper was not touched - route the moved parts' nets next")
    return 0


if __name__ == "__main__":
    sys.exit(main())
