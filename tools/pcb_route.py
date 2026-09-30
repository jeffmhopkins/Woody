"""A small two-layer grid router for simple boards - tools/pcb.py's `route: true`.

Not a general autorouter. It is enough for a key board: a handful of short
digital nets and one power rail, on a board whose ground is two poured planes.

A MULTI-LAYER BOARD (the main board, `route: freerouting`) takes only the
pieces at the end of this file from it, the ones an autorouter would get wrong:
each plane net's pad to its plane by its own via (`fanout`), a pair of nets
side by side (`route_pair`), and the moat's keep-out round an analog island
(`moat_keepout`). Freerouting routes the rest (tools/pcb_freeroute.py).

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
AGAINST = 0.35
TOP, BOT = 0, 1
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]
MM, TO = pcbnew.FromMM, pcbnew.ToMM


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
            tracks = [t for t in self.board.GetTracks() if type(t) is pcbnew.PCB_TRACK]
            # 1. a branch ending in the middle of a track: split the track there
            for t in tracks:
                for e in (t.GetStart(), t.GetEnd()):
                    for u in tracks:
                        if u is t or u.GetNetname() != t.GetNetname() or u.GetLayer() != t.GetLayer():
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
                        ax, ay, bx, by = fa.x - px, fa.y - py, fb.x - px, fb.y - py
                        la, lb = math.hypot(ax, ay), math.hypot(bx, by)
                        if not la or not lb or (ax * bx + ay * by) / (la * lb) <= math.cos(math.radians(89.5)):
                            continue
                        if acute_closed(self.board, net, layer, (px, py), (ax, ay), (bx, by), max(ta.GetWidth(), tb.GetWidth())):
                            continue
                        k = (ax * bx + ay * by) / (la * la)      # the foot of fb's perpendicular on P->fa
                        if not 0.02 < k < 0.98:
                            continue
                        X = pcbnew.VECTOR2I(int(px + k * ax), int(py + k * ay))
                        L = LAYERS.index(layer)
                        seg = LineString([(TO(X.x), TO(X.y)), (TO(fb.x), TO(fb.y))])
                        body = seg.buffer(TO(tb.GetWidth()) / 2)
                        g = seg.buffer(TO(tb.GetWidth()) / 2 + self.clear)
                        if any(n != net and L in ls and g.intersects(o) for (n, ls, o, _) in self.copper) \
                                or any(body.intersects(h) for h in self.holes) or not self.inside.contains(body):
                            continue
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


def merge_tracks(board):
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
            board.Remove(b)
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
                    self.items.append((c.buffer(TO(pad.GetDrillSize().x) / 2), "", {"F", "B"},
                                       "npth" if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else "hole"))
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    continue
                for L, lid in (("F", pcbnew.F_Cu), ("B", pcbnew.B_Cu)):
                    if pad.IsOnLayer(lid):
                        self.items.append((pad_geom_on(pad, lid), pad.GetNetname(), {L}, "pad" if pad.HasHole() else "smd"))
        for z in board.Zones():
            if z.GetIsRuleArea() and (z.GetDoNotAllowVias() or z.GetDoNotAllowTracks()):
                ls = {k for k, lid in (("F", pcbnew.F_Cu), ("B", pcbnew.B_Cu)) if z.IsOnLayer(lid)}
                for i in range(z.Outline().OutlineCount()):
                    o = z.Outline().Outline(i)
                    self.items.append((Polygon([(TO(o.CPoint(k).x), TO(o.CPoint(k).y)) for k in range(o.PointCount())]),
                                       None, ls, "keepout"))
        silk = [d for d in board.GetDrawings() if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
        for fp in board.GetFootprints():
            silk += [g for g in fp.GraphicalItems() if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
        for it in silk:
            bb = it.GetBoundingBox()
            self.items.append((box(TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom())), None,
                               {"F" if it.GetLayer() == pcbnew.F_SilkS else "B"}, "silk"))
        for t in board.GetTracks():
            self.add_item(t)
        self.outline = board_outline_with_holes(board)
        from shapely.prepared import prep
        self.inner = prep(self.outline.buffer(-self.edge))
        self._tree = None

    def add(self, geom, net, layers, kind):
        self.items.append((geom, net, layers, kind))
        self._tree = None

    def add_item(self, t):
        """A track or via already on the board, as an obstacle."""
        if isinstance(t, pcbnew.PCB_VIA):
            c = Point(TO(t.GetPosition().x), TO(t.GetPosition().y))
            self.add(c.buffer(TO(t.GetWidth(pcbnew.F_Cu)) / 2, 16), t.GetNetname(), {"F", "B"}, "via")
            self.add(c.buffer(TO(t.GetDrillValue()) / 2, 16), t.GetNetname(), {"F", "B"}, "vhole")
        elif t.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
            a, b = t.GetStart(), t.GetEnd()
            g = LineString([(TO(a.x), TO(a.y)), (TO(b.x), TO(b.y))]).buffer(TO(t.GetWidth()) / 2, 8) \
                if (a.x, a.y) != (b.x, b.y) else Point(TO(a.x), TO(a.y)).buffer(TO(t.GetWidth()) / 2)
            self.add(g, t.GetNetname(), {"F" if t.GetLayer() == pcbnew.F_Cu else "B"}, "track")

    def near(self, g, pad=1.0):
        from shapely.strtree import STRtree
        if self._tree is None:
            self._tree = STRtree([it[0] for it in self.items])
        return [self.items[i] for i in self._tree.query(g.buffer(pad))]

    def via_ok(self, x, y, net):
        """A via of `net` at (x, y): its copper clear of every other net by the clearance,
        off every SMD pad (its own net's too: a via in a pad wicks its solder), its hole
        the board house's hole-to-hole from every other, off silkscreen and keep-outs,
        and inside the board by the edge clearance."""
        v = Point(x, y).buffer(self.via / 2, 16)
        if not self.inner.contains(v):
            return False
        hole = Point(x, y).buffer(self.drill / 2, 16)
        for g, n, ls, kind in self.near(v):
            if kind in ("hole", "vhole", "npth"):
                gap = self.h2h if kind != "vhole" else max(self.h2h, self.clear)
                if g.distance(hole) < gap - 1e-6 or (kind == "npth" and g.distance(v) < self.hclear):
                    return False
            elif kind in ("keepout", "silk"):
                if g.intersects(v):
                    return False
            elif kind == "smd" and n == net:
                if g.distance(v) < OWN_PAD_GAP:
                    return False
            elif n != net and g.distance(v) < self.clear - 1e-6:
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
        out[spec["net"]] = p
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
    t.SetLayer(pcbnew.F_Cu if layer == "F" else pcbnew.B_Cu)
    t.SetNet(board.FindNet(net))
    t.SetLocked(locked)
    board.Add(t)
    obs.add_item(t)
    return t


def fanout(board, lay, obs):
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
            if net not in (lay.get("fanout") or []) or pad.HasHole() or name in skip:
                continue
            if any(q.HasHole() and q.GetNumber() == pad.GetNumber() for q in fp.Pads()):
                continue            # a plated hole's face pad (a mount's): the hole meets the plane
            L = "F" if pad.IsOnLayer(pcbnew.F_Cu) else "B"
            pg = pad_geom_on(pad, pcbnew.F_Cu if L == "F" else pcbnew.B_Cu)
            c = pg.centroid
            region = regions[net].buffer(-(obs.via / 2 + 0.3))
            fc = Point(TO(fp.GetPosition().x), TO(fp.GetPosition().y))
            away = math.atan2(c.y - fc.y, c.x - fc.x) if fc.distance(c) > 0.05 else 0.0
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
                continue
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
                for g, n, ls, kind in self.obs.near(p, self.rad):
                    if self.L not in ls or kind in ("silk", "hole", "vhole") or (n in self.own and kind != "keepout"):
                        continue
                    if g.distance(p) < self.rad:
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
    return report


def tidy(board, lay):
    """After an autorouter: what it leaves that the checks fail - zero-length and
    duplicated tracks, tracks with an end that reaches nothing of their net (dangling),
    two tracks of a net meeting at under 90 degrees (square_joins, as on a key board),
    and collinear runs in pieces (merge_tracks)."""
    key = lambda v: (v.x, v.y)
    n0 = n1 = n2 = 0
    seen = set()
    for t in [t for t in board.GetTracks() if type(t) is pcbnew.PCB_TRACK]:
        k = (t.GetNetname(), t.GetLayer(), t.GetWidth()) + tuple(sorted([key(t.GetStart()), key(t.GetEnd())]))
        if t.GetStart() == t.GetEnd() or k in seen:
            board.Delete(t)         # Delete, not Remove: a Remove from a LOADED board crashes the next walk of it
            n0 += 1
            continue
        seen.add(k)
    # dangling ends, repeatedly: an end touches another track of the net (its end or its
    # body), a via of the net, or a pad of the net on its layer - or it goes
    pads = [(p, p.GetNetname()) for fp in board.GetFootprints() for p in fp.Pads()]
    while True:
        tracks = [t for t in board.GetTracks() if type(t) is pcbnew.PCB_TRACK]
        vias = [v for v in board.GetTracks() if isinstance(v, pcbnew.PCB_VIA)]
        gone = []
        for t in tracks:
            if t.IsLocked():
                continue
            for e in (t.GetStart(), t.GetEnd()):
                net, L = t.GetNetname(), t.GetLayer()
                ok = any(u is not t and u.GetNetname() == net and u.GetLayer() == L and u.HitTest(e, 1000) for u in tracks) \
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
    # a via that nothing reaches but its own plane is a plane via; one with no plane and
    # nothing on either face is debris
    r = Router(board, lay)
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            c = Point(TO(t.GetPosition().x), TO(t.GetPosition().y))
            r.copper.append((t.GetNetname(), {TOP, BOT}, c.buffer(TO(t.GetWidth(pcbnew.F_Cu)) / 2), "track"))
        elif t.GetLayer() in LAYERS:
            a, b = t.GetStart(), t.GetEnd()
            g = LineString([(TO(a.x), TO(a.y)), (TO(b.x), TO(b.y))]).buffer(TO(t.GetWidth()) / 2)
            r.copper.append((t.GetNetname(), {LAYERS.index(t.GetLayer())}, g, "track"))
    n2 = r.square_joins()
    n3 = merge_tracks(board)
    print(f"route: tidy - {n0} empty or doubled track(s), {n1} dangling, {n2} acute join(s) squared, {n3} joint(s) merged")


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
        tie = board.FindFootprintByReference(spec["tie"])
        tx, ty = pcb_main.to_body(TO(tie.GetPosition().x), TO(tie.GetPosition().y))
        ring = ring.difference(Point(tx, ty).buffer(spec["tie_window"]))
        for t in board.GetTracks():
            if type(t) is pcbnew.PCB_TRACK and t.GetNetname() in {n for pr in lay.get("pairs") or [] for n in pr["nets"]}:
                a, b = (pcb_main.to_body(TO(v.x), TO(v.y)) for v in (t.GetStart(), t.GetEnd()))
                ring = ring.difference(LineString([a, b]).buffer(TO(t.GetWidth()) / 2 + 0.6))
        pcb_main.rule_area(board, ring, f"{spec['net']} moat", [above[spec["layer"]]])


def prepare(board, lay):
    """A multi-layer board's own routing before the autorouter (tools/pcb.py
    `route: freerouting`): the pairs, then every plane net's fanout. Returns the report."""
    obs = Obstacles(board, lay)
    report = []
    for spec in lay.get("pairs") or []:
        report += route_pair(board, lay, obs, spec)
    report += fanout(board, lay, obs)
    moat_keepout(board, lay)
    for r in report:
        print("route: " + r)
    return report
