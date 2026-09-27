"""A small two-layer grid router for simple boards - tools/pcb.py's `route: true`.

Not a general autorouter, and not meant for the main board (ADR 0017's analog
return rules want a hand; docs/reference/pcb-pipeline.md). It is enough for a
key board: a handful of short digital nets and one power rail, on a board
whose ground is two poured planes.

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
    every single-sided GND pad a stitching via into the other plane.
  * Every track, via and zone is written to the board, zones are filled, and
    tools/pcb.py's `check` runs KiCad's DRC over the result - the router
    proves nothing about itself; the DRC does.
"""
import heapq
import math

import pcbnew
from shapely.geometry import Point, Polygon, box
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
    # chain the segments into one ring
    pts = [(segs[0][0], segs[0][1]), (segs[0][2], segs[0][3])]
    rest = segs[1:]
    while rest:
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
            raise SystemExit("route: board outline is not one closed ring")
    return Polygon(pts)


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
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                net = pad.GetNetname()
                layers = {L for L, lid in enumerate(LAYERS) if pad.IsOnLayer(lid)}
                g = pad_geom(pad)
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    self.holes.append(g)
                    continue
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
        self.inside = self.outline.buffer(-self.edge)

    def cell_xy(self, i, j):
        return (self.x0 + i * GRID, self.y0 + j * GRID)

    def blocked(self, net, width, via=False):
        """A boolean grid per layer: True where this net cannot put a track (or a via) centre."""
        half = (self.via / 2 if via else width / 2)
        grids = [[[False] * self.ny for _ in range(self.nx)] for _ in (TOP, BOT)]
        for L in (TOP, BOT):
            obst = [g for (n, ls, g, _) in self.copper if L in ls and n != net]
            obst += self.holes + (self.pth_holes if via else [])
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
        tree = {(L, i, j) for L in pads[0][1] for (i, j) in pads[0][2]}
        todo = pads[1:]
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
            _, ls, cells, g = todo.pop(idx)
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
        """Every single-layer GND pad gets a via into the other layer's plane, beside it."""
        vgrid = self.blocked(gnd, self.w, via=True)
        n = 0
        for (_, ls, cells, g) in self.pad_cells(gnd):
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
            # a pad the ground route already reaches does not need the via at any
            # angle - it only adds a parallel path; one with no track takes any spot
            best = best or (fallback if not leave else None)
            if not best:
                continue
            self.commit(gnd, [(L, *best), (1 - L, *best)], self.w)
            self.pad_stub(gnd, g, L, best, self.w)
            vgrid = self.blocked(gnd, self.w, via=True)
            n += 1
        return n

    def square_joins(self):
        """Where a route joined the tree at one of its bends at under 90 degrees,
        the wedge between the two is an acid trap. Move the joining track's end
        along the other track to the foot of the perpendicular from its far end,
        and split that track there: the join becomes a right-angle T. Only where
        the moved track keeps its clearance to every other net's copper."""
        from shapely.geometry import LineString
        fixed = 0
        for _ in range(20):
            again = False
            tracks = [t for t in self.board.GetTracks() if type(t) is pcbnew.PCB_TRACK]
            ends = {}
            for t in tracks:
                for e, o in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
                    ends.setdefault((t.GetNetname(), t.GetLayer(), e.x, e.y), []).append((t, o))
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
                        k = (ax * bx + ay * by) / (la * la)      # the foot of fb's perpendicular on P->fa
                        if not 0.02 < k < 0.98:
                            continue
                        X = pcbnew.VECTOR2I(int(px + k * ax), int(py + k * ay))
                        L = LAYERS.index(layer)
                        g = LineString([(TO(X.x), TO(X.y)), (TO(fb.x), TO(fb.y))]).buffer(TO(tb.GetWidth()) / 2 + self.clear)
                        if any(n != net and L in ls and g.intersects(o) for (n, ls, o, _) in self.copper):
                            continue
                        if tb.GetStart().x == px and tb.GetStart().y == py:
                            tb.SetStart(X)
                        else:
                            tb.SetEnd(X)
                        a2 = pcbnew.PCB_TRACK(self.board)
                        a2.SetStart(X)
                        a2.SetEnd(fa)
                        a2.SetWidth(ta.GetWidth())
                        a2.SetLayer(layer)
                        a2.SetNet(ta.GetNet())
                        if ta.GetStart().x == px and ta.GetStart().y == py:
                            ta.SetEnd(X)
                        else:
                            ta.SetStart(X)
                        self.board.Add(a2)
                        fixed += 1
                        again = True
                        break
                    if again:
                        break
                if again:
                    break
            if not again:
                break
        return fixed

    def pour(self, gnd):
        for L in (TOP, BOT):
            z = pcbnew.ZONE(self.board)
            z.SetLayer(LAYERS[L])
            z.SetNet(self.board.FindNet(gnd))
            z.SetLocalClearance(MM(self.clear))
            z.SetMinThickness(MM(0.25))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
            z.SetThermalReliefGap(MM(0.3))
            z.SetThermalReliefSpokeWidth(MM(0.4))
            ol = z.Outline()
            ol.NewOutline()
            minx, miny, maxx, maxy = self.outline.bounds
            for x, y in list(self.outline.exterior.coords)[:-1]:
                ol.Append(MM(x), MM(y))
            z.SetIsFilled(False)
            self.board.Add(z)


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
