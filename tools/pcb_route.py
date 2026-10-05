"""A small two-layer grid router for simple boards - tools/pcb.py's `route: true`.

Not a general autorouter. It is enough for a key board: a handful of short
digital nets and one power rail, on a board whose ground is two poured planes.

A MULTI-LAYER BOARD (the main board, `route: freerouting`) takes only the
pieces at the end of this file from it, the ones an autorouter would get wrong:
each plane net's pad to its plane by its own via (`fanout`), a pair of nets
side by side (`route_pair`), and the moat's keep-out round an analog island
(`moat_keepout`). Freerouting routes the rest (tools/pcb_freeroute.py).
Under `route: astar` the rest is `complete` - or, with layout.yaml `families:`,
`route_families`: family by family, each negotiated (issue #41; the comment above
route_families).

HOW IT WORKS
  * Both copper layers become grids (GRID mm). A cell is blocked for a net
    when a track of that net's width, centred there, would come closer than
    the clearance to copper of ANY OTHER net, to a hole, or to the board edge.
    Distances are computed exactly against each pad's outline (shapely), then
    a grid-slack margin is added so a segment between two free cells is free
    too.
  * Each net is routed as a tree: A* from everything already connected to the
    nearest pad not yet connected, 8-connected moves on a layer, a via to the
    other layer where a via fits. Vias cost more than distance; each layer
    has a preferred direction (top along the board, bottom across it) and a
    move against it costs extra; a turn costs by its angle, so a route is a
    few straight runs joined by 45-degree corners rather than a staircase.
  * Then rip-up and reroute: a net that took a real detour is ripped up with
    the nets crossing its corridor, routed first, and the result kept only if
    the group's total cost fell. (Rerouting a net with every other net still
    in place cannot improve it - it faces the same obstacles or more - which
    is what the first version of this pass did, improving nothing.)
  * Ground is routed last as an ordinary net, so no ground pin depends on a
    pour finding a way round the tracks; then both layers get a GND pour and
    each single-sided GND pad a stitching via into the other plane - except a
    pad already on the routed ground tree, which the tree's copper joins.
  * Every track, via and zone is written to the board, zones are filled, and
    tools/pcb.py's `check` runs KiCad's DRC over the result - the router
    proves nothing about itself; the DRC does.
"""
import heapq
import sys
import math

import pcbnew
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

GRID = 0.2
SLACK = GRID * 0.75
OWN_PAD_GAP = 0.05            # a via's ring to its own net's SMD pad: off it, not another net's clearance
# Search costs, in grid steps. A 45-degree turn is cheap, a 90-degree one is
# not, and anything sharper is as good as forbidden; a via is worth a detour
# of about 2.4 mm; a move against the layer's direction costs a third extra.
DIAG = 1.5
TURN = {1: 0.8, 2: 2.5, 3: 20.0, 4: 40.0}      # by the angle between moves, in 45-degree steps
VIA = 12.0
SOFT = 40.0       # complete's rip-up: entering a cell another net's routing holds
AGAINST = 0.35
TOP, BOT = 0, 1
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]
MM, TO = pcbnew.FromMM, pcbnew.ToMM


def fence_of(lay):
    """layout.yaml `route_fence: [x0, y0, x1, y1]` (board mm, KiCad's frame) as a sorted
    rectangle, or None: a run that may change copper only inside it (#40, a section
    re-routed on its own). Copper outside it is fixed, as locked copper is."""
    f = lay.get("route_fence")
    if not f:
        return None
    x0, y0, x1, y1 = (float(v) for v in f)
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def in_fence(t, f):
    """Every point of track or via t inside fence f (board mm)."""
    if isinstance(t, pcbnew.PCB_VIA):
        pts = [t.GetPosition()]
    else:
        pts = [t.GetStart(), t.GetEnd()] + ([t.GetMid()] if type(t) is pcbnew.PCB_ARC else [])
    return all(f[0] <= TO(q.x) <= f[2] and f[1] <= TO(q.y) <= f[3] for q in pts)


def is_fixed(t, f):
    """Copper no routing step may delete, move, split or merge away: locked, or outside
    the run's fence."""
    return t.IsLocked() or (f is not None and not in_fence(t, f))


def steps45(a, b):
    """The angle between two grid moves, in 45-degree steps (0-4)."""
    d = math.degrees(math.atan2(b[1], b[0]) - math.atan2(a[1], a[0])) % 360
    return round(min(d, 360 - d) / 45)


def pad_geom(pad):
    """The pad's copper as a shapely geometry, in mm."""
    poly = pad.GetEffectivePolygon(pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu)
    pts = []
    for i in range(poly.OutlineCount()):
        ol = poly.Outline(i)
        pts.append(Polygon([(TO(ol.CPoint(j).x), TO(ol.CPoint(j).y)) for j in range(ol.PointCount())]))
    return unary_union(pts)


def board_outline(board):
    segs = [(TO(d.GetStart().x), TO(d.GetStart().y), TO(d.GetEnd().x), TO(d.GetEnd().y))
            for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    # chain the segments into rings: the outline, and any cut-out inside it (a
    # multi-layer board's routed holes); a key board has the one ring
    rings, rest = [], segs
    while rest:
        pts = [(rest[0][0], rest[0][1]), (rest[0][2], rest[0][3])]
        rest = rest[1:]
        while math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]) >= 1e-3:
            x, y = pts[-1]
            for i, s in enumerate(rest):
                if math.hypot(s[0] - x, s[1] - y) < 1e-3:
                    pts.append((s[2], s[3]))
                    rest.pop(i)
                    break
                if math.hypot(s[2] - x, s[3] - y) < 1e-3:
                    pts.append((s[0], s[1]))
                    rest.pop(i)
                    break
            else:
                raise SystemExit("route: board outline is not closed")
        rings.append(pts)
    if len(rings) == 1:
        return Polygon(rings[0])
    rings.sort(key=lambda r: -Polygon(r).area)
    return Polygon(rings[0], rings[1:])


class Router:
    fence = None            # tidy sets the run's fence (fence_of) before square_joins
    def __init__(self, board, lay):
        self.board, self.lay = board, lay
        r = lay["rules"]
        self.clear, self.w, self.pw = r["clearance"], r["track"], r["power_track"]
        self.via, self.via_drill = r["via"], r["via_drill"]
        self.edge = r["edge_clearance"]
        self.outline = board_outline(board)
        minx, miny, maxx, maxy = self.outline.bounds
        self.x0, self.y0 = minx, miny
        self.nx, self.ny = int((maxx - minx) / GRID) + 2, int((maxy - miny) / GRID) + 2
        # copper per net and per layer: (net, layer) -> list of geometries
        self.copper = []            # (netname, layer set, geometry, kind) - kind is 'pad' or 'track'
        self.holes = []             # unplated holes and keep-outs: no copper of any net
        self.pth_holes = []         # plated holes: kept apart from vias only
        self.smd = []               # (net, layer set, geometry): SMD pads - no via in or on them, not even their own net's
        self.owned = {}             # net -> [(board item, copper entry, hole)] its routes added
        self.pad_at = {}            # "REF.PIN" -> index of the pad's entry in self.copper
        self.tree_pads = {}         # net -> copper indices of the pads its main tree joined
        self.prejoined = {}         # net -> (pad indices, cells) joined by connect_first
        self.silk = []              # silkscreen outlines: no via under them (a via under silk
                                    # prints the legend onto a tented hole)
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                net = pad.GetNetname()
                layers = {L for L, lid in enumerate(LAYERS) if pad.IsOnLayer(lid)}
                g = pad_geom(pad)
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    self.holes.append(g)
                    continue
                self.pad_at[f"{fp.GetReference()}.{pad.GetNumber()}"] = len(self.copper)
                self.copper.append((net, layers, g, "pad"))
                if not pad.HasHole():
                    # reflowed on this side: a via in the pad is an untented hole that
                    # wicks its solder away, so a via keeps off every SMD pad, its own too
                    self.smd.append((net, layers, g))
                if pad.HasHole():
                    # a plated hole: its pad's copper already keeps other nets' tracks
                    # away, so it matters only to vias (hole to hole)
                    self.pth_holes.append(Point(TO(pad.GetPosition().x), TO(pad.GetPosition().y)).buffer(TO(pad.GetDrillSize().x) / 2))
        # keep-outs (the standoffs' faces and screw heads): obstacles on every layer
        for z in board.Zones():
            if z.GetIsRuleArea() and z.GetDoNotAllowTracks():
                ol = z.Outline().Outline(0)
                self.holes.append(Polygon([(TO(ol.CPoint(k).x), TO(ol.CPoint(k).y)) for k in range(ol.PointCount())]))
        silk_layers = (pcbnew.F_SilkS, pcbnew.B_SilkS)
        items = [d for d in board.GetDrawings() if d.GetLayer() in silk_layers]
        for fp in board.GetFootprints():
            items += [g for g in fp.GraphicalItems() if g.GetLayer() in silk_layers]
            items += [f for f in fp.GetFields() if f.GetLayer() in silk_layers and f.IsVisible()]
        for it in items:
            bb = it.GetBoundingBox()
            self.silk.append(box(TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom())))
        self.inside = self.outline.buffer(-self.edge)

    def cell_xy(self, i, j):
        return (self.x0 + i * GRID, self.y0 + j * GRID)

    def blocked(self, net, width, via=False):
        """A boolean grid per layer: True where this net cannot put a track (or a via) centre."""
        half = (self.via / 2 if via else width / 2)
        grids = [[[False] * self.ny for _ in range(self.nx)] for _ in (TOP, BOT)]
        for L in (TOP, BOT):
            obst = [g for (n, ls, g, _) in self.copper if L in ls and n != net]
            obst += self.holes + (self.pth_holes + self.silk if via else [])
            rad = half + self.clear + SLACK
            if via:
                # its own net's SMD pads: off the pad (and its mask opening, which is
                # the pad: pad_to_mask_clearance 0), not the clearance another net needs
                own = [g.buffer(OWN_PAD_GAP - self.clear) for (n, ls, g) in self.smd if n == net and L in ls]
                obst += own
            for g in obst:
                gx0, gy0, gx1, gy1 = g.bounds
                i0, i1 = max(0, int((gx0 - rad - self.x0) / GRID)), min(self.nx - 1, int((gx1 + rad - self.x0) / GRID) + 1)
                j0, j1 = max(0, int((gy0 - rad - self.y0) / GRID)), min(self.ny - 1, int((gy1 + rad - self.y0) / GRID) + 1)
                for i in range(i0, i1 + 1):
                    for j in range(j0, j1 + 1):
                        if not grids[L][i][j] and g.distance(Point(*self.cell_xy(i, j))) < rad:
                            grids[L][i][j] = True
            inner = self.outline.buffer(-(self.edge + half + SLACK))
            for i in range(self.nx):
                for j in range(self.ny):
                    if not grids[L][i][j] and not inner.contains(Point(*self.cell_xy(i, j))):
                        grids[L][i][j] = True
        return grids

    def pad_cells(self, net):
        """Cells inside each pad of this net: (pad id, layer set, cells)."""
        out = []
        for k, (n, ls, g, kind) in enumerate(self.copper):
            if n != net or kind != "pad":
                continue
            gx0, gy0, gx1, gy1 = g.bounds
            cells = [(i, j) for i in range(int((gx0 - self.x0) / GRID), int((gx1 - self.x0) / GRID) + 2)
                     for j in range(int((gy0 - self.y0) / GRID), int((gy1 - self.y0) / GRID) + 2)
                     if g.buffer(-0.05).contains(Point(*self.cell_xy(i, j)))]
            if not cells:
                c = g.centroid
                cells = [(round((c.x - self.x0) / GRID), round((c.y - self.y0) / GRID))]
            out.append((k, ls, cells, g))
        return out

    def astar(self, sources, targets, grid, vgrid):
        """sources, targets: sets of (layer, i, j). Returns the path as a list of (layer, i, j)."""
        tx = [(i, j) for (_, i, j) in targets]
        cx, cy = sum(i for i, _ in tx) / len(tx), sum(j for _, j in tx) / len(tx)

        def h(i, j):
            return min(math.hypot(i - a, j - b) for a, b in tx) if len(tx) < 40 else math.hypot(i - cx, j - cy)
        openq, came, cost = [], {}, {}
        for s in sources:
            cost[s] = 0
            heapq.heappush(openq, (h(s[1], s[2]), 0, s, None))
        moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, DIAG), (1, -1, DIAG), (-1, 1, DIAG), (-1, -1, DIAG)]
        seen = set()
        while openq:
            f, g, cur, prevdir = heapq.heappop(openq)
            if cur in seen:
                continue
            seen.add(cur)
            if cur in targets:
                path = [cur]
                while path[-1] in came:
                    path.append(came[path[-1]][0])
                return path[::-1]
            L, i, j = cur
            for di, dj, c in moves:
                ni, nj = i + di, j + dj
                if not (0 <= ni < self.nx and 0 <= nj < self.ny) or grid[L][ni][nj]:
                    continue
                if di and dj and (grid[L][i + di][j] or grid[L][i][j + dj]):
                    continue            # no corner-cutting past an obstacle
                nxt = (L, ni, nj)
                turn = TURN.get(steps45(prevdir, (di, dj)), 0) if prevdir else 0
                pref = (dj == 0) if L == TOP else (di == 0)
                ng = g + c + turn + (0 if pref else AGAINST * c)
                if ng < cost.get(nxt, 1e18):
                    cost[nxt] = ng
                    came[nxt] = (cur,)
                    heapq.heappush(openq, (ng + h(ni, nj), ng, nxt, (di, dj)))
            # a via to the other layer
            O = 1 - L
            if not vgrid[L][i][j] and not vgrid[O][i][j]:
                nxt = (O, i, j)
                ng = g + VIA
                if ng < cost.get(nxt, 1e18):
                    cost[nxt] = ng
                    came[nxt] = (cur,)
                    heapq.heappush(openq, (ng + h(i, j), ng, nxt, None))
        return None

    def own(self, net, item, copper=None, hole=None):
        """Record what a route added, so rip_up can take it all back."""
        self.board.Add(item)
        rec = self.owned.setdefault(net, [])
        rec.append((item, copper, hole))
        if copper is not None:
            self.copper.append(copper)
        if hole is not None:
            self.pth_holes.append(hole)     # a via's drill: plated

    def rip_up(self, net):
        """Remove every track and via this net's routes added; returns them for put_back."""
        rec = self.owned.pop(net, [])
        for item, copper, hole in rec:
            self.board.Remove(item)
            # by identity: two entries can be equal geometry
            if copper is not None:
                self.copper = [c for c in self.copper if c is not copper]
            if hole is not None:
                self.pth_holes = [h for h in self.pth_holes if h is not hole]
        return rec

    def put_back(self, net, rec):
        for item, copper, hole in rec:
            self.own(net, item, copper, hole)

    def cost(self, net):
        """What a net's route costs: its length, and its vias at their search cost."""
        c = 0.0
        for item, _, _ in self.owned.get(net, []):
            if isinstance(item, pcbnew.PCB_VIA):
                c += VIA * GRID
            else:
                c += TO(item.GetLength())
        return c

    def commit(self, net, path, width):
        """Write the path as tracks and vias, and add it to the copper others must avoid."""
        netinfo = self.board.FindNet(net)
        pts = [(L, *self.cell_xy(i, j)) for (L, i, j) in path]
        # merge collinear runs on one layer - on the grid's integer cells: in mm,
        # rounding leaves a diagonal staircase of 0.28 mm steps unmerged
        segs, start = [], 0
        for k in range(1, len(pts) + 1):
            if k == len(pts) or pts[k][0] != pts[start][0]:
                run = list(range(start, k))
                keep = [run[0]]
                for m in run[1:-1]:
                    a, b, c = path[keep[-1]], path[m], path[m + 1]
                    if (b[1] - a[1]) * (c[2] - b[2]) - (b[2] - a[2]) * (c[1] - b[1]) != 0:
                        keep.append(m)
                if len(run) > 1:
                    keep.append(run[-1])
                for a, b in zip(keep, keep[1:]):
                    segs.append((pts[a][0], (pts[a][1], pts[a][2]), (pts[b][1], pts[b][2])))
                if k < len(pts):
                    v = pcbnew.PCB_VIA(self.board)
                    v.SetPosition(pcbnew.VECTOR2I(MM(pts[k][1]), MM(pts[k][2])))
                    v.SetWidth(MM(self.via))
                    v.SetDrill(MM(self.via_drill))
                    v.SetNet(netinfo)
                    self.own(net, v, (net, {TOP, BOT}, Point(pts[k][1], pts[k][2]).buffer(self.via / 2), "track"),
                             Point(pts[k][1], pts[k][2]).buffer(self.via_drill / 2))
                start = k
        for L, a, b in segs:
            t = pcbnew.PCB_TRACK(self.board)
            t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
            t.SetWidth(MM(width))
            t.SetLayer(LAYERS[L])
            t.SetNet(netinfo)
            from shapely.geometry import LineString
            g = LineString([a, b]).buffer(width / 2) if a != b else Point(a).buffer(width / 2)
            self.own(net, t, (net, {L}, g, "track"))

    def pad_stub(self, net, pad_geom_, L, cell, width, prev=None):
        """A short track from the pad's centre to the cell the path ended in - inside
        the pad already, so the stub is for the eye, not the connection. Left out
        where it would meet the path's last step at an acute angle: the wedge
        between them is an acid trap the pour cannot fill."""
        c = pad_geom_.centroid
        x, y = self.cell_xy(*cell)
        if math.hypot(c.x - x, c.y - y) < 1e-6:
            return
        if prev is not None:
            px, py = self.cell_xy(*prev)
            if (c.x - x) * (px - x) + (c.y - y) * (py - y) > 0:
                return
        # a pad another route already reaches keeps that stub alone: a second one
        # beside it is overlapping copper, not a connection (the path ends in the pad)
        inner = pad_geom_.buffer(0.01)
        for item, _, _ in self.owned.get(net, []):
            if type(item) is pcbnew.PCB_TRACK and item.GetLayer() == LAYERS[L] and \
                    any(inner.contains(Point(TO(v.x), TO(v.y))) for v in (item.GetStart(), item.GetEnd())):
                return
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(MM(c.x), MM(c.y)))
        t.SetEnd(pcbnew.VECTOR2I(MM(x), MM(y)))
        t.SetWidth(MM(width))
        t.SetLayer(LAYERS[L])
        t.SetNet(self.board.FindNet(net))
        from shapely.geometry import LineString
        self.own(net, t, (net, {L}, LineString([(c.x, c.y), (x, y)]).buffer(width / 2), "track"))

    def route_net(self, net, width, planes=False):
        pads = self.pad_cells(net)
        if len(pads) < 2:
            return True
        grid = self.blocked(net, width)
        vgrid = self.blocked(net, width, via=True)
        for (_, ls, cells, _) in pads:          # a net may always reach its own pads
            for L in ls:
                for (i, j) in cells:
                    grid[L][i][j] = False
        # start from the pad nearest the others' middle
        cx = sum(g.centroid.x for *_, g in pads) / len(pads)
        cy = sum(g.centroid.y for *_, g in pads) / len(pads)
        pads.sort(key=lambda p: math.hypot(p[3].centroid.x - cx, p[3].centroid.y - cy))
        if net in self.prejoined:
            # connect_first already joined some of these pads: they, and the path
            # between them, are the tree's seed, so the tree does not join them twice
            ks, cells0 = self.prejoined[net]
            tree = set(cells0) | {(L, i, j) for (k, ls, cells, _) in pads if k in ks for L in ls for (i, j) in cells}
            todo = [p for p in pads if p[0] not in ks]
            joined = set(ks)
        else:
            tree = {(L, i, j) for L in pads[0][1] for (i, j) in pads[0][2]}
            todo = pads[1:]
            joined = {pads[0][0]}
        self.tree_pads[net] = joined
        while todo:
            targets = {}
            for idx, (_, ls, cells, _) in enumerate(todo):
                for L in ls:
                    for (i, j) in cells:
                        targets[(L, i, j)] = idx
            path = self.astar(tree, set(targets), grid, vgrid)
            if path is None:
                # the tree reaches none of the rest; a net with planes (ground)
                # still wants every pin that can be joined, so it gets them
                return False if not planes else (self.route_rest(net, todo, width, grid, vgrid) and False)
            idx = targets[path[-1]]
            k, ls, cells, g = todo.pop(idx)
            joined.add(k)
            self.commit(net, path, width)
            self.pad_stub(net, g, path[-1][0], path[-1][1:], width, path[-2][1:] if len(path) > 1 else None)
            tree |= set(path) | {(L, i, j) for L in ls for (i, j) in cells}
        return True

    def route_rest(self, net, todo, width, grid, vgrid):
        """Join the pins the tree could not reach to each other, in the groups they
        can reach, so each group has more copper for its stitching via and pour."""
        while len(todo) > 1:
            first = todo.pop(0)
            tree = {(L, i, j) for L in first[1] for (i, j) in first[2]}
            while todo:
                targets = {(L, i, j): idx for idx, (_, ls, cells, _) in enumerate(todo) for L in ls for (i, j) in cells}
                path = self.astar(tree, set(targets), grid, vgrid)
                if path is None:
                    break
                _, ls, cells, g = todo.pop(targets[path[-1]])
                self.commit(net, path, width)
                self.pad_stub(net, g, path[-1][0], path[-1][1:], width, path[-2][1:] if len(path) > 1 else None)
                tree |= set(path) | {(L, i, j) for L in ls for (i, j) in cells}
        return True

    def stub_clear(self, net, L, a, b):
        """A straight stub from a to b on layer L keeps its clearance to every other net."""
        from shapely.geometry import LineString
        g = LineString([a, b]).buffer(self.w / 2 + self.clear)
        return not any(n != net and L in ls and g.intersects(o) for (n, ls, o, _) in self.copper)

    def stitch_gnd(self, gnd):
        """A single-layer GND pad gets a via into the other layer's plane, beside it,
        where the via's stub keeps 90 degrees from every track already on the pad.
        A pad the main ground tree reaches goes without when no such spot exists;
        any other pad takes the via wherever it fits."""
        vgrid = self.blocked(gnd, self.w, via=True)
        n = 0
        on_tree = self.tree_pads.get(gnd, set())
        for (k, ls, cells, g) in self.pad_cells(gnd):
            if len(ls) != 1:
                continue
            c = g.centroid
            L = next(iter(ls))
            # the ways tracks already leave this pad: the via's stub keeps 90 degrees
            # from each, or the two make an acid-trap wedge
            leave = []
            for item, _, _ in self.owned.get(gnd, []):
                if type(item) is pcbnew.PCB_TRACK and item.GetLayer() == LAYERS[L]:
                    ends = [(TO(v.x), TO(v.y)) for v in (item.GetStart(), item.GetEnd())]
                    if any(g.buffer(0.01).contains(Point(*e)) for e in ends):
                        leave += [math.atan2(y - c.y, x - c.x) for x, y in ends if math.hypot(x - c.x, y - c.y) > 0.05]
            best = fallback = None
            for r in range(3, 20):
                for a in range(0, 360, 20):
                    x, y = c.x + r * GRID * math.cos(math.radians(a)), c.y + r * GRID * math.sin(math.radians(a))
                    i, j = round((x - self.x0) / GRID), round((y - self.y0) / GRID)
                    if 0 <= i < self.nx and 0 <= j < self.ny and not vgrid[0][i][j] and not vgrid[1][i][j] \
                            and self.stub_clear(gnd, L, (c.x, c.y), self.cell_xy(i, j)):
                        if all(math.cos(math.radians(a) - t) <= 0 for t in leave):
                            best = (i, j)
                            break
                        fallback = fallback or (i, j)
                if best:
                    break
            # a pad the main ground tree already reaches does not need the via at
            # any angle - it would only add a parallel path; any other pad (an
            # island route_rest joined, or none) takes the via wherever it fits
            best = best or (None if k in on_tree else fallback)
            if not best:
                continue
            self.commit(gnd, [(L, *best), (1 - L, *best)], self.w)
            self.pad_stub(gnd, g, L, best, self.w)
            vgrid = self.blocked(gnd, self.w, via=True)
            n += 1
        return n

    def recopper(self, net, item):
        """Bring a track's entry in self.copper back in line after it was moved."""
        from shapely.geometry import LineString
        rec = self.owned.get(net, [])
        for n, (it, cop, hole) in enumerate(rec):
            if it is item:
                a, b = item.GetStart(), item.GetEnd()
                g = LineString([(TO(a.x), TO(a.y)), (TO(b.x), TO(b.y))]).buffer(TO(item.GetWidth()) / 2) \
                    if (a.x, a.y) != (b.x, b.y) else Point(TO(a.x), TO(a.y)).buffer(TO(item.GetWidth()) / 2)
                new = (net, {LAYERS.index(item.GetLayer())}, g, "track")
                if cop is None:
                    self.copper.append(new)
                else:
                    self.copper = [new if c is cop else c for c in self.copper]
                rec[n] = (it, new, hole)
                return

    def split(self, t, X):
        """Split track t at the point X on it; returns the new second half."""
        end = pcbnew.VECTOR2I(t.GetEnd().x, t.GetEnd().y)
        t2 = pcbnew.PCB_TRACK(self.board)
        t2.SetStart(pcbnew.VECTOR2I(X.x, X.y))
        t2.SetEnd(end)
        t2.SetWidth(t.GetWidth())
        t2.SetLayer(t.GetLayer())
        t2.SetNet(t.GetNet())
        t2.SetLocked(t.IsLocked())
        t.SetEnd(pcbnew.VECTOR2I(X.x, X.y))
        net = t.GetNetname()
        self.own(net, t2, None)
        self.recopper(net, t)
        self.recopper(net, t2)
        return t2

    def square_joins(self):
        """Where two tracks of a net meet on a layer at under 90 degrees - at a bend,
        or where a branch starts in the middle of another track - the wedge between
        them is an acid trap. A branch ending mid-track first splits that track, so
        the join is a vertex like any other. Then the joining track's end moves along
        the other track to the foot of the perpendicular from its far end, and that
        track splits there: the join becomes a right-angle T. Only where the moved
        track keeps its clearance to every other net's copper, off every hole and
        keep-out and inside the edge clearance; a wedge whose apex a via or pad of
        the net fills is left (acute_closed)."""
        from shapely.geometry import LineString
        fixed = 0
        for rnd in range(60):
            changed = False
            # the outer layers' (an inner routing layer's joins are left as routed; check_tracks
            # still tests them)
            tracks = [t for t in self.board.GetTracks() if type(t) is pcbnew.PCB_TRACK and t.GetLayer() in LAYERS]
            # 1. a branch ending in the middle of a track: split the track there
            for t in tracks:
                for e in (t.GetStart(), t.GetEnd()):
                    for u in tracks:
                        if u is t or u.GetNetname() != t.GetNetname() or u.GetLayer() != t.GetLayer() \
                                or is_fixed(u, self.fence):
                            continue
                        a, b = u.GetStart(), u.GetEnd()
                        dx, dy = b.x - a.x, b.y - a.y
                        l2 = dx * dx + dy * dy
                        if not l2:
                            continue
                        k = ((e.x - a.x) * dx + (e.y - a.y) * dy) / l2
                        if 0 < k < 1 and abs((e.x - a.x) * dy - (e.y - a.y) * dx) / math.sqrt(l2) < 1000 \
                                and (e.x, e.y) not in ((a.x, a.y), (b.x, b.y)):
                            self.split(u, pcbnew.VECTOR2I(e.x, e.y))
                            changed = True
                            break
                    if changed:
                        break
                if changed:
                    break
            if changed:
                continue
            # 2. an acute pair at a shared end: square it
            ends = {}
            for t in tracks:
                for e, o in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
                    ends.setdefault((t.GetNetname(), t.GetLayer(), e.x, e.y), []).append((t, pcbnew.VECTOR2I(o.x, o.y)))
            for (net, layer, px, py), vs in ends.items():
                for i in range(len(vs)):
                    for j in range(len(vs)):
                        if i == j:
                            continue
                        (ta, fa), (tb, fb) = vs[i], vs[j]
                        if is_fixed(ta, self.fence) or is_fixed(tb, self.fence):
                            continue            # locked, or outside the run's fence: left as it is
                        ax, ay, bx, by = fa.x - px, fa.y - py, fb.x - px, fb.y - py
                        la, lb = math.hypot(ax, ay), math.hypot(bx, by)
                        if not la or not lb or (ax * bx + ay * by) / (la * lb) <= math.cos(math.radians(89.5)):
                            continue
                        if acute_closed(self.board, net, layer, (px, py), (ax, ay), (bx, by), max(ta.GetWidth(), tb.GetWidth())):
                            continue
                        # the whole of tb turned onto the foot of its far end's perpendicular;
                        # failing that (no room), only its first part: tb split at Q, a fraction
                        # of the way along, and P..Q turned - a short square step, then tb's
                        # own line from Q at an obtuse join
                        if layer not in LAYERS:
                            continue            # an inner routing layer (the module's layer 3): left as routed
                        L = LAYERS.index(layer)
                        found = None
                        for frac in (1.0, 0.5, 0.3, 0.15):
                            Q = pcbnew.VECTOR2I(int(px + frac * bx), int(py + frac * by))
                            k = frac * (ax * bx + ay * by) / (la * la)      # the foot of Q's perpendicular on P->fa
                            if not 0.02 < k < 0.98:
                                continue
                            X = pcbnew.VECTOR2I(int(px + k * ax), int(py + k * ay))
                            if math.hypot(Q.x - X.x, Q.y - X.y) < MM(0.1):
                                continue
                            seg = LineString([(TO(X.x), TO(X.y)), (TO(Q.x), TO(Q.y))])
                            body = seg.buffer(TO(tb.GetWidth()) / 2)
                            g = seg.buffer(TO(tb.GetWidth()) / 2 + self.clear)
                            if any(n != net and L in ls and g.intersects(o) for (n, ls, o, _) in self.copper) \
                                    or any(body.intersects(h) for h in self.holes) or not self.inside.contains(body):
                                continue
                            found = (frac, Q, X)
                            break
                        if not found:
                            continue
                        frac, Q, X = found
                        if frac < 1.0:
                            t2 = self.split(tb, Q)
                            if (tb.GetStart().x, tb.GetStart().y) != (px, py):
                                tb = t2                         # tb ran fb -> P: its P half is the second
                        if (tb.GetStart().x, tb.GetStart().y) == (px, py):
                            tb.SetStart(X)
                        else:
                            tb.SetEnd(X)
                        self.recopper(net, tb)
                        if (ta.GetStart().x, ta.GetStart().y) == (px, py):
                            # ta runs P -> fa: split it at X
                            self.split(ta, X)
                        else:
                            # ta runs fa -> P: its start half is fa -> X
                            t2 = self.split(ta, X)            # ta: fa -> X, t2: X -> P
                        fixed += 1
                        changed = True
                        break
                    if changed:
                        break
                if changed:
                    break
            if not changed:
                return fixed
        print("route: WARNING - square_joins stopped at its pass limit; pcb.py check reports what is left")
        return fixed

    def pour(self, gnd):
        for L in (TOP, BOT):
            z = pcbnew.ZONE(self.board)
            z.SetLayer(LAYERS[L])
            z.SetNet(self.board.FindNet(gnd))
            z.SetLocalClearance(MM(self.clear))
            z.SetMinThickness(MM(0.25))
            # thermal spokes on through-hole pads, which are hand-soldered and
            # need the heat kept in; SMD pads are reflowed and join the pour
            # solid - a spoke there only starves the joint (KiCad's
            # starved_thermal, which a boxed-in SMD ground pin kept tripping)
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
            z.SetThermalReliefGap(MM(0.3))
            z.SetThermalReliefSpokeWidth(MM(0.4))
            ol = z.Outline()
            ol.NewOutline()
            minx, miny, maxx, maxy = self.outline.bounds
            for x, y in list(self.outline.exterior.coords)[:-1]:
                ol.Append(MM(x), MM(y))
            z.SetIsFilled(False)
            self.board.Add(z)


def acute_closed(board, net, layer, p, a, c, width):
    """Whether copper of the net fills the apex of the wedge two tracks leaving p
    along a and c (nm) make: their inner edges meet at (w/2)/sin(theta/2) from p on
    the bisector, and a via or pad of the net covering that point leaves no sharp
    wedge for the etch to pool in (R6-7)."""
    na, nc = math.hypot(*a), math.hypot(*c)
    ux, uy = a[0] / na + c[0] / nc, a[1] / na + c[1] / nc
    nb = math.hypot(ux, uy)
    cos = max(-1.0, min(1.0, (a[0] * c[0] + a[1] * c[1]) / (na * nc)))
    half = math.acos(cos) / 2
    if not nb or half <= 0:
        return False
    if math.sin(half) < 1e-3:
        return True             # the two run out along each other: no wedge, an overlap merge_tracks takes
    d = (width / 2) / math.sin(half)
    m = pcbnew.VECTOR2I(int(p[0] + ux / nb * d), int(p[1] + uy / nb * d))
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == net and \
                math.hypot(t.GetPosition().x - m.x, t.GetPosition().y - m.y) <= t.GetWidth(pcbnew.F_Cu) / 2:
            return True
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == net and pad.IsOnLayer(layer) and pad.HitTest(m):
                return True
    return False


def route(board, lay):
    r = Router(board, lay)
    gnd = lay["ground_net"]
    power = set(lay.get("power_nets", []))
    nets = sorted({n for (n, _, _, _) in r.copper if n and n != gnd and not n.startswith("unconnected")})
    # the power rail first - it visits every network on the board and is the
    # widest track, so it takes the straight way and signals go round it;
    # then the shortest nets: they have the fewest ways round
    def span(n):
        gs = [g for (nn, _, g, _) in r.copper if nn == n]
        xs = [g.centroid.x for g in gs]
        ys = [g.centroid.y for g in gs]
        return (max(xs) - min(xs)) + (max(ys) - min(ys)) if len(gs) > 1 else 0
    # layout.yaml route_first: nets whose pads can be reached from one side only
    # (a 1.27 mm header's far row) go before anything that could close that side
    first = lay.get("route_first", [])
    order = sorted(nets, key=lambda n: (n not in power, n not in first, first.index(n) if n in first else 0, span(n)))
    # layout.yaml connect_first: pad-to-pad connections routed before anything else,
    # the most direct path the board allows - a decoupler's return to its IC's
    # ground pin, which the ground net (routed last, round everything) would not give
    for spec in lay.get("connect_first", []):
        pa, pb = spec["pads"]
        ka, kb = r.pad_at[pa], r.pad_at[pb]
        net = r.copper[ka][0]
        if r.copper[kb][0] != net:
            sys.exit(f"pcb: connect_first {pa} and {pb} are not on one net")
        width = r.pw if net in power else r.w
        pads = {k: (ls, cells, g) for (k, ls, cells, g) in r.pad_cells(net)}
        grid, vgrid = r.blocked(net, width), r.blocked(net, width, via=True)
        for k in (ka, kb):
            for L in pads[k][0]:
                for (i, j) in pads[k][1]:
                    grid[L][i][j] = False
        src = {(L, i, j) for L in pads[ka][0] for (i, j) in pads[ka][1]}
        dst = {(L, i, j) for L in pads[kb][0] for (i, j) in pads[kb][1]}
        path = r.astar(src, dst, grid, vgrid)
        if path is None:
            print(f"route: connect_first {pa} - {pb} FAILED")
            continue
        r.commit(net, path, width)
        r.pad_stub(net, pads[kb][2], path[-1][0], path[-1][1:], width, path[-2][1:] if len(path) > 1 else None)
        r.prejoined[net] = (r.prejoined.get(net, (set(), set()))[0] | {ka, kb}, r.prejoined.get(net, (set(), set()))[1] | set(path))
        print(f"route: connect_first {pa} - {pb} ok")
    failed = []
    for n in order:
        ok = r.route_net(n, r.pw if n in power else r.w)
        print(f"route: {n:20s} {'ok' if ok else 'FAILED'}")
        if not ok:
            failed.append(n)
    # A net that could not route at all: rip up the nets whose tracks cross the
    # box round its pads, route it first and them after, and keep that only if
    # every one of them routes; else put them back as they were.
    for n in list(failed):
        gs = [g for (nn, _, g, k) in r.copper if nn == n and k == "pad"]
        corridor = unary_union(gs).envelope.buffer(1.0)
        blockers = sorted({nn for (nn, ls, g, k) in r.copper
                           if k == "track" and nn not in (n, gnd) and nn in order and g.intersects(corridor)},
                          key=lambda m: (m in power, span(m)))
        r.rip_up(n)
        old = {m: r.rip_up(m) for m in blockers}
        if all(r.route_net(m, r.pw if m in power else r.w) for m in [n] + blockers):
            failed.remove(n)
            print(f"route: {n:20s} ok after ripping up {len(blockers)} net(s)")
        else:
            for m in [n] + blockers:
                r.rip_up(m)
            for m in blockers:
                r.put_back(m, old[m])
    # Rip up and reroute. A net routed early went round an emptier board; a net
    # routed late had to go round the early ones. So for each net that took a
    # real detour (its route much longer than its pads' span), rip up it AND the
    # nets whose tracks cross its corridor, route it first and them after, and
    # keep the result only if the group's total cost fell and nothing failed.
    for rnd in range(3):
        better = 0
        for n in sorted(order, key=lambda n: -(r.cost(n) / max(span(n), 0.5))):
            if n in failed or r.cost(n) <= 1.4 * span(n) + 2:
                continue
            gs = [g for (nn, _, g, k) in r.copper if nn == n and k == "pad"]
            corridor = unary_union(gs).envelope.buffer(1.0)
            blockers = sorted({nn for (nn, ls, g, k) in r.copper
                               if k == "track" and nn not in (n, gnd) and nn in order and g.intersects(corridor)})
            group = [n] + blockers
            before = sum(r.cost(m) for m in group)
            old = {m: r.rip_up(m) for m in group}
            ok = all(r.route_net(m, r.pw if m in power else r.w) for m in group)
            if ok and sum(r.cost(m) for m in group) < before - 0.05:
                better += 1
            else:
                for m in group:
                    r.rip_up(m)
                for m in group:
                    r.put_back(m, old[m])
        print(f"route: rip-up round {rnd + 1}: {better} group(s) improved")
        if not better:
            break
    # Ground is wired as a net too, after everything else, so no ground pin
    # depends on a pour finding its way round the tracks; the pours then add the
    # planes. A pin it cannot reach is left to its stitching via and the pour,
    # and the DRC says whether that was enough.
    ok = r.route_net(gnd, r.w, planes=True)
    print(f"route: {gnd:20s} {'ok' if ok else 'partial - pours and stitching vias must finish it'}")
    vias = r.stitch_gnd(gnd)
    print(f"route: {vias} ground stitching via(s)")
    print(f"route: {r.square_joins()} acute join(s) squared")
    print(f"route: {merge_tracks(board)} collinear joint(s) merged")
    r.pour(gnd)
    return failed


def merge_tracks(board, delete=False, fence=None):
    """Join two tracks of one net and layer that meet head to tail in a straight
    line, so the board is edited in KiCad as runs, not grid steps. Never at a
    via, a third track, or inside a pad: KiCad connects a track to a pad by its
    end, so an end in a pad must stay one."""
    key = lambda v: (round(v.x / 1000), round(v.y / 1000))       # to the micron
    pads = [p for fp in board.GetFootprints() for p in fp.Pads()]
    vias = {key(t.GetPosition()) for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)}
    merged, again = 0, True
    while again:
        again = False
        ends = {}
        tracks = [t for t in board.GetTracks() if type(t) is pcbnew.PCB_TRACK]
        for t in tracks:
            for e in (t.GetStart(), t.GetEnd()):
                ends.setdefault((t.GetNetname(), t.GetLayer(), key(e)), []).append(t)
        for (net, layer, pt), ts in ends.items():
            if len(ts) != 2 or ts[0] is ts[1] or pt in vias or ts[0].GetWidth() != ts[1].GetWidth():
                continue
            if is_fixed(ts[0], fence) or is_fixed(ts[1], fence):
                continue            # locked or outside the fence: never merged away
            a, b = ts
            far = lambda t: t.GetEnd() if key(t.GetStart()) == pt else t.GetStart()
            pa, pb = far(a), far(b)
            p = pcbnew.VECTOR2I(pt[0] * 1000, pt[1] * 1000)
            ux, uy, vx, vy = p.x - pa.x, p.y - pa.y, pb.x - p.x, pb.y - p.y
            if abs(ux * vy - uy * vx) > 1e-3 * math.hypot(ux, uy) * math.hypot(vx, vy) or ux * vx + uy * vy <= 0:
                continue
            if any(q.IsOnLayer(layer) and q.HitTest(p) for q in pads):
                continue
            if any(t is not a and t is not b and t.GetNetname() == net and t.GetLayer() == layer and t.HitTest(p, 1000)
                   for t in tracks):
                continue
            a.SetStart(pa)
            a.SetEnd(pb)
            board.Delete(b) if delete else board.Remove(b)     # Delete on a LOADED board (tidy): Remove corrupts it
            merged += 1
            again = True
            break
    return merged


def fill_zones(path):
    """Fill every zone of a SAVED board, in its own load: filling the board the router
    just built in memory crashes KiCad 9's Python (no connectivity yet), silently."""
    board = pcbnew.LoadBoard(path)
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(path, board)


# ------------------------------------------------------------------ multi-layer boards: planes

class Obstacles:
    """Every piece of copper, hole, keep-out and silkscreen box on a board, indexed, for
    the pieces a multi-layer board's router lays itself before the autorouter: a plane
    net's vias (fanout) and the breath pair (route_pair). In PCB mm; each entry is
    (geometry, net, layers - a set of 'F' / 'B', the outer layers - , kind)."""

    def __init__(self, board, lay):
        self.board, self.lay = board, lay
        r = lay["rules"]
        self.clear, self.via, self.drill = r["clearance"], r["via"], r["via_drill"]
        self.edge = r["edge_clearance"]
        fab = lay.get("fab") or {}
        self.h2h = fab.get("hole_to_hole", 0.25)
        self.hclear = fab.get("hole_clearance", self.clear)
        self.items = []
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if pad.HasHole():
                    c = Point(TO(pad.GetPosition().x), TO(pad.GetPosition().y))
                    self.items.append((c.buffer(TO(pad.GetDrillSize().x) / 2), "", {"F", "B", "I"},
                                       "npth" if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else "hole"))
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    continue
                for L, lid in (("F", pcbnew.F_Cu), ("B", pcbnew.B_Cu), ("I", pcbnew.In2_Cu)):
                    if pad.IsOnLayer(lid) and (L != "I" or pad.HasHole()):
                        self.items.append((pad_geom_on(pad, lid), pad.GetNetname(), {L}, "pad" if pad.HasHole() else "smd"))
        for z in board.Zones():
            if z.GetIsRuleArea() and (z.GetDoNotAllowVias() or z.GetDoNotAllowTracks()):
                ls = {k for k, lid in (("F", pcbnew.F_Cu), ("B", pcbnew.B_Cu), ("I", pcbnew.In2_Cu)) if z.IsOnLayer(lid)}
                for i in range(z.Outline().OutlineCount()):
                    o = z.Outline().Outline(i)
                    self.items.append((Polygon([(TO(o.CPoint(k).x), TO(o.CPoint(k).y)) for k in range(o.PointCount())]),
                                       None, ls, "keepout"))
        # a footprint's own copper shapes - a net tie's bridge - belong to no net
        for fp in board.GetFootprints():
            for g in fp.GraphicalItems():
                for L, lid in (("F", pcbnew.F_Cu), ("B", pcbnew.B_Cu)):
                    if g.GetLayer() == lid:
                        ps = pcbnew.SHAPE_POLY_SET()
                        g.TransformShapeToPolygon(ps, lid, 0, MM(0.005), pcbnew.ERROR_OUTSIDE)
                        import pcb
                        # less the footprint's own pads grown by the clearance (which already holds
                        # every other net off them): a stub or track starts inside its pad
                        own = unary_union([pad_geom_on(p, lid) for p in fp.Pads() if p.IsOnLayer(lid)]).buffer(self.clear)
                        self.items.append((pcb.shapely_of(ps).buffer(self.clear).difference(own), None, {L}, "keepout"))
        silk = [d for d in board.GetDrawings() if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
        for fp in board.GetFootprints():
            silk += [g for g in fp.GraphicalItems() if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
        for it in silk:
            bb = it.GetBoundingBox()
            self.items.append((box(TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom())), None,
                               {"F" if it.GetLayer() == pcbnew.F_SilkS else "B"}, "silk"))
        for t in board.GetTracks():
            self.add_item(t)
        # layout.yaml pairs: `guard:` - every other net's copper kept that much further off
        # the pair's legs than the clearance (a sensitive pair beside clock lines: 3W edge
        # to edge is guard + clearance). The guard is the leg's own net, so its own copper
        # passes; it holds only what this router lays, not a hand edit (KiCad's DRC keeps
        # the plain clearance)
        # (the pair's own tracks: locked and of the pair's width - a plane net's fanout stub is
        # locked too, but wider)
        guards = {n: (float(pr["guard"]), float(pr["width"])) for pr in lay.get("pairs") or [] if pr.get("guard") for n in pr["nets"]}
        for t in board.GetTracks():
            if type(t) in (pcbnew.PCB_TRACK, pcbnew.PCB_ARC) and t.IsLocked() and t.GetNetname() in guards \
                    and t.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu) and abs(TO(t.GetWidth()) - guards[t.GetNetname()][1]) < 1e-3:
                a, b = t.GetStart(), t.GetEnd()
                if (a.x, a.y) == (b.x, b.y):
                    continue
                g = track_line(t).buffer(TO(t.GetWidth()) / 2 + guards[t.GetNetname()][0], 8)
                self.items.append((g, t.GetNetname(), {"F" if t.GetLayer() == pcbnew.F_Cu else "B"}, "guard"))
        self.outline = board_outline_with_holes(board)
        from shapely.prepared import prep
        self.inner = prep(self.outline.buffer(-self.edge))
        self._tree = None
        self._via_inner = None

    def add(self, geom, net, layers, kind):
        self.items.append((geom, net, layers, kind))
        self._tree = None

    def add_item(self, t):
        """A track or via already on the board, as an obstacle."""
        if isinstance(t, pcbnew.PCB_VIA):
            c = Point(TO(t.GetPosition().x), TO(t.GetPosition().y))
            self.add(c.buffer(TO(t.GetWidth(pcbnew.F_Cu)) / 2, 16), t.GetNetname(), {"F", "B", "I"}, "via")
            self.add(c.buffer(TO(t.GetDrillValue()) / 2, 16), t.GetNetname(), {"F", "B", "I"}, "vhole")
        else:
            # an inner layer's track (a board that routes layer 3) is an obstacle to vias only;
            # an arc by its own curve, not its chord
            g = track_line(t).buffer(TO(t.GetWidth()) / 2, 8)
            self.add(g, t.GetNetname(), {{pcbnew.F_Cu: "F", pcbnew.B_Cu: "B"}.get(t.GetLayer(), "I")}, "track")

    def near(self, g, pad=1.0):
        from shapely.strtree import STRtree
        if self._tree is None:
            self._tree = STRtree([it[0] for it in self.items])
        return [self.items[i] for i in self._tree.query(g.buffer(pad))]

    def within(self, p, d):
        """The entries whose geometry comes within d of p: one indexed query, exact."""
        from shapely.strtree import STRtree
        if self._tree is None:
            self._tree = STRtree([it[0] for it in self.items])
        return [self.items[i] for i in self._tree.query(p, predicate="dwithin", distance=d)]

    def via_ok(self, x, y, net):
        """A via of `net` at (x, y): its copper clear of every other net by the clearance,
        off every SMD pad (its own net's too: a via in a pad wicks its solder), its hole
        the board house's hole-to-hole from every other, off silkscreen and keep-outs,
        and inside the board by the edge clearance."""
        p = Point(x, y)
        if self._via_inner is None:
            from shapely.prepared import prep
            self._via_inner = prep(self.outline.buffer(-(self.edge + self.via / 2)))
        if not self._via_inner.contains(p):
            return False
        rv, rd = self.via / 2, self.drill / 2
        reach = max(rd + max(self.h2h, self.clear), rv + max(self.clear, self.hclear, OWN_PAD_GAP))
        for g, n, ls, kind in self.within(p, reach):
            d = g.distance(p)
            if kind in ("hole", "vhole", "npth"):
                gap = self.h2h if kind != "vhole" else max(self.h2h, self.clear)
                if d < rd + gap - 1e-6 or (kind == "npth" and d < rv + self.hclear):
                    return False
            elif kind in ("keepout", "silk"):
                if d < rv:
                    return False
            elif kind == "smd" and n == net:
                if d < rv + OWN_PAD_GAP:
                    return False
            elif n != net and d < rv + self.clear - 1e-6:
                return False
        return True

    def track_ok(self, a, b, width, net, layer):
        """A straight track a -> b on layer ('F' / 'B') clear of every other net's copper,
        off keep-outs and unplated holes, inside the board by the edge clearance."""
        g = LineString([a, b]).buffer(width / 2, 8) if a != b else Point(a).buffer(width / 2)
        if not self.inner.contains(g):
            return False
        for og, n, ls, kind in self.near(g):
            if layer not in ls or kind in ("silk", "hole", "vhole"):
                continue
            if kind == "npth":
                if og.distance(g) < self.hclear:
                    return False
            elif kind == "keepout":
                if og.intersects(g):
                    return False
            elif n != net and og.distance(g) < self.clear - 1e-6:
                return False
        return True


def pad_geom_on(pad, layer):
    poly = pad.GetEffectivePolygon(layer)
    pts = []
    for i in range(poly.OutlineCount()):
        ol = poly.Outline(i)
        pts.append(Polygon([(TO(ol.CPoint(j).x), TO(ol.CPoint(j).y)) for j in range(ol.PointCount())]))
    return unary_union(pts)


def board_outline_with_holes(board):
    """The board's Edge.Cuts as one shapely polygon, its inner cut-outs (a routed hole,
    a slot) as holes."""
    ol = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(ol):
        raise SystemExit("route: the Edge.Cuts outline is not closed")
    ring = lambda c: [(TO(c.CPoint(k).x), TO(c.CPoint(k).y)) for k in range(c.PointCount())]
    return unary_union([Polygon(ring(ol.Outline(i)), [ring(ol.Hole(i, h)) for h in range(ol.HoleCount(i))])
                        for i in range(ol.OutlineCount())])


def plane_regions(board, lay):
    """net -> where that net's plane copper is, in PCB mm: a plane's layer less each
    island's moat on it, and each island. A via for the net must stand inside."""
    import pcb
    out = {}
    outline = board_outline_with_holes(board)
    isl = []
    for spec in lay.get("islands") or []:
        p = Polygon([pcb.to_pcb(x, y) for x, y in spec["outline"]]).intersection(outline)
        isl.append((spec, p, p.buffer(spec["moat"], join_style=2)))
    for pl in lay.get("planes") or []:
        reg = outline
        for spec, p, moat in isl:
            if spec["layer"] == pl["layer"]:
                reg = reg.difference(moat)
        out[pl["net"]] = unary_union([out[pl["net"]], reg]) if pl["net"] in out else reg
    for spec, p, moat in isl:
        out[spec["net"]] = unary_union([out[spec["net"]], p]) if spec["net"] in out and any(
            s_["net"] == spec["net"] and s_ is not spec for s_, _, _ in isl) else p
    # an outer-layer pour (the module's isolated return on the rear face): a via into it
    for po in lay.get("pours") or []:
        p = outline if po["outline"] == "board" else Polygon([pcb.to_pcb(x, y) for x, y in po["outline"]]).intersection(outline)
        out[po["net"]] = unary_union([out[po["net"]], p]) if po["net"] in out else p
    return out


def lay_via(board, obs, net, x, y, locked=True):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(obs.via))
    v.SetDrill(MM(obs.drill))
    v.SetNet(board.FindNet(net))
    v.SetLocked(locked)
    board.Add(v)
    obs.add_item(v)
    return v


def lay_track(board, obs, net, a, b, width, layer, locked=True):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(width))
    t.SetLayer({"F": pcbnew.F_Cu, "B": pcbnew.B_Cu, "I": pcbnew.In2_Cu}[layer])
    t.SetNet(board.FindNet(net))
    t.SetLocked(locked)
    board.Add(t)
    obs.add_item(t)
    return t


def fanout(board, lay, obs, only=None):
    """Every SMD pad on a plane net (layout.yaml fanout:) gets its own via into that
    plane, on a short straight stub from the pad's centre: the nearest spot, searching
    away from the part first, where the via is legal (Obstacles.via_ok), inside its
    plane's region by the via's radius and a margin, and the stub clear of every other
    net. A through-hole pad meets the plane itself. A pad in its island's `off_island:`
    is left to the route that serves it (the pair). Both are LOCKED, so the autorouter
    keeps them. Returns the pads no via fits by."""
    regions = plane_regions(board, lay)
    width = (lay.get("net_classes") or {}).get("plane_nets", {}).get("track", lay["rules"]["track"])
    skip = {p for spec in lay.get("islands") or [] for p in spec.get("off_island", [])}
    missed, n = [], 0
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        for pad in sorted(fp.Pads(), key=lambda p: p.GetNumber()):
            net = pad.GetNetname()
            name = f"{fp.GetReference()}.{pad.GetNumber()}"
            through = name in (lay.get("fanout_through") or []) or (only is not None and name in only and pad.HasHole())
            if only is not None and name not in only:
                continue
            if net not in (lay.get("fanout") or []) or (pad.HasHole() and not through) or name in skip:
                continue
            if not through and any(q.HasHole() and q.GetNumber() == pad.GetNumber() for q in fp.Pads()):
                continue            # a plated hole's face pad (a mount's): the hole meets the plane
            L = "F" if pad.IsOnLayer(pcbnew.F_Cu) else "B"
            pg = pad_geom_on(pad, pcbnew.F_Cu if L == "F" else pcbnew.B_Cu)
            c = pg.centroid
            region = regions[net].buffer(-(obs.via / 2 + 0.3))
            if only is not None:
                # an orphan's via goes on the body of its plane's fill, not on its fragment
                import pcb
                for z in board.Zones():
                    if not z.GetIsRuleArea() and z.IsFilled() and z.GetNetname() == net:
                        fill = pcb.shapely_of(z.GetFilledPolysList(z.GetLayer()))
                        body = max(getattr(fill, "geoms", [fill]), key=lambda g: g.area)
                        region = region.intersection(body.buffer(-(obs.via / 2 + 0.3)))
            fc = Point(TO(fp.GetPosition().x), TO(fp.GetPosition().y))
            away = math.atan2(c.y - fc.y, c.x - fc.x) if fc.distance(c) > 0.05 else 0.0
            # layout.yaml fanout_count: a power pad's plane transition by more than one via
            # (each its own stub, the next nearest legal spot): current and inductance shared
            want = int((lay.get("fanout_count") or {}).get(name, 1))
            for _ in range(want):
                found = None
                for k in range(3, 41):
                    r = k * 0.1
                    for da in range(0, 181, 15):
                        for sgn in ((1,) if da in (0, 180) else (1, -1)):
                            a = away + sgn * math.radians(da)
                            x, y = c.x + r * math.cos(a), c.y + r * math.sin(a)
                            p = Point(x, y)
                            if pg.buffer(obs.via / 2 + OWN_PAD_GAP).contains(p) or not region.contains(p):
                                continue
                            if obs.via_ok(x, y, net) and obs.track_ok((c.x, c.y), (x, y), width, net, L):
                                found = (x, y)
                                break
                        if found:
                            break
                    if found:
                        break
                if not found:
                    missed.append(f"{name} ({net}): no legal via within 4 mm")
                    break
                lay_via(board, obs, net, *found)
                lay_track(board, obs, net, (c.x, c.y), found, width, L)
                n += 1
    print(f"route: fanout - {n} plane via(s); {len(missed)} pad(s) without one")
    for m in missed:
        print("  fanout: " + m)
    return missed


class Grid:
    """A lazy routing grid on one outer layer for one kind of track: a cell is free when
    a track of half-width `half` centred there keeps the clearance to every obstacle on
    the layer except copper of the nets in `own`, and stays inside the edge clearance.
    Cells are tested as the search reaches them (the board is 300 mm long; a whole grid
    of shapely tests is minutes, a search's worth is seconds)."""

    def __init__(self, obs, layer, half, own=()):
        from shapely.prepared import prep
        self.obs, self.L, self.own = obs, layer, set(own)
        self.rad = half + obs.clear + SLACK
        self.x0, self.y0 = obs.outline.bounds[:2]
        self.inner = prep(obs.outline.buffer(-(obs.edge + half + SLACK)))
        self.cache = {}

    def xy(self, c):
        return (self.x0 + c[0] * GRID, self.y0 + c[1] * GRID)

    def cell(self, x, y):
        return (round((x - self.x0) / GRID), round((y - self.y0) / GRID))

    def free(self, i, j):
        if (i, j) not in self.cache:
            p = Point(*self.xy((i, j)))
            ok = self.inner.contains(p)
            if ok:
                for g, n, ls, kind in self.obs.within(p, self.rad - 1e-4):
                    if self.L not in ls or kind in ("silk", "hole", "vhole") or (n in self.own and kind != "keepout"):
                        continue
                    ok = False
                    break
            self.cache[(i, j)] = ok
        return self.cache[(i, j)]

    def astar(self, starts, goals, gxy):
        """starts {cell: cost}; goals a set of cells; gxy the goal's point (the heuristic).
        8-connected, no corner cutting, turns costed as pcb_route's own router."""
        ti, tj = (gxy[0] - self.x0) / GRID, (gxy[1] - self.y0) / GRID
        h = lambda i, j: math.hypot(i - ti, j - tj)
        moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, DIAG), (1, -1, DIAG), (-1, 1, DIAG), (-1, -1, DIAG)]
        openq, came, cost, seen = [], {}, {}, set()
        for c, c0 in starts.items():
            cost[c] = c0
            heapq.heappush(openq, (c0 + h(*c), c0, c, None))
        free = self.free
        while openq:
            f, g, cur, pd = heapq.heappop(openq)
            if cur in seen:
                continue
            seen.add(cur)
            if cur in goals:
                path = [cur]
                while path[-1] in came:
                    path.append(came[path[-1]])
                return path[::-1]
            if len(seen) > 400000:
                return None
            for di, dj, c in moves:
                nxt = (cur[0] + di, cur[1] + dj)
                if nxt in seen or not free(*nxt) or (di and dj and not (free(cur[0] + di, cur[1]) and free(cur[0], cur[1] + dj))):
                    continue
                ng = g + c + (TURN.get(steps45(pd, (di, dj)), 0) if pd else 0)
                if ng < cost.get(nxt, 1e18):
                    cost[nxt], came[nxt] = ng, cur
                    heapq.heappush(openq, (ng + h(*nxt), ng, nxt, (di, dj)))
        return None


def corners(path):
    """A grid path's cells where its direction changes, and its two ends."""
    if len(path) < 3:
        return list(path)
    return [path[0]] + [path[k] for k in range(1, len(path) - 1)
                        if (path[k][0] - path[k - 1][0], path[k][1] - path[k - 1][1]) != (path[k + 1][0] - path[k][0], path[k + 1][1] - path[k][1])] + [path[-1]]


def route_pair(board, lay, obs, spec):
    """Two nets side by side on one layer (layout.yaml pairs:) - a sensor's signal and
    its reference taken at the sensor. The coupled run starts at the first of `through:`
    (body mm: past the crowded corner the pads are in) and ends beside the `to` pads; it
    is routed as ONE fat track - two widths and their gap - by A* on the 0.2 mm grid
    through each `through:` point, and its two legs are that centreline offset each way
    by half a width and half the gap. Each leg then reaches its own pad at each end by
    a single track of its net (A* again, the other leg an obstacle), so the reference
    leg really starts at the sensor's pin. Locked, so the autorouter keeps them.
    Returns what it could not do."""
    import pcb
    if spec.get("detours") is not None:
        return route_pair_smooth(board, lay, obs, spec)
    nets, w, gap, L = spec["nets"], spec["width"], spec["gap"], {"F.Cu": "F", "B.Cu": "B"}[spec["layer"]]
    lid = pcbnew.F_Cu if L == "F" else pcbnew.B_Cu
    pads = {}
    for p in spec["from"] + spec["to"]:
        ref, num = p.split(".")
        pad = board.FindFootprintByReference(ref).FindPadByNumber(num)
        pads[p] = pad_geom_on(pad, lid)
    fat = Grid(obs, L, w + gap / 2)
    stops = [pcb.to_pcb(*p) for p in spec.get("through", [])]
    if not stops:
        return [f"pair {nets}: give it a through: point to start the coupled run at"]
    tx = sum(pads[p].centroid.x for p in spec["to"]) / 2
    ty = sum(pads[p].centroid.y for p in spec["to"]) / 2
    c0 = fat.cell(*stops[0])
    if not fat.free(*c0):
        return [f"pair {nets}: its first through: point is not free for the pair"]
    # the far end: the free cells within 5 mm of the `to` pads' midpoint
    ci, cj = fat.cell(tx, ty)
    dst = {(ci + di, cj + dj) for di in range(-25, 26) for dj in range(-25, 26)
           if di * di + dj * dj <= 625 and fat.free(ci + di, cj + dj)}
    path, starts = [c0], {c0: 0}
    for k, stop in enumerate(stops[1:] + [(tx, ty)]):
        if k < len(stops) - 1:
            gi, gj = fat.cell(*stop)
            goals = {(gi + a, gj + b) for a in range(-2, 3) for b in range(-2, 3) if fat.free(gi + a, gj + b)}
        else:
            goals = dst
        seg = fat.astar(starts, goals, stop) if goals else None
        if seg is None:
            return [f"pair {nets}: no way through for the pair on {spec['layer']} (to through: point {k + 2})"
                    if k < len(stops) - 1 else f"pair {nets}: no way to its far end on {spec['layer']}"]
        path += seg[1:]
        starts = {path[-1]: 0}
    centre = LineString([fat.xy(c) for c in corners(path)])
    legs = [centre.offset_curve(s * (w + gap) / 2, join_style=2, mitre_limit=2.0) for s in (1, -1)]
    # which leg is which net: the one whose ends lie nearer that net's pads
    ends = lambda leg: (Point(leg.coords[0]), Point(leg.coords[-1]))
    want = [pads[spec["from"][0]].centroid, pads[spec["to"][0]].centroid, pads[spec["from"][1]].centroid, pads[spec["to"][1]].centroid]
    d = lambda a, b: sum(p.distance(q) for p, q in zip(ends(a) + ends(b), want))
    if d(legs[1], legs[0]) < d(legs[0], legs[1]):
        legs = legs[::-1]
    for leg, net in zip(legs, nets):
        pts = list(leg.coords)
        for a, b in zip(pts, pts[1:]):
            lay_track(board, obs, net, a, b, w, L)
    # each leg's end to its own pad: a single track of the leg's net
    report = []
    for leg, net, pf, pt in zip(legs, nets, spec["from"], spec["to"]):
        pts = list(leg.coords)
        for end, pname in ((pts[0], pf), (pts[-1], pt)):
            g = Grid(obs, L, w / 2, own={net})
            pad_obj = board.FindFootprintByReference(pname.split(".")[0]).FindPadByNumber(pname.split(".")[1])
            if not pad_obj.IsOnLayer(lid):
                # a pad on the other face (an SMD part on layer 1 for a layer-4 pair): the
                # autorouter joins the leg's end to it, by a via (a track under the pad would
                # only dangle)
                report.append(f"pair {net}: {pname} is on the other face - its via left to the autorouter")
                continue
            pg = pads[pname].buffer(-0.05)
            bx0, by0, bx1, by1 = pads[pname].bounds
            goals = {(i, j) for i in range(g.cell(bx0, by0)[0], g.cell(bx1, by1)[0] + 1)
                     for j in range(g.cell(bx0, by0)[1], g.cell(bx1, by1)[1] + 1) if pg.contains(Point(*g.xy((i, j))))}
            s0 = g.cell(*end)
            seg = g.astar({s0: 0}, goals, (pads[pname].centroid.x, pads[pname].centroid.y)) if goals else None
            if seg is None:
                report.append(f"pair {net}: no way from the pair's end to {pname} - left to the autorouter")
                continue
            pts2 = [end] + [g.xy(c) for c in corners(seg)[1:]]
            for a, b in zip(pts2, pts2[1:]):
                if math.dist(a, b) > 1e-3:
                    lay_track(board, obs, net, a, b, w, L)
    print(f"route: pair {' / '.join(nets)} - {centre.length:.1f} mm side by side on {spec['layer']}")
    if spec.get("guard_traces"):
        report += guard_traces(board, lay, obs, spec, centre, L, lid)
    return report


def guard_traces(board, lay, obs, spec, centre, L, lid):
    """layout.yaml pairs: `guard_traces: {net, every}` - a ground track each side of the
    coupled run, one clearance off its legs, stitched by a via into its net's island or
    strip at least every `every` mm. Laid where it fits: a piece that would come within the
    clearance of another net's copper (a pad, a keep-out, the board's edge) is left out,
    and a run with no room for a single stitching via is dropped, never left floating.
    Locked, so the autorouter keeps them. Returns the spans left without a guard."""
    gnet, every = spec["guard_traces"]["net"], float(spec["guard_traces"].get("every", 5.0))
    w, gap = spec["width"], spec["gap"]
    gw = w
    off = (w + gap) / 2 + w / 2 + obs.clear + gw / 2
    voff = (w + gap) / 2 + w / 2 + obs.clear + obs.via / 2 + 0.02
    region = plane_regions(board, lay).get(gnet)
    mine = {gnet}
    step = 0.4
    out, laid, vias = [], 0.0, 0

    def clear_of_others(g):
        for geom, n, ls, kind in obs.near(g, 0.5):
            if L not in ls or kind in ("silk", "guard") or n in mine:
                continue
            if geom.distance(g) < obs.clear - 1e-3:
                return False
        return obs.inner.contains(g)
    for side in (1, -1):
        line = centre.offset_curve(side * off, join_style=2, mitre_limit=2.0)
        vline = centre.offset_curve(side * voff, join_style=2, mitre_limit=2.0)
        n = max(1, int(line.length / step))
        keep = []
        for i in range(n):
            a, b = line.interpolate(i * line.length / n), line.interpolate((i + 1) * line.length / n)
            keep.append(clear_of_others(LineString([a, b]).buffer(gw / 2, cap_style=1)))
        runs, cur = [], None
        for i, k in enumerate(keep):
            if k and cur is None:
                cur = i
            if not k and cur is not None:
                runs.append((cur, i))
                cur = None
        if cur is not None:
            runs.append((cur, n))
        for i0, i1 in runs:
            d0, d1 = i0 * line.length / n, i1 * line.length / n
            if d1 - d0 < 1.0:
                continue
            got, d = [], d0 + 0.5
            while d <= d1 - 0.5:
                q = vline.interpolate(d / line.length * vline.length)
                if (region is None or region.contains(q)) and obs.via_ok(q.x, q.y, gnet):
                    got.append((d, q))
                    d += every
                else:
                    d += 0.4
            if len(got) < 2:
                a_, b_ = line.interpolate(d0), line.interpolate(d1)
                out.append(f"guard {gnet}: {d1 - d0:.1f} mm beside the pair, ({a_.x:.1f}, {a_.y:.1f}) to ({b_.x:.1f}, {b_.y:.1f}), "
                           f"with no room for two stitching vias - left out")
                continue
            # the run from its first via to its last: no end of it left hanging
            d0, d1 = got[0][0], got[-1][0]
            ds = [d0] + [x for x in (line.project(Point(c)) for c in line.coords) if d0 < x < d1] + [d1]
            pts = [line.interpolate(x) for x in sorted(ds)]
            for a, b in zip(pts, pts[1:]):
                if a.distance(b) > 1e-3:
                    lay_track(board, obs, gnet, (a.x, a.y), (b.x, b.y), gw, L)
            for d_, q in got:
                lay_via(board, obs, gnet, q.x, q.y)
                g_ = line.interpolate(d_)
                lay_track(board, obs, gnet, (g_.x, g_.y), (q.x, q.y), gw, L)
                vias += 1
            laid += d1 - d0
    print(f"route: pair {' / '.join(spec['nets'])} - guard {gnet} {laid:.1f} mm, {vias} stitching via(s)")
    return out


# ------------------------------------------------------------------ smooth paths (arcs)
# A pair laid along a drawn centreline (layout.yaml pairs: `detours:`), not the grid:
# straight runs between its `through:` points, every corner a fillet arc of `fillet:` mm,
# and round each detour's mount a concentric arc of radius r, entered and left by two
# fillets mirrored about the mount's centre line - so every leg and guard is the same
# shape offset: lines and concentric arcs, one spacing all the way (owner, 2026-10-04:
# "curve around standoffs much better and be mirrored around them").

class Prim:
    """A line (kind 'L': p0 -> p1) or an arc (kind 'A': centre, radius, start angle a0,
    signed sweep), both in PCB mm; point(t) for t in [0, 1]."""
    def __init__(self, kind, **k):
        self.kind = kind
        self.__dict__.update(k)

    def point(self, t):
        if self.kind == "L":
            return (self.p0[0] + (self.p1[0] - self.p0[0]) * t, self.p0[1] + (self.p1[1] - self.p0[1]) * t)
        a = self.a0 + self.sweep * t
        return (self.c[0] + self.r * math.cos(a), self.c[1] + self.r * math.sin(a))

    def tangent(self, t):
        if self.kind == "L":
            dx, dy = self.p1[0] - self.p0[0], self.p1[1] - self.p0[1]
        else:
            a = self.a0 + self.sweep * t
            s = 1 if self.sweep > 0 else -1
            dx, dy = -math.sin(a) * s, math.cos(a) * s
        n = math.hypot(dx, dy)
        return (dx / n, dy / n)

    def length(self):
        if self.kind == "L":
            return math.dist(self.p0, self.p1)
        return abs(self.sweep) * self.r

    def offset(self, d):
        """The same primitive d mm to the left of travel (a concentric arc, a parallel line)."""
        if self.kind == "L":
            tx, ty = self.tangent(0)
            nx, ny = -ty, tx
            return Prim("L", p0=(self.p0[0] + d * nx, self.p0[1] + d * ny), p1=(self.p1[0] + d * nx, self.p1[1] + d * ny))
        # left of travel is toward the centre on a left turn (sweep > 0)
        r = self.r - d if self.sweep > 0 else self.r + d
        return Prim("A", c=self.c, r=r, a0=self.a0, sweep=self.sweep)

    def piece(self, t0, t1):
        if self.kind == "L":
            return Prim("L", p0=self.point(t0), p1=self.point(t1))
        return Prim("A", c=self.c, r=self.r, a0=self.a0 + self.sweep * t0, sweep=self.sweep * (t1 - t0))

    def line(self, n=24):
        return LineString([self.point(i / n) for i in range(n + 1)] if self.kind == "A" else [self.p0, self.p1])


def _unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n)


def _arc_between(c, r, p, q, sign, through=None):
    """The arc round c from p to q turning `sign` (+1 left, -1 right); the short way unless
    `through` (a direction) says which way round."""
    a0 = math.atan2(p[1] - c[1], p[0] - c[0])
    a1 = math.atan2(q[1] - c[1], q[0] - c[0])
    sw = a1 - a0
    if sign > 0:
        while sw <= 0:
            sw += 2 * math.pi
    else:
        while sw >= 0:
            sw -= 2 * math.pi
    return Prim("A", c=c, r=r, a0=a0, sweep=sw)


def smooth_path(points, detours, fillet, fillet_mid=1.5):
    """The centreline through `points` (PCB mm), every corner filleted, and round each
    detour (centre, r) where a straight run passes it: [Prim]."""
    segs, prims = [], []
    pts = [tuple(p) for p in points]
    # corners: each vertex's fillet, and how far it eats into the runs either side
    cut_in, cut_out, fil = [0.0] * len(pts), [0.0] * len(pts), [None] * len(pts)
    for i in range(1, len(pts) - 1):
        u1, u2 = _unit((pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])), _unit((pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
        th = math.atan2(u1[0] * u2[1] - u1[1] * u2[0], u1[0] * u2[0] + u1[1] * u2[1])
        if abs(th) < 1e-6:
            continue
        L = fillet * math.tan(abs(th) / 2)
        s = (pts[i][0] - u1[0] * L, pts[i][1] - u1[1] * L)
        e = (pts[i][0] + u2[0] * L, pts[i][1] + u2[1] * L)
        sg = 1 if th > 0 else -1
        c = (s[0] - u1[1] * fillet * sg, s[1] + u1[0] * fillet * sg)
        fil[i] = _arc_between(c, fillet, s, e, sg)
        cut_in[i], cut_out[i] = L, L
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        u = _unit((b[0] - a[0], b[1] - a[1]))
        a2 = (a[0] + u[0] * cut_out[i], a[1] + u[1] * cut_out[i])
        b2 = (b[0] - u[0] * cut_in[i + 1], b[1] - u[1] * cut_in[i + 1])
        nl = (-u[1], u[0])
        here = []
        for chain in detours:
            c, rc = chain[0]
            s_ = (c[0] - a2[0]) * u[0] + (c[1] - a2[1]) * u[1]
            h = (c[0] - a2[0]) * nl[0] + (c[1] - a2[1]) * nl[1]
            if abs(h) < rc and 0 < s_ < math.dist(a2, b2):
                here.append((s_, chain, h))
        cur = a2
        for s_, chain, h in sorted(here, key=lambda e: e[0]):
            sg = 1 if h > 0 else -1               # the mount's side; the path passes beyond it
            nb = (nl[0] * sg, nl[1] * sg)
            loc = lambda q: ((q[0] - a2[0]) * u[0] + (q[1] - a2[1]) * u[1], abs((q[0] - a2[0]) * nl[0] + (q[1] - a2[1]) * nl[1]))
            # in: a fillet from the run onto the first circle
            (c0, r0), (cl, rl) = chain[0], chain[-1]
            s0, hd0 = loc(c0)
            sl, hdl = loc(cl)
            dx0 = math.sqrt((fillet + r0) ** 2 - (fillet - hd0) ** 2)
            dxl = math.sqrt((fillet + rl) ** 2 - (fillet - hdl) ** 2)
            p1 = (a2[0] + u[0] * (s0 - dx0), a2[1] + u[1] * (s0 - dx0))
            p2 = (a2[0] + u[0] * (sl + dxl), a2[1] + u[1] * (sl + dxl))
            f1 = (p1[0] + nb[0] * fillet, p1[1] + nb[1] * fillet)
            f2 = (p2[0] + nb[0] * fillet, p2[1] + nb[1] * fillet)
            v1, v2 = _unit((c0[0] - f1[0], c0[1] - f1[1])), _unit((cl[0] - f2[0], cl[1] - f2[1]))
            t1 = (f1[0] + v1[0] * fillet, f1[1] + v1[1] * fillet)
            t2 = (f2[0] + v2[0] * fillet, f2[1] + v2[1] * fillet)
            prims.append(Prim("L", p0=cur, p1=p1))
            prims.append(_arc_between(f1, fillet, p1, t1, sg))
            at = t1
            # round each circle in turn, from one to the next along their common tangent on
            # the far side of both - one smooth sweep, never back up between them
            for k in range(len(chain) - 1):
                (ca, ra), (cb, rb) = chain[k], chain[k + 1]
                d = math.dist(ca, cb)
                e = _unit((cb[0] - ca[0], cb[1] - ca[1]))
                pp = (e[1], -e[0]) if e[1] * nb[0] - e[0] * nb[1] > 0 else (-e[1], e[0])
                if pp[0] * nb[0] + pp[1] * nb[1] < 0:
                    pp = (-pp[0], -pp[1])
                k_ = (ra - rb) / d
                q_ = math.sqrt(max(1 - k_ * k_, 0.0))
                m = (e[0] * k_ + pp[0] * q_, e[1] * k_ + pp[1] * q_)
                ta = (ca[0] + m[0] * ra, ca[1] + m[1] * ra)
                tb = (cb[0] + m[0] * rb, cb[1] + m[1] * rb)
                prims.append(_arc_between(ca, ra, at, ta, -sg))
                prims.append(Prim("L", p0=ta, p1=tb))
                at = tb
            prims.append(_arc_between(cl, rl, at, t2, -sg))
            prims.append(_arc_between(f2, fillet, t2, p2, sg))
            cur = p2
        prims.append(Prim("L", p0=cur, p1=b2))
        if i + 1 < len(pts) - 1 and fil[i + 1] is not None:
            prims.append(fil[i + 1])
    return [p for p in prims if p.length() > 1e-4]


def lay_prim(board, obs, net, p, width, layer, locked=True):
    """A Prim as copper: a track, or a KiCad arc (start, mid, end)."""
    if p.kind == "L":
        return lay_track(board, obs, net, p.p0, p.p1, width, layer, locked)
    a = pcbnew.PCB_ARC(board)
    a.SetStart(pcbnew.VECTOR2I(MM(p.point(0)[0]), MM(p.point(0)[1])))
    a.SetMid(pcbnew.VECTOR2I(MM(p.point(0.5)[0]), MM(p.point(0.5)[1])))
    a.SetEnd(pcbnew.VECTOR2I(MM(p.point(1)[0]), MM(p.point(1)[1])))
    a.SetWidth(MM(width))
    a.SetLayer({"F": pcbnew.F_Cu, "B": pcbnew.B_Cu, "I": pcbnew.In2_Cu}[layer])
    a.SetNet(board.FindNet(net))
    a.SetLocked(locked)
    board.Add(a)
    obs.add_item(a)
    return a


def route_pair_smooth(board, lay, obs, spec):
    """route_pair for a pair with `detours:` - its centreline drawn, not searched."""
    import pcb
    nets, w, gap, L = spec["nets"], spec["width"], spec["gap"], {"F.Cu": "F", "B.Cu": "B"}[spec["layer"]]
    pts = [pcb.to_pcb(*p) for p in spec["through"]]
    # each detour a chain: its mount, then any circle it must also pass round (`then:`)
    dets = [[(pcb.to_pcb(*d["at"]), float(d["r"]))] + [(pcb.to_pcb(*t["at"]), float(t["r"])) for t in d.get("then") or []]
            for d in spec["detours"]]
    prims = smooth_path(pts, dets, float(spec.get("fillet", 3.0)), float(spec.get("fillet_mid", 1.5)))
    half = (w + gap) / 2
    # which side is which net: the leg whose start lies nearer that net's `from` pad
    pf = {}
    for p_ in spec["from"]:
        ref, num = p_.split(".")
        q = board.FindFootprintByReference(ref).FindPadByNumber(num).GetPosition()
        pf[p_] = (TO(q.x), TO(q.y))
    st = prims[0].point(0)
    t = prims[0].tangent(0)
    left = (st[0] - t[1] * half, st[1] + t[0] * half)
    d_left = math.dist(left, pf[spec["from"][0]]) + 0.0
    right = (st[0] + t[1] * half, st[1] - t[0] * half)
    sides = (half, -half) if d_left <= math.dist(right, pf[spec["from"][0]]) else (-half, half)
    # a drawn path is not searched, so it is checked before it is laid: every leg clear of
    # every hole (plated or not - a switch's centre hole, a mount's) by the hole clearance,
    # of every keep-out, and of every other net's copper on its layer by the clearance;
    # one that is not stops the run, by where (owner, 2026-10-04: a leg through KS-33's
    # centre hole went unseen because nothing checked the drawn path)
    allowed = set(nets) | ({spec["guard_traces"]["net"]} if spec.get("guard_traces") else set())
    bad = []
    for net, d in zip(nets, sides):
        for p in prims:
            g = p.offset(d).line(24).buffer(w / 2, cap_style=1)
            for geom, n, ls, kind in obs.near(g, 1.0):
                if kind in ("hole", "vhole", "npth"):
                    if geom.distance(g) < obs.hclear - 1e-3:
                        bad.append((net, kind, geom.centroid))
                elif L not in ls or kind in ("silk", "guard") or n in allowed:
                    continue
                elif kind == "keepout":
                    if geom.intersects(g):
                        bad.append((net, kind, geom.centroid))
                elif geom.distance(g) < obs.clear - 1e-3:
                    bad.append((net, f"{n} {kind}", geom.centroid))
    if bad:
        seen = sorted({(n, k, round(c.x, 1), round(c.y, 1)) for n, k, c in bad})
        sys.exit("pcb: pair " + " / ".join(nets) + ": its drawn path is not clear - "
                 + "; ".join(f"{n} against {k} at ({x}, {y})" for n, k, x, y in seen[:8])
                 + (" ..." if len(seen) > 8 else "") + " (layout.yaml pairs: through:, detours:)")
    for net, d in zip(nets, sides):
        for p in prims:
            lay_prim(board, obs, net, p.offset(d), w, L)
    # `tails:` - each leg's end to its pad on the other face, drawn: a track on the pair's
    # layer along `path` (body mm, from the leg's end), a via, and a track to the pad
    other = "F" if L == "B" else "B"
    for tl in spec.get("tails") or []:
        net = tl["net"]
        pts = [pcb.to_pcb(*q) for q in tl["path"]]
        vx, vy = pcb.to_pcb(*tl["via"])
        ref, num = tl["pad"].split(".")
        q = board.FindFootprintByReference(ref).FindPadByNumber(num).GetPosition()
        pad_at = (TO(q.x), TO(q.y))
        segs = [(a, b, L) for a, b in zip(pts + [(vx, vy)], pts[1:] + [(vx, vy)]) if math.dist(a, b) > 1e-3] + [((vx, vy), pad_at, other)]
        for a, b, lyr in segs:
            g = LineString([a, b]).buffer(w / 2, cap_style=1)
            for geom, n, ls, kind in obs.near(g, 1.0):
                if kind in ("hole", "vhole", "npth") and n != net:
                    hit = geom.distance(g) < obs.hclear - 1e-3
                elif lyr not in ls or kind in ("silk", "guard") or n == net:
                    continue
                else:
                    hit = geom.intersects(g) if kind == "keepout" else geom.distance(g) < obs.clear - 1e-3
                if hit:
                    sys.exit(f"pcb: pair tail {net} to {tl['pad']}: {n or kind} {kind} in the way near "
                             f"({geom.centroid.x:.1f}, {geom.centroid.y:.1f}) (layout.yaml pairs: tails:)")
        if not obs.via_ok(vx, vy, net):
            sys.exit(f"pcb: pair tail {net} to {tl['pad']}: no room for its via at {tl['via']}")
        for a, b, lyr in segs:
            lay_track(board, obs, net, a, b, w, lyr)
        lay_via(board, obs, net, vx, vy)
    total = sum(p.length() for p in prims)
    print(f"route: pair {' / '.join(nets)} - {total:.1f} mm side by side on {spec['layer']}, "
          f"{sum(1 for p in prims if p.kind == 'A')} arc(s), round {len(dets)} mount(s)")
    drawn = {t["pad"] for t in spec.get("tails") or []}
    report = [f"pair {n}: its end to {pd} left to the autorouter" for i, n in enumerate(nets)
              for pd in (spec["from"][i], spec["to"][i]) if pd not in drawn]
    if spec.get("guard_traces"):
        report += guard_prims(board, lay, obs, spec, prims, L)
    return report


def guard_prims(board, lay, obs, spec, prims, L):
    """guard_traces along a drawn centreline: each guard is the centreline offset, cut into
    ~1 mm pieces; a piece clear of every other net's copper is laid (a track or an arc),
    and each run of laid pieces is stitched into the guard net's island or strip at
    least every `every` mm, by a via beside a piece's end and a stub square to it; a run
    with room for fewer than two vias is not laid. Returns the spans left out."""
    gnet, every = spec["guard_traces"]["net"], float(spec["guard_traces"].get("every", 5.0))
    w, gap = spec["width"], spec["gap"]
    off = (w + gap) / 2 + w / 2 + obs.clear + w / 2
    voff = off + w / 2 + obs.clear + obs.via / 2 - 0.1
    region = plane_regions(board, lay).get(gnet)
    out, laid, vias = [], 0.0, 0

    def clear(g):
        for geom, n, ls, kind in obs.near(g, 0.5):
            if kind in ("hole", "vhole", "npth") and n != gnet:
                if geom.distance(g) < obs.hclear - 1e-3:
                    return False
                continue
            if L not in ls or kind in ("silk", "guard") or n == gnet:
                continue
            if kind == "keepout":
                if geom.intersects(g):
                    return False
            elif geom.distance(g) < obs.clear - 1e-3:
                return False
        return obs.inner.contains(g)
    for side in (1, -1):
        pieces = []
        for p in prims:
            o = p.offset(side * off)
            n = max(1, int(math.ceil(o.length() / 1.0)))
            for i in range(n):
                pieces.append((o.piece(i / n, (i + 1) / n), p, i / n, (i + 1) / n))
        ok = [clear(pc.line(8).buffer(w / 2, cap_style=1)) for pc, _, _, _ in pieces]
        runs, cur = [], None
        for i, k in enumerate(ok + [False]):
            if k and cur is None:
                cur = i
            if not k and cur is not None:
                runs.append((cur, i))
                cur = None
        for i0, i1 in runs:
            got, since = [], every
            for i in range(i0, i1 + 1):
                if i < i1:
                    since += pieces[i][0].length()
                j = min(i, i1 - 1)
                pc, base, t0, t1 = pieces[j]
                tt = t0 if i < i1 else t1
                e = pc.point(0) if i < i1 else pc.point(1)
                tg = base.tangent(tt)
                q = (e[0] - tg[1] * (voff - off) * side, e[1] + tg[0] * (voff - off) * side)
                if since >= every and (region is None or region.contains(Point(q))) and obs.via_ok(q[0], q[1], gnet):
                    got.append((e, q))
                    since = 0.0
            if len(got) < 2:
                a_, b_ = pieces[i0][0].point(0), pieces[i1 - 1][0].point(1)
                out.append(f"guard {gnet}: {sum(pieces[k][0].length() for k in range(i0, i1)):.1f} mm beside the pair, "
                           f"({a_[0]:.1f}, {a_[1]:.1f}) to ({b_[0]:.1f}, {b_[1]:.1f}), with no room for two stitching vias - left out")
                continue
            # the run from its first stitching via to its last
            first = next(k for k in range(i0, i1 + 1) if math.dist(pieces[min(k, i1 - 1)][0].point(0 if k < i1 else 1), got[0][0]) < 1e-6)
            last = next(k for k in range(i1, i0 - 1, -1) if math.dist(pieces[min(k, i1 - 1)][0].point(0 if k < i1 else 1), got[-1][0]) < 1e-6)
            for k in range(first, last):
                lay_prim(board, obs, gnet, pieces[k][0], w, L)
                laid += pieces[k][0].length()
            for e, q in got:
                lay_via(board, obs, gnet, q[0], q[1])
                lay_track(board, obs, gnet, e, q, w, L)
                vias += 1
    print(f"route: pair {' / '.join(spec['nets'])} - guard {gnet} {laid:.1f} mm, {vias} stitching via(s)")
    return out


def track_line(t):
    """A track's or arc's centreline as shapely, in PCB mm."""
    a, b = t.GetStart(), t.GetEnd()
    if isinstance(t, pcbnew.PCB_ARC):
        m = t.GetMid()
        p = Prim("A", **_arc_from3((TO(a.x), TO(a.y)), (TO(m.x), TO(m.y)), (TO(b.x), TO(b.y))))
        return p.line(24)
    if (a.x, a.y) == (b.x, b.y):
        return Point(TO(a.x), TO(a.y))
    return LineString([(TO(a.x), TO(a.y)), (TO(b.x), TO(b.y))])


def _arc_from3(p, m, q):
    ax, ay = p; bx, by = m; cx, cy = q
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0 = math.atan2(ay - uy, ax - ux)
    am = math.atan2(by - uy, bx - ux)
    a1 = math.atan2(cy - uy, cx - ux)
    def ccw_between(s, mid, e):
        tm = (mid - s) % (2 * math.pi)
        te = (e - s) % (2 * math.pi)
        return tm < te
    if ccw_between(a0, am, a1):
        sw = (a1 - a0) % (2 * math.pi)
    else:
        sw = -((a0 - a1) % (2 * math.pi))
    return dict(c=(ux, uy), r=r, a0=a0, sweep=sw)


def one_sided(board, v, lay):
    """A signal via whose copper is met on one layer only (KiCad's via_dangling): no
    track end of its net at it on the other face, and no plane of its net. Not a
    plated pad's - those join every layer."""
    if not isinstance(v, pcbnew.PCB_VIA) or v.GetNetname() in {pl["net"] for pl in lay.get("planes") or []} | \
            {s_["net"] for s_ in lay.get("islands") or []}:
        return False
    p, net, on = v.GetPosition(), v.GetNetname(), set()
    for t in board.GetTracks():
        if type(t) is pcbnew.PCB_TRACK and t.GetNetname() == net and (t.HitTest(p, 1000)):
            on.add(t.GetLayer())
    for f in board.GetFootprints():
        for q in f.Pads():
            if q.GetNetname() == net and q.HitTest(p):
                on |= {L for L in (pcbnew.F_Cu, pcbnew.B_Cu) if q.IsOnLayer(L)}
    return len(on) < 2


def tidy(board, lay):
    """After an autorouter: what it leaves that the checks fail - zero-length and
    duplicated tracks, tracks with an end that reaches nothing of their net (dangling),
    two tracks of a net meeting at under 90 degrees (square_joins, as on a key board),
    and collinear runs in pieces (merge_tracks). Locked copper, and with layout.yaml
    `route_fence:` everything outside it, is never deleted, moved, split or merged."""
    fence = fence_of(lay)
    fixed = lambda t: is_fixed(t, fence)
    key = lambda v: (v.x, v.y)
    n0 = n1 = n2 = 0
    seen = set()
    for t in [t for t in board.GetTracks() if type(t) is pcbnew.PCB_TRACK]:
        k = (t.GetNetname(), t.GetLayer(), t.GetWidth()) + tuple(sorted([key(t.GetStart()), key(t.GetEnd())]))
        if (t.GetStart() == t.GetEnd() or k in seen) and not fixed(t):
            board.Delete(t)         # Delete, not Remove: a Remove from a LOADED board crashes the next walk of it
            n0 += 1
            continue
        seen.add(k)
    # a track lying along another of its net and layer, over part of it: the two become
    # one, over both (an autorouter's overlap; check_tracks reads it as a 0-degree join)
    groups = {}
    for t in [t for t in board.GetTracks() if type(t) is pcbnew.PCB_TRACK]:
        groups.setdefault((t.GetNetname(), t.GetLayer(), t.GetWidth()), []).append(t)
    for ts in groups.values():
        alive = list(ts)
        again = True
        while again:
            again = False
            for i in range(len(alive)):
                for j in range(i + 1, len(alive)):
                    a, b = alive[i], alive[j]
                    if fixed(a) or fixed(b):
                        continue
                    p0, p1 = a.GetStart(), a.GetEnd()
                    dx, dy = p1.x - p0.x, p1.y - p0.y
                    l2 = dx * dx + dy * dy
                    if not l2:
                        continue
                    ks = []
                    for q in (b.GetStart(), b.GetEnd()):
                        if abs((q.x - p0.x) * dy - (q.y - p0.y) * dx) / math.sqrt(l2) > 1000:
                            break
                        ks.append(((q.x - p0.x) * dx + (q.y - p0.y) * dy) / l2)
                    else:
                        lo, hi = min(ks), max(ks)
                        if hi <= 1e-6 or lo >= 1 - 1e-6:
                            continue          # end to end, or apart: not an overlap
                        k0, k1 = min(0.0, lo), max(1.0, hi)
                        a.SetStart(pcbnew.VECTOR2I(int(p0.x + k0 * dx), int(p0.y + k0 * dy)))
                        a.SetEnd(pcbnew.VECTOR2I(int(p0.x + k1 * dx), int(p0.y + k1 * dy)))
                        board.Delete(b)
                        alive.pop(j)
                        n0 += 1
                        again = True
                        break
                if again:
                    break
    # dangling ends, repeatedly: an end touches another track of the net (its end or its
    # body), a via of the net, or a pad of the net on its layer - or it goes; and a via
    # of a net that has no plane, reached on fewer than two layers, goes with them
    pads = [(p, p.GetNetname()) for fp in board.GetFootprints() for p in fp.Pads()]
    planes = set(lay.get("fanout") or [])
    while True:
        for v in [v for v in board.GetTracks() if isinstance(v, pcbnew.PCB_VIA) and v.GetNetname() not in planes and not fixed(v)]:
            c, net = v.GetPosition(), v.GetNetname()
            on = {t.GetLayer() for t in board.GetTracks() if type(t) in (pcbnew.PCB_TRACK, pcbnew.PCB_ARC) and t.GetNetname() == net
                  and (t.GetStart() == c or t.GetEnd() == c or t.HitTest(c, 1000))}
            on |= {L for p, n in pads if n == net and p.HitTest(c) for L in (pcbnew.F_Cu, pcbnew.B_Cu) if p.IsOnLayer(L)}
            if len(on) < 2:
                board.Delete(v)
                n1 += 1
        tracks = [t for t in board.GetTracks() if type(t) is pcbnew.PCB_TRACK]
        arcs = [t for t in board.GetTracks() if type(t) is pcbnew.PCB_ARC]
        vias = [v for v in board.GetTracks() if isinstance(v, pcbnew.PCB_VIA)]
        gone = []
        for t in tracks:
            if fixed(t):
                continue
            for e in (t.GetStart(), t.GetEnd()):
                net, L = t.GetNetname(), t.GetLayer()
                ok = any(u is not t and u.GetNetname() == net and u.GetLayer() == L and u.HitTest(e, 1000) for u in tracks + arcs) \
                    or any(v.GetNetname() == net and v.HitTest(e, 1000) for v in vias) \
                    or any(n == net and p.IsOnLayer(L) and p.HitTest(e) for p, n in pads)
                if not ok:
                    gone.append(t)
                    break
        for t in gone:
            board.Delete(t)
        n1 += len(gone)
        if not gone:
            break
    # and what KiCad's DRC calls dangling that the test above lets by: a track of no
    # length, and a via met on one face only - by geometry, not by the board's own
    # connectivity, which in one process does not follow tracks added or deleted
    # (it took hundreds of live tracks, 2026-10-01)
    while True:
        gone = [t for t in board.GetTracks() if not fixed(t) and ((type(t) is pcbnew.PCB_TRACK and t.GetLength() < 1000)
                or one_sided(board, t, lay))]
        for t in gone:
            board.Delete(t)
        n1 += len(gone)
        if not gone:
            break
    r = Router(board, lay)
    r.fence = fence
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            c = Point(TO(t.GetPosition().x), TO(t.GetPosition().y))
            r.copper.append((t.GetNetname(), {TOP, BOT}, c.buffer(TO(t.GetWidth(pcbnew.F_Cu)) / 2), "track"))
        elif t.GetLayer() in LAYERS:
            g = track_line(t).buffer(TO(t.GetWidth()) / 2)
            r.copper.append((t.GetNetname(), {LAYERS.index(t.GetLayer())}, g, "track"))
    n2 = r.square_joins()
    n3 = merge_tracks(board, delete=True, fence=fence)
    c = float((lay.get("directions") or {}).get("chamfer", 0))
    n4 = chamfer(board, lay, c) if c else 0
    print(f"route: tidy - {n0} empty or doubled track(s), {n1} dangling, {n2} acute join(s) squared, "
          f"{n3} joint(s) merged, {n4} corner(s) chamfered")


def chamfer(board, lay, size):
    """Every right-angle corner where exactly two tracks of a net meet on a layer, with no
    pad or via there, cut to two 45-degree bends: each track shortened by up to `size` mm
    (never past half its length) and a diagonal laid between - where that diagonal keeps
    its clearance to every other net (Obstacles.track_ok). Returns how many."""
    obs = Obstacles(board, lay)
    LN = {pcbnew.F_Cu: "F", pcbnew.B_Cu: "B"}
    ends = {}
    for t in board.GetTracks():
        if type(t) is pcbnew.PCB_TRACK and t.GetLayer() in LN:
            for e in (t.GetStart(), t.GetEnd()):
                ends.setdefault((t.GetNetname(), t.GetLayer(), e.x, e.y), []).append(t)
    holes = {(v.GetNetname(), v.GetPosition().x, v.GetPosition().y) for v in board.GetTracks() if isinstance(v, pcbnew.PCB_VIA)}
    pads = [(p, p.GetNetname()) for f in board.GetFootprints() for p in f.Pads()]
    n = 0
    for (net, layer, x, y), ts in ends.items():
        if len(ts) != 2 or (net, x, y) in holes or is_fixed(ts[0], fence_of(lay)) or is_fixed(ts[1], fence_of(lay)):
            continue
        P = pcbnew.VECTOR2I(x, y)
        if any(nn == net and p.IsOnLayer(layer) and p.HitTest(P) for p, nn in pads):
            continue
        far = [t.GetEnd() if (t.GetStart().x, t.GetStart().y) == (x, y) else t.GetStart() for t in ts]
        if any((f.x, f.y) == (x, y) for f in far):
            continue
        u = [((f.x - x) / math.hypot(f.x - x, f.y - y), (f.y - y) / math.hypot(f.x - x, f.y - y), math.hypot(f.x - x, f.y - y)) for f in far]
        if abs(u[0][0] * u[1][0] + u[0][1] * u[1][1]) > 1e-3:
            continue            # not a right angle
        c = min(MM(size), u[0][2] / 2, u[1][2] / 2)
        if c < MM(0.15):
            continue
        A = pcbnew.VECTOR2I(int(round(x + c * u[0][0])), int(round(y + c * u[0][1])))
        B = pcbnew.VECTOR2I(int(round(x + c * u[1][0])), int(round(y + c * u[1][1])))
        w = max(t.GetWidth() for t in ts)
        if not obs.track_ok((TO(A.x), TO(A.y)), (TO(B.x), TO(B.y)), TO(w), net, LN[layer]):
            continue
        for t, E in zip(ts, (A, B)):
            if (t.GetStart().x, t.GetStart().y) == (x, y):
                t.SetStart(E)
            else:
                t.SetEnd(E)
        d = pcbnew.PCB_TRACK(board)
        d.SetStart(A)
        d.SetEnd(B)
        d.SetWidth(w)
        d.SetLayer(layer)
        d.SetNet(ts[0].GetNet())
        board.Add(d)
        n += 1
    return n


def complete(board, lay, unconnected, max_nodes=250000, per_mm=2500, frozen=(), layers=None, via_cost=None):
    """After the autorouter: each connection KiCad still counts missing - `unconnected`,
    [(net, (x, y), (x, y))], the two copper items' positions from its DRC - routed by
    A* on both outer layers at once, on the lazy 0.2 mm grid, a via wherever one is legal
    (Obstacles.via_ok) and costing VIA, from the copper at the first position to the copper
    at the second. With layout.yaml `rip_up: n`, a connection with no way through is
    searched again through other nets' copper, each cell of it costing SOFT: the nets that
    path crosses are taken up whole (never a plane net's, the pair's or locked copper,
    and each net at most n times), the connection laid, and theirs queued again, pad to
    pad. Returns the ones it could not route.

    The three keywords are the families stage's (route_families) and change nothing at
    their defaults: `frozen` nets the rip-up may not take up (an earlier family's),
    `layers` the routed layers ('F', 'B', 'I') it may use, `via_cost` in place of
    directions: via_cost."""
    import pcb
    obs = Obstacles(board, lay)
    classes = lay.get("net_classes") or {}
    width_of = lambda net: next((c["track"] for c in classes.values() if net in c["nets"]), lay["rules"]["track"])
    failed = []
    fixed = set(lay.get("fanout") or []) | {pl["net"] for pl in lay.get("planes") or []} | \
        {s_["net"] for s_ in lay.get("islands") or []} | {n for pr in lay.get("pairs") or [] for n in pr["nets"]} | set(frozen)
    fence = fence_of(lay)
    if fence is not None:
        # layout.yaml route_fence: a net with any copper outside it is not taken up (its
        # rip-up is the whole net), and neither is a net with locked copper
        fixed |= {t.GetNetname() for t in board.GetTracks() if is_fixed(t, fence)}
    limit, rips = int(lay.get("rip_up", 0)), {}
    queue = list(unconnected)
    # the layers it routes: the outer two, and layer 3 where layout.yaml directions: names it
    # (a four-layer board whose layer 3 is a routing layer, the module's)
    dirs_ = lay.get("directions") or {}
    routed_all = ["F", "B"] + (["I"] if "In2.Cu" in (dirs_.get("layers") or {}) or "In2.Cu" in (dirs_.get("routed") or []) else [])
    if layers is not None:
        routed_all = [L for L in routed_all if L in layers]
    via_cost = float(dirs_.get("via_cost", VIA) if via_cost is None else via_cost)
    # a net class's `layers:` - the only layers its nets route on (an analog net kept on
    # layer 1, over its island, not on layer 4 over another rail's plane)
    LK_ = {"F.Cu": "F", "B.Cu": "B", "In2.Cu": "I"}
    only = {n: [LK_[L] for L in c["layers"]] for c in classes.values() if c.get("layers") for n in c["nets"]}
    # ...or a class's `layer_cost:` - each step on that layer costs this many times more, so
    # its nets take it only for the hops they cannot make on the others
    lcost = {n: {LK_[L]: float(v) for L, v in c["layer_cost"].items()} for c in classes.values() if c.get("layer_cost") for n in c["nets"]}
    # ...or a class's `via: [diameter, drill]` - its nets' vias at that size, not the
    # board's (a power rail that must change layers does it through one via sized for
    # its current, not a signal's 0.3 mm drill: #8-6)
    via_of = {n: tuple(float(v) for v in c["via"]) for c in classes.values() if c.get("via") for n in c["nets"]}
    via_default = (obs.via, obs.drill)
    while queue:
        net, pa, pb = queue.pop(0)
        if (obs.via, obs.drill) != via_of.get(net, via_default):
            obs.via, obs.drill = via_of.get(net, via_default)
            obs._via_inner = None
        routed = [L for L in routed_all if L in only.get(net, routed_all)]
        lc_ = lcost.get(net, {})
        w = width_of(net)
        grids = {L: Grid(obs, L, w / 2, own={net}) for L in routed}
        gF = grids[routed[0]]       # every layer's grid has one frame: its cells and points
        vcache = {}

        def via_ok(i, j):
            if (i, j) not in vcache:
                x, y = gF.xy((i, j))
                vcache[(i, j)] = obs.via_ok(x, y, net)
            return vcache[(i, j)]

        def cells_of(p):
            """The cells on the copper of `net` at p (a pad or a track end), per layer."""
            x, y = p
            out = set()
            for g, n, ls, kind in obs.near(Point(x, y), 0.05):
                if n == net and kind in ("pad", "smd", "track", "via") and g.distance(Point(x, y)) < 0.05:
                    gx0, gy0, gx1, gy1 = g.bounds
                    g_ = g.buffer(-0.02)
                    c0, c1 = gF.cell(gx0, gy0), gF.cell(gx1, gy1)
                    for i in range(c0[0], c1[0] + 1):
                        for j in range(c0[1], c1[1] + 1):
                            if g_.contains(Point(*gF.xy((i, j)))):
                                out |= {(L, i, j) for L in ls if L in grids}    # a THT pad's inner layer only where it is routed
            return out
        src, dst = cells_of(pa), cells_of(pb)
        if src & dst and {c[0] for c in src | dst} != {"F"} and any(c[0] == "F" for c in src | dst):
            # the two items stand at one place on different faces (a front pad over a rear
            # one): a path from the front copper to the rest, so a via joins them
            src, dst = {c for c in src | dst if c[0] == "F"}, {c for c in src | dst if c[0] != "F"}
        # start and end only where a track may stand: a cell inside a pad can still be
        # within clearance of the next pin's copper (all of them, if none may)
        src = {c for c in src if grids[c[0]].free(c[1], c[2])} or src
        dst = {c for c in dst if grids[c[0]].free(c[1], c[2])} or dst
        if not src or not dst:
            failed.append((net, pa, pb, "its copper was not found"))
            continue
        moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, DIAG), (1, -1, DIAG), (-1, 1, DIAG), (-1, -1, DIAG)]
        soft_of = {}

        def softc(L, i, j):
            """None where the cell is closed by anything but another net's own unlocked
            routing; else the extra cost of entering it, and the nets it would cross."""
            if (L, i, j) not in soft_of:
                gr = grids[L]
                p = Point(*gr.xy((i, j)))
                nets = set()
                if not gr.inner.contains(p):
                    soft_of[(L, i, j)] = None
                    return None
                for g, n, ls, kind in obs.within(p, gr.rad - 1e-4):
                    if L not in ls or kind in ("silk", "hole", "vhole") or (n == net and kind != "keepout"):
                        continue
                    if kind in ("track", "via") and n and n not in fixed and not n.startswith("unconnected"):
                        nets.add(n)
                        continue
                    nets = None
                    break
                soft_of[(L, i, j)] = nets
            return soft_of[(L, i, j)]
        # layout.yaml directions: a step against its layer's preferred direction costs
        # against_cost, a diagonal one half way between (a 45-degree corner stays cheap).
        # `layers:` holds over the whole board (the controller's boards); `regions:` only
        # inside each region's rectangle (frame mm), free routing elsewhere - the owner's
        # rule, 2026-10-03: one direction per layer only where a crossing needs it
        # (docs/reference/tooling.md, the router).
        dirs = dirs_
        ag = float(dirs.get("against_cost", 1.0))
        LK = {"F.Cu": "F", "B.Cu": "B", "In2.Cu": "I"}
        way = {LK[k]: v for k, v in (dirs.get("layers") or {}).items() if k in LK}
        regions = []
        for rg in dirs.get("regions") or []:
            x0, y0, x1, y1 = rg["rect"]
            (ax, ay), (bx, by) = pcb.to_pcb(x0, y0), pcb.to_pcb(x1, y1)
            regions.append((min(ax, bx), min(ay, by), max(ax, bx), max(ay, by),
                            {LK[k]: v for k, v in (rg.get("layers") or {}).items() if k in LK}))

        def way_at(L, i, j):
            if regions:
                x, y = gF.xy((i, j))
                for rx0, ry0, rx1, ry1, w_ in regions:
                    if rx0 <= x <= rx1 and ry0 <= y <= ry1 and L in w_:
                        return w_[L]
            return way.get(L)

        def step_cost(L, di, dj, c, i=0, j=0):
            c = c * lc_.get(L, 1.0)
            wl = way_at(L, i, j)
            if wl is None:
                return c
            along = di if wl == "horizontal" else dj
            if di and dj:
                return c * (1 + ag) / 2
            return c if along else c * ag

        def search(src, dst, target, soft=False):
            ti, tj = gF.cell(*target)
            h = lambda i, j: math.hypot(i - ti, j - tj)
            openq, came, cost, seen = [], {}, {}, set()
            for s_ in src:
                cost[s_] = 0
                heapq.heappush(openq, (h(s_[1], s_[2]), 0, s_, None))
            while openq and len(seen) < budget:
                f, g, cur, pd = heapq.heappop(openq)
                if cur in seen:
                    continue
                seen.add(cur)
                if cur in dst:
                    path = [cur]
                    while path[-1] in came:
                        path.append(came[path[-1]])
                    return path[::-1], len(seen)
                L, i, j = cur
                gr = grids[L]
                for di, dj, c in moves:
                    nxt = (L, i + di, j + dj)
                    extra = 0
                    if nxt in seen:
                        continue
                    if not (gr.free(i + di, j + dj) or nxt in dst):
                        if not soft or softc(L, i + di, j + dj) is None:
                            continue
                        extra = SOFT
                    if di and dj and not (gr.free(i + di, j) and gr.free(i, j + dj)):
                        if not soft or softc(L, i + di, j) is None or softc(L, i, j + dj) is None:
                            continue
                    ng = g + extra + step_cost(L, di, dj, c, i, j) + (TURN.get(steps45(pd, (di, dj)), 0) if pd else 0)
                    if ng < cost.get(nxt, 1e18):
                        cost[nxt], came[nxt] = ng, cur
                        heapq.heappush(openq, (ng + h(i + di, j + dj), ng, nxt, (di, dj)))
                for O in routed:
                    if O == L:
                        continue
                    nxt = (O, i, j)
                    if nxt not in seen and via_ok(i, j) and (grids[O].free(i, j) or nxt in dst
                                                             or (soft and softc(O, i, j) is not None)):
                        ng = g + via_cost
                        if ng < cost.get(nxt, 1e18):
                            cost[nxt], came[nxt] = ng, cur
                            heapq.heappush(openq, (ng + h(i, j), ng, nxt, None))
            return None, len(seen)
        # from the first item; if that search is boxed in early, from the second (a
        # pad walled in on one side can still be reached from outside)
        budget = max_nodes + per_mm * math.dist(pa, pb)     # a long connection gets a longer search
        path, nseen = search(src, dst, pb)
        if path is None and nseen < budget:
            path, n2 = search(dst, src, pa)
            nseen += n2
            if path is not None:
                path = path[::-1]
        seen = range(nseen)
        goal = path[-1] if path else None
        if goal is None and limit:
            # rip-up: a way through other nets' routing, and those nets taken up whole
            rp, _ = search(src, dst, pb, soft=True)
            crossed = set().union(*(softc(*c) or set() for c in rp if not grids[c[0]].free(c[1], c[2]))) if rp else set()
            if rp and crossed and all(rips.get(n, 0) < limit for n in crossed):
                for t in list(board.GetTracks()):
                    if t.GetNetname() in crossed and not t.IsLocked():
                        board.Delete(t)
                obs.items = [it for it in obs.items if not (it[1] in crossed and it[3] in ("track", "via", "vhole"))]
                obs._tree = None
                queue[:] = [(net, pa, pb)] + [q for q in queue if q[0] not in crossed]
                for n in sorted(crossed):
                    rips[n] = rips.get(n, 0) + 1
                    pts = [(TO(q.GetPosition().x), TO(q.GetPosition().y)) for f in board.GetFootprints()
                           for q in f.Pads() if q.GetNetname() == n]
                    done, rest = pts[:1], pts[1:]
                    while rest:         # pad to pad, the shortest tree
                        a, b = min(((a, b) for a in done for b in rest), key=lambda ab: math.dist(*ab))
                        queue.append((n, a, b))
                        done.append(b)
                        rest.remove(b)
                print(f"route: complete - {net} ({pa[0]:.1f}, {pa[1]:.1f}): rip-up of {', '.join(sorted(crossed))}", flush=True)
                continue
        if goal is None:
            failed.append((net, pa, pb, "no way through the room the autorouter left"))
            print(f"route: complete - {net} ({pa[0]:.1f}, {pa[1]:.1f}) to ({pb[0]:.1f}, {pb[1]:.1f}): no way ({len(seen)} cells searched)", flush=True)
            continue
        print(f"route: complete - {net} ({pa[0]:.1f}, {pa[1]:.1f}) to ({pb[0]:.1f}, {pb[1]:.1f}): routed", flush=True)
        # runs per layer, a via between
        k = 0
        while k < len(path):
            m = k
            while m + 1 < len(path) and path[m + 1][0] == path[k][0]:
                m += 1
            run = [p[1:] for p in path[k:m + 1]]
            pts = [gF.xy(c) for c in corners(run)]
            for a, b in zip(pts, pts[1:]):
                lay_track(board, obs, net, a, b, w, path[k][0], locked=False)
            if m + 1 < len(path):
                lay_via(board, obs, net, *gF.xy(path[m][1:]), locked=False)
            k = m + 1
    if (obs.via, obs.drill) != via_default:
        obs.via, obs.drill = via_default
        obs._via_inner = None
    return failed


# ------------------------------------------------------------------ families (issue #41)
#
# The owner, 2026-10-05: "we should do families of traces... then do those and then do
# the next ones then do the next ones instead of just letting the auto router go
# Willy-nilly". layout.yaml `families:` - an ordered list - is routed one family at a
# time, and each family's copper is fixed for the families after it. Inside a family
# the connections are routed together by negotiated congestion (PathFinder, McMurchie
# and Ebeling, 1995): every connection is routed letting its track share cells with
# the family's other nets, each shared cell gets dearer (a present cost that grows
# each round and a history cost that remembers), and all of them are routed again,
# until none share a cell or the round or time cap is reached. The order is
# crossing-aware - fewest airwire crossings first, then shortest - an idea from
# drandyhaas/KiCadRoutingTools (MIT; the idea only, no code). What negotiation leaves
# shared, or cannot reach, goes to complete() as before, the earlier families frozen.
# Without `families:`, route_families() IS complete(): nothing else changes.

FAMILY_ITERATIONS = 16      # negotiation rounds, a family's `iterations:`
FAMILY_TIME_S = 300.0       # seconds a family may negotiate, its `time_s:`
PRES0, PRES_GROW = 0.5, 2.0     # the present-sharing factor, and its growth per round
HIST = 1.0                  # what one round of sharing adds to a cell's history cost
LANE = 0.55                 # `bundle: true`: a step on a lane beside a bundle-mate costs this much
_LK = {"F.Cu": "F", "B.Cu": "B", "In2.Cu": "I"}


def _net_key(n):
    return n.lstrip("/") if n else n


def family_match(net, pats, lay):
    """Is `net` one of `pats` - a name (with or without its leading /), an fnmatch glob,
    or class:<name> (a layout.yaml net_classes: entry's nets)?"""
    import fnmatch
    k = _net_key(net)
    for p in pats:
        p = str(p)
        if p.startswith("class:"):
            c = (lay.get("net_classes") or {}).get(p[6:])
            if c is None:
                raise SystemExit(f"route: families - no net class {p[6:]!r} in net_classes:")
            if k in {_net_key(n) for n in c["nets"]}:
                return True
        elif fnmatch.fnmatchcase(k, _net_key(p)):
            return True
    return False


def family_plan(lay, nets):
    """layout.yaml families: as [(spec, set of nets)], in routing order. `route_first:`
    leads, as a family of that name; each net goes to the FIRST family that names it;
    `rest` - every net no family names - is last, with the options of a family named
    rest if one is listed. Plane, island, fanout and pair nets are routed before any
    family (prepare) and are left out. An empty family is kept, so the report says so."""
    skip = set(lay.get("fanout") or []) | {pl["net"] for pl in lay.get("planes") or []} | \
        {s_["net"] for s_ in lay.get("islands") or []} | {n for pr in lay.get("pairs") or [] for n in pr["nets"]}
    specs = list(lay.get("families") or [])
    names = [s_.get("name") for s_ in specs]
    if len(set(names)) != len(names) or None in names:
        raise SystemExit("route: families - every family needs a name, and each name once")
    if lay.get("route_first") and "route_first" not in names:
        specs = [{"name": "route_first", "nets": list(lay["route_first"])}] + specs
    rest_spec = next((s_ for s_ in specs if s_["name"] == "rest"), {"name": "rest"})
    specs = [s_ for s_ in specs if s_["name"] != "rest"]
    left = [n for n in nets if n and not n.startswith("unconnected") and n not in skip]
    plan = []
    for s_ in specs:
        mine = {n for n in left if family_match(n, s_.get("nets") or [], lay)}
        left = [n for n in left if n not in mine]
        plan.append((s_, mine))
    plan.append((rest_spec, set(left)))
    return plan


def _crossings(conns):
    """For each connection (net, a, b), how many other nets' airwires its own crosses."""
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return (v > 1e-9) - (v < -1e-9)
    out = []
    for k, (n, a, b) in enumerate(conns):
        out.append(sum(1 for m, (n2, p, q) in enumerate(conns)
                       if m != k and n2 != n and orient(a, b, p) * orient(a, b, q) < 0 and orient(p, q, a) * orient(p, q, b) < 0))
    return out


class _Shared:
    """One layer's routing grid for one track width, shared by every net of that width
    (Grid's test, cached once for all of them): each cell holds the nets whose copper is
    within the clearance, as a frozenset, or None where nothing may go - outside the edge
    clearance, a keep-out, an unplated hole, copper on no net. A cell is free for a net
    when it holds no net but that one."""

    def __init__(self, obs, layer, half):
        from shapely.prepared import prep
        self.obs, self.L = obs, layer
        self.rad = half + obs.clear + SLACK
        self.x0, self.y0 = obs.outline.bounds[:2]
        self.inner = prep(obs.outline.buffer(-(obs.edge + half + SLACK)))
        self.cache = {}

    xy = Grid.xy
    cell = Grid.cell

    def holds(self, i, j):
        c = self.cache.get((i, j), 0)
        if c == 0:
            p = Point(*self.xy((i, j)))
            if not self.inner.contains(p):
                c = None
            else:
                nets = set()
                for g, n, ls, kind in self.obs.within(p, self.rad - 1e-4):
                    if self.L not in ls or kind in ("silk", "hole", "vhole"):
                        continue
                    if kind in ("keepout", "npth") or not n:
                        nets = None
                        break
                    nets.add(n)
                c = None if nets is None else frozenset(nets)
            self.cache[(i, j)] = c
        return c

    def free(self, net, i, j):
        c = self.holds(i, j)
        return c is not None and (not c or c == {net})


def _directions(lay, xy):
    """complete()'s `directions:` cost, as step_cost(L, di, dj, c, i, j)."""
    import pcb
    dirs = lay.get("directions") or {}
    ag = float(dirs.get("against_cost", 1.0))
    way = {_LK[k]: v for k, v in (dirs.get("layers") or {}).items() if k in _LK}
    regions = []
    for rg in dirs.get("regions") or []:
        x0, y0, x1, y1 = rg["rect"]
        (ax, ay), (bx, by) = pcb.to_pcb(x0, y0), pcb.to_pcb(x1, y1)
        regions.append((min(ax, bx), min(ay, by), max(ax, bx), max(ay, by),
                        {_LK[k]: v for k, v in (rg.get("layers") or {}).items() if k in _LK}))

    def way_at(L, i, j):
        if regions:
            x, y = xy((i, j))
            for rx0, ry0, rx1, ry1, w_ in regions:
                if rx0 <= x <= rx1 and ry0 <= y <= ry1 and L in w_:
                    return w_[L]
        return way.get(L)

    def step_cost(L, di, dj, c, i, j):
        wl = way_at(L, i, j)
        if wl is None:
            return c
        if di and dj:
            return c * (1 + ag) / 2
        return c if (di if wl == "horizontal" else dj) else c * ag
    return step_cost


def route_families(board, lay, unconnected, report=None):
    """complete(), family by family, when layout.yaml has `families:`; complete() itself
    when it has not. `unconnected` as complete's; returns what could not be routed. Each
    family's record (route_family) is printed, and appended to `report` if one is given."""
    if not lay.get("families"):
        return complete(board, lay, unconnected)
    allnets = sorted({str(n) for n in board.GetNetsByName().keys()} | {m[0] for m in unconnected})
    failed, done = [], set()
    for spec, nets in family_plan(lay, allnets):
        conns = [m for m in unconnected if m[0] in nets]
        rec = route_family(board, lay, spec, conns, frozen=set() if spec.get("rip_up") else done)
        failed += rec.pop("failed_list")
        if report is not None:
            report.append(rec)
        done |= nets
    return failed


def family_line(rec):
    return (f"route: family {rec['family']:<14} {rec['routed']:>3} of {rec['connections']:<3} routed "
            f"({rec['negotiated']} negotiated, {rec['fallback']} by complete), {rec['failed']} failed, "
            f"{rec['vias']} via(s), {rec['length_mm']:.1f} mm; {rec['rounds']} round(s), "
            f"{rec['shared_cells']} cell(s) still shared, {rec['seconds']:.0f} s")


def route_family(board, lay, spec, conns, frozen=()):
    """One family: `conns` [(net, (x, y), (x, y))] negotiated together (the comment
    above), then what that leaves to complete(), the `frozen` nets kept from its rip-up.
    Returns the family's record: connections, routed, negotiated, fallback (routed by
    complete), failed, vias, length_mm, rounds, shared_cells, seconds, failed_list."""
    import time
    t0 = time.monotonic()
    name = spec.get("name", "?")
    rec = {"family": name, "connections": len(conns), "routed": 0, "negotiated": 0, "fallback": 0,
           "failed": 0, "vias": 0, "length_mm": 0.0, "rounds": 0, "shared_cells": 0, "seconds": 0.0,
           "failed_list": []}
    if not conns:
        print(family_line(rec), flush=True)
        return rec
    iters = int(spec.get("iterations", FAMILY_ITERATIONS))
    tcap = float(spec.get("time_s", FAMILY_TIME_S))
    obs = Obstacles(board, lay)
    classes = lay.get("net_classes") or {}
    width_of = lambda net: next((c["track"] for c in classes.values() if net in c["nets"]), lay["rules"]["track"])
    dirs_ = lay.get("directions") or {}
    routed_all = ["F", "B"] + (["I"] if "In2.Cu" in (dirs_.get("layers") or {}) or "In2.Cu" in (dirs_.get("routed") or []) else [])
    fam_layers = [_LK[L] for L in spec["layers"]] if spec.get("layers") else None
    if fam_layers:
        routed_all = [L for L in routed_all if L in fam_layers]
    if not routed_all:
        raise SystemExit(f"route: family {name} - its layers: {spec.get('layers')} are none the board routes")
    via_cost = float(spec.get("via_cost", dirs_.get("via_cost", VIA)))
    only = {n: [_LK[L] for L in c["layers"]] for c in classes.values() if c.get("layers") for n in c["nets"]}
    lcost = {n: {_LK[L]: float(v) for L, v in c["layer_cost"].items()} for c in classes.values() if c.get("layer_cost") for n in c["nets"]}
    via_of = {n: tuple(float(v) for v in c["via"]) for c in classes.values() if c.get("via") for n in c["nets"]}
    via_default = (obs.via, obs.drill)
    shared = {}

    def grid(L, w):
        if (L, w) not in shared:
            shared[(L, w)] = _Shared(obs, L, w / 2)
        return shared[(L, w)]
    g0 = grid(routed_all[0], lay["rules"]["track"])
    xy, cell = g0.xy, g0.cell
    step_cost = _directions(lay, xy)
    region = None
    if spec.get("region"):
        # in the board's own (KiCad) mm, as tools/pcb_plot.py draws it
        x0, y0, x1, y1 = spec["region"]
        (a0, b0), (a1, b1) = cell(min(x0, x1), min(y0, y1)), cell(max(x0, x1), max(y0, y1))
        region = (a0, b0, a1, b1)
    vcache = {}

    def use_via(net):
        want = via_of.get(net, via_default)
        if (obs.via, obs.drill) != want:
            obs.via, obs.drill = want
            obs._via_inner = None

    def via_ok(net, i, j):
        k = (net, i, j)
        if k not in vcache:
            use_via(net)
            vcache[k] = obs.via_ok(*xy((i, j)), net)
        return vcache[k]

    # each connection's context: its layers, width, and the cells on its two items
    ctx = []
    for net, pa, pb in conns:
        w = width_of(net)
        layers = [L for L in routed_all if L in only.get(net, routed_all)]
        c = {"net": net, "pa": pa, "pb": pb, "w": w, "layers": layers, "lc": lcost.get(net, {}), "src": set(), "dst": set()}
        ctx.append(c)
        if not layers:
            continue

        def cells_of(p):
            out = set()
            for g, n, ls, kind in obs.near(Point(*p), 0.05):
                if n == net and kind in ("pad", "smd", "track", "via") and g.distance(Point(*p)) < 0.05:
                    gx0, gy0, gx1, gy1 = g.bounds
                    g_ = g.buffer(-0.02)
                    c0, c1 = cell(gx0, gy0), cell(gx1, gy1)
                    for i in range(c0[0], c1[0] + 1):
                        for j in range(c0[1], c1[1] + 1):
                            if g_.contains(Point(*xy((i, j)))):
                                out |= {(L, i, j) for L in ls if L in layers}
            return out
        src, dst = cells_of(pa), cells_of(pb)
        if src & dst and {q[0] for q in src | dst} != {"F"} and any(q[0] == "F" for q in src | dst):
            src, dst = {q for q in src | dst if q[0] == "F"}, {q for q in src | dst if q[0] != "F"}
        c["src"] = {q for q in src if grid(q[0], w).free(net, q[1], q[2])} or src
        c["dst"] = {q for q in dst if grid(q[0], w).free(net, q[1], q[2])} or dst
    cross = _crossings(conns)
    order = sorted(range(len(conns)), key=lambda k: (cross[k], math.dist(conns[k][1], conns[k][2])))
    # sharing: within this of another net's track centre, a track centre is too near -
    # the widest of the family's tracks (both halves), the clearance, and the grid's
    # slack (Grid's own margin: a diagonal between two free cells); round a via, its
    # larger copper instead of a track's half
    wmax = max(c["w"] for c in ctx)
    reach = wmax + obs.clear + SLACK
    vmax = max([via_default[0]] + [via_of[c["net"]][0] for c in ctx if c["net"] in via_of])
    vreach = vmax / 2 + wmax / 2 + obs.clear + SLACK

    def disc_of(r):
        R = int(math.ceil(r / GRID))
        return [(di, dj) for di in range(-R, R + 1) for dj in range(-R, R + 1) if math.hypot(di, dj) * GRID < r - 1e-6]
    disc, vdisc = disc_of(reach), disc_of(vreach)
    vvdisc = disc_of(vmax + obs.clear + SLACK)       # a via from another net's via
    # a bundle's lanes: the cells one pitch off a bundle-mate's track, the pitch the
    # family's `pitch:` or the least the clearance allows, on the grid
    pitch = float(spec.get("pitch", math.ceil(reach / GRID - 1e-6) * GRID))
    P = int(math.ceil(pitch / GRID)) + 1
    ring = [(di, dj) for di in range(-P, P + 1) for dj in range(-P, P + 1) if abs(math.hypot(di, dj) * GRID - pitch) <= GRID * 0.5]
    bundle = bool(spec.get("bundle"))
    occ, vocc, hist, lanes = {}, {}, {}, {}
    paths = [None] * len(conns)

    def is_via(p, idx):
        return (idx + 1 < len(p) and p[idx + 1][0] != p[idx][0]) or (idx > 0 and p[idx - 1][0] != p[idx][0])

    def bump(d_, q, net, sign):
        d = d_.setdefault(q, {})
        d[net] = d.get(net, 0) + sign
        if not d[net]:
            del d[net]
            if not d:
                del d_[q]

    def mark(k, sign):
        p = paths[k]
        if not p:
            return
        net = ctx[k]["net"]
        cells, vcells = set(), set()
        for idx, (L, i, j) in enumerate(p):
            via = is_via(p, idx)
            for L2 in (ctx[k]["layers"] if via else (L,)):
                cells |= {(L2, i + di, j + dj) for di, dj in (vdisc if via else disc)}
            if via:
                vcells |= {(i + di, j + dj) for di, dj in vvdisc}
        for q in cells:
            bump(occ, q, net, sign)
        for q in vcells:
            bump(vocc, q, net, sign)
        if bundle:
            for L, i, j in p:
                for di, dj in ring:
                    q = (L, i + di, j + dj)
                    lanes[q] = lanes.get(q, 0) + sign

    def others(net, q, d_=occ):
        d = d_.get(q)
        return 0 if not d else sum(1 for n in d if n != net)

    def search(k, pres):
        c = ctx[k]
        net, src, dst, w, lc = c["net"], c["src"], c["dst"], c["w"], c["lc"]
        if not src or not dst:
            return None
        grids = {L: grid(L, w) for L in c["layers"]}
        ti, tj = cell(*c["pb"])
        h = lambda i, j: math.hypot(i - ti, j - tj)
        budget = 250000 + 2500 * math.dist(c["pa"], c["pb"])
        moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, DIAG), (1, -1, DIAG), (-1, 1, DIAG), (-1, -1, DIAG)]
        openq, came, cost, seen = [], {}, {}, set()
        for s_ in src:
            cost[s_] = 0
            heapq.heappush(openq, (h(s_[1], s_[2]), 0, s_, None))

        def inside(i, j):
            return region is None or (region[0] <= i <= region[2] and region[1] <= j <= region[3])

        def enter(q, base, via=False):
            # PathFinder: (base + history) x (1 + present x the other nets sharing it)
            n_ = others(net, q) + (others(net, q[1:], vocc) if via else 0)
            f = LANE if bundle and lanes.get(q) and not n_ else 1.0
            return (base * f + hist.get(q, 0.0)) * (1 + pres * n_)
        while openq and len(seen) < budget:
            f, g, cur, pd = heapq.heappop(openq)
            if cur in seen:
                continue
            seen.add(cur)
            if cur in dst:
                path = [cur]
                while path[-1] in came:
                    path.append(came[path[-1]])
                return path[::-1]
            L, i, j = cur
            gr = grids[L]
            for di, dj, cst in moves:
                nxt = (L, i + di, j + dj)
                if nxt in seen:
                    continue
                if nxt not in dst and not (gr.free(net, i + di, j + dj) and inside(i + di, j + dj)):
                    continue
                if di and dj and not (gr.free(net, i + di, j) and gr.free(net, i, j + dj)):
                    continue
                base = step_cost(L, di, dj, cst, i, j) * lc.get(L, 1.0) + (TURN.get(steps45(pd, (di, dj)), 0) if pd else 0)
                ng = g + enter(nxt, base)
                if ng < cost.get(nxt, 1e18):
                    cost[nxt], came[nxt] = ng, cur
                    heapq.heappush(openq, (ng + h(i + di, j + dj), ng, nxt, (di, dj)))
            for O in c["layers"]:
                if O == L:
                    continue
                nxt = (O, i, j)
                if nxt not in seen and via_ok(net, i, j) and (grids[O].free(net, i, j) or nxt in dst):
                    ng = g + enter(nxt, via_cost, via=True)
                    if ng < cost.get(nxt, 1e18):
                        cost[nxt], came[nxt] = ng, cur
                        heapq.heappush(openq, (ng + h(i, j), ng, nxt, None))
        return None

    def shared_cells(k):
        p, net = paths[k], ctx[k]["net"]
        return {q for idx, q in enumerate(p) if others(net, q) or (is_via(p, idx) and others(net, q[1:], vocc))} if p else set()
    pres, timed_out = PRES0, False
    for rnd in range(iters):
        rec["rounds"] = rnd + 1
        for k in order:
            if time.monotonic() - t0 > tcap:
                timed_out = True
                break
            mark(k, -1)
            paths[k] = search(k, pres)
            mark(k, +1)
        clash = set()
        for k in range(len(conns)):
            clash |= shared_cells(k)
        for q in clash:
            hist[q] = hist.get(q, 0.0) + HIST
        rec["shared_cells"] = len(clash)
        if not clash or timed_out:
            break
        pres *= PRES_GROW
    if timed_out:
        print(f"route: family {name} - its time cap, {tcap:.0f} s, reached in round {rec['rounds']}", flush=True)
    # lay what negotiated clear, each piece tested against the copper as it then stands
    # (the grid's sharing test is an estimate; Obstacles' is exact); the rest to complete()
    left = []
    for k in order:
        net, p = ctx[k]["net"], paths[k]
        if not p or shared_cells(k):
            left.append(conns[k])
            continue
        w = ctx[k]["w"]
        segs, vias = [], []
        m0 = 0
        while m0 < len(p):
            m = m0
            while m + 1 < len(p) and p[m + 1][0] == p[m0][0]:
                m += 1
            pts = [xy(q) for q in corners([q[1:] for q in p[m0:m + 1]])]
            segs += [(a, b, p[m0][0]) for a, b in zip(pts, pts[1:])]
            if m + 1 < len(p):
                vias.append(xy(p[m][1:]))
            m0 = m + 1
        use_via(net)
        if all(obs.track_ok(a, b, w, net, L) for a, b, L in segs) and all(obs.via_ok(x, y, net) for x, y in vias):
            for a, b, L in segs:
                lay_track(board, obs, net, a, b, w, L, locked=False)
            for x, y in vias:
                lay_via(board, obs, net, x, y, locked=False)
            rec["negotiated"] += 1
        else:
            left.append(conns[k])
    if (obs.via, obs.drill) != via_default:
        obs.via, obs.drill = via_default
        obs._via_inner = None
    if left:
        fl = complete(board, lay, left, frozen=frozen, layers=fam_layers, via_cost=spec.get("via_cost"))
        rec["fallback"] = len(left) - len(fl)
        rec["failed_list"] = fl
    rec["failed"] = len(rec["failed_list"])
    rec["routed"] = rec["connections"] - rec["failed"]
    # the family's own copper: its nets' unlocked tracks and vias (prepare's are locked)
    nets = {c["net"] for c in ctx}
    mine = [t for t in board.GetTracks() if t.GetNetname() in nets and not t.IsLocked()]
    rec["vias"] = sum(1 for t in mine if isinstance(t, pcbnew.PCB_VIA))
    rec["length_mm"] = sum(TO(t.GetLength()) for t in mine if type(t) is pcbnew.PCB_TRACK)
    rec["seconds"] = time.monotonic() - t0
    print(family_line(rec), flush=True)
    return rec


def plane_orphans(board, lay):
    """The plane-net pads standing on a FRAGMENT of their plane's fill - a piece the
    antipads round them (a 1.27 mm header's neighbours, a row of vias) cut off from the
    rest - on a board whose zones are filled: each needs its own via (fanout `only=`)."""
    import pcb
    out = []
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.IsFilled():
            continue
        net = z.GetNetname()
        if net not in (lay.get("fanout") or []):
            continue
        fill = pcb.shapely_of(z.GetFilledPolysList(z.GetLayer()))
        parts = sorted(getattr(fill, "geoms", [fill]), key=lambda g: -g.area)
        for frag in parts[1:]:
            for f in board.GetFootprints():
                for q in f.Pads():
                    c = Point(TO(q.GetPosition().x), TO(q.GetPosition().y))
                    if q.GetNetname() == net and frag.buffer(0.05).contains(c):
                        out.append(f"{f.GetReference()}.{q.GetNumber()}")
    return sorted(set(out))


def unfanned(board, lay):
    """Plane-net SMD pads with no track of their net ending on them - a part moved or
    added after the layout's fanout: each needs its via (fanout `only=`)."""
    nets = set(lay.get("fanout") or [])
    skip = {p for spec in lay.get("islands") or [] for p in spec.get("off_island", [])}
    tracks = [t for t in board.GetTracks() if type(t) is pcbnew.PCB_TRACK and t.GetNetname() in nets]
    out = []
    for f in board.GetFootprints():
        for q in f.Pads():
            name = f"{f.GetReference()}.{q.GetNumber()}"
            if q.GetNetname() not in nets or q.HasHole() or name in skip or f.IsNetTie():
                continue
            if any(h.HasHole() and h.GetNumber() == q.GetNumber() for h in f.Pads()):
                continue        # a plated hole's face pad (a mount's): the hole meets the plane
            if not any(t.GetNetname() == q.GetNetname() and (q.HitTest(t.GetStart()) or q.HitTest(t.GetEnd())) for t in tracks):
                out.append(name)
    return out


def moat_keepout(board, lay):
    """Over each island's moat, on the layer whose reference plane the island is (layer
    1 over layer 2), no track may cross but at the tie's window (a disc round the net
    tie, layout.yaml tie_window) and where the pairs already cross: a rule area, so
    the autorouter keeps off it and KiCad's DRC holds anyone who edits the board."""
    import pcb
    import pcb_main
    above = {"In1.Cu": "F.Cu", "In2.Cu": "B.Cu"}
    for spec in lay.get("islands") or []:
        p = Polygon(spec["outline"])
        ring = p.buffer(spec["moat"], join_style=2).difference(p.buffer(-0.05, join_style=2))
        for t_ in pcb_main.ties_of(spec):
            tie = board.FindFootprintByReference(t_)
            tx, ty = pcb_main.to_body(TO(tie.GetPosition().x), TO(tie.GetPosition().y))
            ring = ring.difference(Point(tx, ty).buffer(spec["tie_window"]))
        for x, y, r in spec.get("windows") or []:
            # a part that straddles the moat by design (the module's DAC): its pins' escapes
            ring = ring.difference(Point(x, y).buffer(r))
        for t in board.GetTracks():
            if type(t) is pcbnew.PCB_TRACK and t.GetNetname() in {n for pr in lay.get("pairs") or [] for n in pr["nets"]}:
                a, b = (pcb_main.to_body(TO(v.x), TO(v.y)) for v in (t.GetStart(), t.GetEnd()))
                ring = ring.difference(LineString([a, b]).buffer(TO(t.GetWidth()) / 2 + 0.6))
        pcb_main.rule_area(board, ring, f"{spec['net']} moat", [above[spec["layer"]]])


def escape(board, lay):
    """layout.yaml escape: [refs] - a fine-pitch part's pads (0.5-0.65 mm: an MSOP, a
    TSSOP) each get a short straight stub outward along the pad's long axis, past
    its end, so the grid router starts from copper it can leave: on the 0.2 mm grid a
    track in a 0.5 mm row has one legal line, the pad's own centre line, and the
    grid seldom lands on it. Plane-net pads already fanned and pads on no net are
    left; a stub that would come nearer another net than the clearance is left out.
    Idempotent: a pad with a track already ending on it is skipped. Locked."""
    obs = Obstacles(board, lay)
    w = lay["rules"]["track_min"]
    n = 0
    for ref in lay.get("escape") or []:
        fp = board.FindFootprintByReference(ref)
        fc = (TO(fp.GetPosition().x), TO(fp.GetPosition().y))
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net or net.startswith("unconnected") or pad.HasHole() or not pad.GetNumber():
                continue
            c = pad.GetPosition()
            if any(type(t) is pcbnew.PCB_TRACK and t.GetNetname() == net and (pad.HitTest(t.GetStart()) or pad.HitTest(t.GetEnd()))
                   for t in board.GetTracks()):
                continue
            L = "F" if pad.IsOnLayer(pcbnew.F_Cu) else "B"
            g = pad_geom_on(pad, pcbnew.F_Cu if L == "F" else pcbnew.B_Cu)
            x0, y0, x1, y1 = g.bounds
            cx, cy = TO(c.x), TO(c.y)
            if x1 - x0 >= y1 - y0:
                d = (1.0 if cx > fc[0] else -1.0, 0.0)
                reach = (x1 - x0) / 2
            else:
                d = (0.0, 1.0 if cy > fc[1] else -1.0)
                reach = (y1 - y0) / 2
            if abs(cx - fc[0]) < 0.05 and abs(cy - fc[1]) < 0.05:
                continue                    # the exposed pad
            end = (cx + d[0] * (reach + 0.6), cy + d[1] * (reach + 0.6))
            if not obs.track_ok((cx, cy), end, w, net, L):
                continue
            lay_track(board, obs, net, (cx, cy), end, w, L)
            n += 1
    print(f"route: escape - {n} stub(s) out of fine-pitch pads")


def prepare(board, lay):
    """A multi-layer board's own routing before the autorouter (tools/pcb.py
    `route: freerouting`): the pairs, then every plane net's fanout. Returns the report."""
    obs = Obstacles(board, lay)
    report = []
    import pcb
    for gd in lay.get("guards") or []:
        # a guard pour's own via (pcb_module: the module's SET guard), joining its faces
        for x, y in gd.get("vias") or []:
            lay_via(board, obs, gd["net"], *pcb.to_pcb(x, y))
    for spec in lay.get("pairs") or []:
        report += route_pair(board, lay, obs, spec)
    # the moat's keep-out before the fanout, so no other plane net's via lands in it
    moat_keepout(board, lay)
    obs = Obstacles(board, lay)
    report += fanout(board, lay, obs)
    # layout.yaml connect_first: on a multi-layer board too, each pad-to-pad connection
    # by its own track before anything else (a Kelvin sense, a decoupling loop, a rail's
    # own branch); pcb.py check holds each to its max_mm
    for spec in lay.get("connect_first") or []:
        pads = []
        for p_ in spec["pads"]:
            ref, num = p_.split(".")
            pads.append(board.FindFootprintByReference(ref).FindPadByNumber(num))
        if pads[0].GetNetname() != pads[1].GetNetname():
            sys.exit(f"pcb: connect_first {spec['pads']} are not on one net")
        at = [(TO(q.GetPosition().x), TO(q.GetPosition().y)) for q in pads]
        if complete(board, lay, [(pads[0].GetNetname(), at[0], at[1])]):
            report.append(f"connect_first {spec['pads'][0]} - {spec['pads'][1]} FAILED")
        else:
            for t in board.GetTracks():
                if t.GetNetname() == pads[0].GetNetname():
                    t.SetLocked(True)            # the autorouter and the rip-up keep it
            print(f"route: connect_first {spec['pads'][0]} - {spec['pads'][1]} ok")
    for r in report:
        print("route: " + r)
    return report
