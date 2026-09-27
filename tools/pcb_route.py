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
  * Then every net is ripped up and routed again with all the others in
    place, in the same order, and the new route kept if it is cheaper: the
    first pass routes early nets round an empty board, and they are the ones
    that wander.
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
        self.holes = []             # geometry of every drilled hole (any net or none)
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
                if pad.HasHole():
                    self.holes.append(Point(TO(pad.GetPosition().x), TO(pad.GetPosition().y)).buffer(TO(pad.GetDrillSize().x) / 2))
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
            obst += self.holes if via else [h for h in self.holes]
            rad = half + self.clear + SLACK
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
            self.holes.append(hole)

    def rip_up(self, net):
        """Remove every track and via this net's routes added; returns them for put_back."""
        rec = self.owned.pop(net, [])
        for item, copper, hole in rec:
            self.board.Remove(item)
            # by identity: two entries can be equal geometry
            if copper is not None:
                self.copper = [c for c in self.copper if c is not copper]
            if hole is not None:
                self.holes = [h for h in self.holes if h is not hole]
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
        # merge collinear runs on one layer
        segs, start = [], 0
        for k in range(1, len(pts) + 1):
            if k == len(pts) or pts[k][0] != pts[start][0]:
                run = pts[start:k]
                simp = [run[0]]
                for p in run[1:-1]:
                    a, b = simp[-1], p
                    nxt = run[run.index(p) + 1]
                    if (b[1] - a[1]) * (nxt[2] - b[2]) - (b[2] - a[2]) * (nxt[1] - b[1]) != 0:
                        simp.append(p)
                if len(run) > 1:
                    simp.append(run[-1])
                for a, b in zip(simp, simp[1:]):
                    segs.append((a[0], (a[1], a[2]), (b[1], b[2])))
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

    def pad_stub(self, net, pad_geom_, L, cell, width):
        """A short track from the pad's centre to the cell the path started or ended in."""
        c = pad_geom_.centroid
        x, y = self.cell_xy(*cell)
        if math.hypot(c.x - x, c.y - y) < 1e-6:
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
            self.pad_stub(net, g, path[-1][0], path[-1][1:], width)
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
                self.pad_stub(net, g, path[-1][0], path[-1][1:], width)
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
            best = None
            for r in range(3, 20):
                for a in range(0, 360, 20):
                    x, y = c.x + r * GRID * math.cos(math.radians(a)), c.y + r * GRID * math.sin(math.radians(a))
                    i, j = round((x - self.x0) / GRID), round((y - self.y0) / GRID)
                    if 0 <= i < self.nx and 0 <= j < self.ny and not vgrid[0][i][j] and not vgrid[1][i][j] \
                            and self.stub_clear(gnd, next(iter(ls)), (c.x, c.y), self.cell_xy(i, j)):
                        best = (i, j)
                        break
                if best:
                    break
            if not best:
                continue
            L = next(iter(ls))
            self.commit(gnd, [(L, *best), (1 - L, *best)], self.w)
            self.pad_stub(gnd, g, L, best, self.w)
            vgrid = self.blocked(gnd, self.w, via=True)
            n += 1
        return n

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
    # shortest nets first: they have the fewest ways round
    def span(n):
        gs = [g for (nn, _, g, _) in r.copper if nn == n]
        xs = [g.centroid.x for g in gs]
        ys = [g.centroid.y for g in gs]
        return (max(xs) - min(xs)) + (max(ys) - min(ys)) if len(gs) > 1 else 0
    order = sorted(nets, key=lambda n: (n in power, span(n)))
    failed = []
    for n in order:
        ok = r.route_net(n, r.pw if n in power else r.w)
        print(f"route: {n:20s} {'ok' if ok else 'FAILED'}")
        if not ok:
            failed.append(n)
    # Rip up and reroute: each net again, with every other net in place. A
    # net that now fails, or comes back dearer, gets its old route back.
    for rnd in range(2):
        better = 0
        for n in order:
            before = r.cost(n)
            old = r.rip_up(n)
            ok = r.route_net(n, r.pw if n in power else r.w)
            if ok and (n in failed or r.cost(n) < before - 0.05):
                better += 1
                if n in failed:
                    failed.remove(n)
            else:
                r.rip_up(n)
                r.put_back(n, old)
        print(f"route: reroute pass {rnd + 1}: {better} net(s) improved")
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
    r.pour(gnd)
    return failed


def fill_zones(path):
    """Fill every zone of a SAVED board, in its own load: filling the board the router
    just built in memory crashes KiCad 9's Python (no connectivity yet), silently."""
    board = pcbnew.LoadBoard(path)
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(path, board)
