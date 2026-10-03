#!/usr/bin/env python3
"""The Matrix's routes on the right-hand key board, drawn by hand (2026-10-03).

    python3 hardware/boards/key-board-rh/matrix_routes.py

WHY THIS EXISTS. tools/pcb_route.py cannot fan J2 (J-MCU-KB, a 2x12 1.27 mm
through-hole header) out on two layers: its pads are 0.2 mm apart along each
row, so every pin leaves its row outward only, and the router closed the way
round the header's ends after about fifteen nets in every order tried.
Freerouting left a few and adds no pours. tools/ is not changed for this one
header. Instead this script runs `tools/pcb.py layout` for the board with
J2-J5's nets held out of the router and the routes below kept clear of it,
then draws the routes below into the board before it is saved, poured and
checked. Re-running it re-makes the board from layout.yaml, as `pcb.py layout
--force` would. The .kicad_pcb is the source afterwards (ADR 0019).

THE ROUTES, in body coordinates (x along the body from the mouth, y across,
mm), all 0.25 mm on 0.7 mm lanes, so two lanes stay 0.45 apart even on a
45-degree run (0.7 / sqrt 2 = 0.495 centre to centre):
- J2's odd row leaves its back (-x) and its even row its front (+x); no
  track fits between its pads.
- Far rail (J4, the IO33..RX row): the odd pins on the bottom face in nested
  Ls round the header's high end, the even pins (IO33, RX) on the top face;
  between the header and the tail column they pass the column's keep-out on
  its near side, then run along the rail. Each net ends in a via over its J4
  pin's column and drops to the pin on the top face, so the lanes need no
  particular order.
- Near rail (J3, the 5V..IO1 row, and J5's wire pads): the even pins and EN
  on the bottom face in nested Ls round the header's low end, IO7 and IO1 on
  the top face, changing to the bottom past the corridor; along the rail all
  nine are bottom-face lanes between J5's row and J3's, each ending in a via
  and rising to J3 or dropping to J5 on the top face.
- The Matrix's grounds (J2 10, 14, 16, 23; J3 2; J5 2) are on the board's
  GND_CHAIN pours, which reach each of them on the top face.
"""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import pcb  # noqa: E402
import pcb_route  # noqa: E402
import pcbnew  # noqa: E402
from shapely.geometry import LineString, Point  # noqa: E402

BDIR = os.path.join(ROOT, "hardware", "boards", "key-board-rh")
HELD = ("J2", "J3", "J4", "J5")      # the Matrix's parts: their nets are routed here
TW = 0.25                             # track
P = 0.7                               # lane pitch
C = 0.5                               # 45-degree corner
VIA, DRILL = 0.7, 0.3                 # layout.yaml rules: via, via_drill
KEEP = TW / 2 + 0.2 + 0.1             # what the router keeps from a route: half a track, the clearance, slack
F, B = "F", "B"

# J2's pins (layout.yaml J2: pin 1 at (242.3, 21.515), its odd row at x 242.3, even at 243.57)
def j2(k):
    return (242.3 if k % 2 else 243.57, 21.515 + ((k - 1) // 2) * 1.27)

J3 = lambda n: (272.97 + (n - 1) * 2.54, 17.07)     # layout.yaml J3, the 5V..IO1 row
J4 = lambda n: (272.97 + (n - 1) * 2.54, 39.93)     # layout.yaml J4, the IO33..RX row
J5 = lambda n: (284.0 + (n - 1) * 2.54, 8.7)        # layout.yaml J5, the wire pads: a 1x4 2.54 mm pin footprint


def routes():
    """[(net, layer, [points])], [(net, point)] - every track and via, body frame."""
    T, V = [], []

    def via(net, p):
        V.append((net, p))

    # ---- FAR RAIL, odd pins on the bottom face: nested Ls up round the header's high end
    far_odd = [(17, "/IO38", 6), (15, "/IO35", 3), (13, "/IO36", 4), (11, "/IO34", 2),
               (9, "/IO39", 7), (7, "/IO37", 5), (5, "/IO40", 8), (3, "/U0TXD", 9)]
    for j, (k, net, n) in enumerate(far_odd):
        x0, y0 = j2(k)
        xt, yh = 240.6 - P * j, 36.6 + P * j
        y1, y2 = 39.3 + P * j, 41.4 + P * j
        xn = J4(n)[0]
        T.append((net, B, [(x0, y0), (xt + C, y0), (xt, y0 + C), (xt, yh - C), (xt + C, yh), (248.8, yh),
                           (248.8 + (y1 - yh), y1), (253.0, y1), (253.0 + (y2 - y1), y2), (xn, y2)]))
        via(net, (xn, y2))
        T.append((net, F, [(xn, y2), J4(n)]))
    # ---- FAR RAIL, the even pins IO33 and RX on the top face, nested up the header's front
    x0, y0 = j2(6)       # IO33 -> J4.1
    T.append(("/IO33", F, [(x0, y0), (247.7, y0), (248.2, y0 + C), (248.2, 39.4), (248.7, 39.9), (251.3, 39.9),
                            (259.2, 47.8), (J4(1)[0], 47.8), J4(1)]))
    x0, y0 = j2(4)       # RX (IO44) -> J4.10, on the bottom face along the rail above the others
    T.append(("/U0RXD", F, [(x0, y0), (248.3, y0), (248.8, y0 + C), (248.8, 38.7), (249.3, 39.2), (252.0, 39.2),
                             (259.8, 47.0)]))
    via("/U0RXD", (259.8, 47.0))
    T.append(("/U0RXD", B, [(259.8, 47.0), (J4(10)[0], 47.0)]))
    via("/U0RXD", (J4(10)[0], 47.0))
    T.append(("/U0RXD", F, [(J4(10)[0], 47.0), J4(10)]))

    # J2's three front-row grounds (10, 14, 16) tied on the top face, beside the pins,
    # where the pour between the row and IO33's rise reaches them
    xg = 244.95
    T.append(("GND_CHAIN", F, [j2(10), (xg, j2(10)[1]), (xg, j2(16)[1]), j2(16)]))
    T.append(("GND_CHAIN", F, [j2(14), (xg, j2(14)[1])]))
    # ... and down to the bottom face's pocket beside them, which no other way reaches
    via("GND_CHAIN", (245.3, j2(10)[1]))
    T.append(("GND_CHAIN", F, [(xg, j2(10)[1]), (245.3, j2(10)[1])]))
    # ---- NEAR RAIL. Corridor order on the bottom face, low y up: EN, IO0, 5V (pin 8),
    # 3V3, IO3, IO2, 5V (pins 22 and 24); then nine bottom-face lanes on the rail.
    band = [15.47 - 0.69 * i for i in range(9)]    # rail lanes, top down: 15.47 .. 9.95, between J3's pads and J5's
    near = [  # (net, J2 pin, vertical x, corridor y, rail lane, target, to J3 (up) or J5 (down))
        ("/INST_5V_A", 22, 248.5, 19.6, 0, J3(1)),
        ("/IO2", 20, 247.8, 18.9, 1, J3(9)),
        ("/IO3", 18, 247.1, 18.2, 2, J3(8)),
        ("/DEV_3V3", 12, 246.4, 17.5, 3, J3(3)),
        ("/INST_5V_A", 8, 245.7, 16.8, 4, J5(1)),
        ("/IO0", 2, 245.0, 16.1, 5, J5(4)),
        ("/EN", 1, 242.3, 15.4, 6, J5(3)),
    ]
    for net, k, xv, yc, lane, tgt in near:
        x0, y0 = j2(k)
        yr = band[lane]
        yd = yc - 2.1                               # past the corridor, on the rail
        pts = [(x0, y0)] if k == 1 else [(x0, y0), (xv - C, y0), (xv, y0 - C)]
        pts += [(xv, yc + C), (xv + C, yc), (249.5, yc), (251.6, yd), (263.0, yd), (263.0 + (yd - yr), yr), (tgt[0], yr)]
        T.append((net, B, pts))
        via(net, (tgt[0], yr))
        T.append((net, F, [(tgt[0], yr), tgt]))
    # pin 24 is 5V too: straight onto pin 22, its neighbour in the row
    T.append(("/INST_5V_A", B, [j2(24), j2(22)]))
    # the two 5V lanes (pin 8's, and pins 22 and 24's) joined on the top face where
    # the rail starts, past IO7's and IO1's crossings and before the lanes fan to the band
    ya, yb = near[4][3] - 2.1, near[0][3] - 2.1
    via("/INST_5V_A", (262.0, ya))
    via("/INST_5V_A", (262.0, yb))
    T.append(("/INST_5V_A", F, [(262.0, ya), (262.0, yb)]))
    # J3.2, the Matrix's pad-row ground: down the top face between J3.1's riser and
    # J5.1's drop, to a via into the bottom face's pour under the lanes
    T.append(("GND_CHAIN", F, [J3(2), (274.2, J3(2)[1] - (J3(2)[0] - 274.2)), (274.2, 9.0)]))
    via("GND_CHAIN", (274.2, 9.0))
    # the bottom face's strip between the lanes and J3's row, which J3.2 alone reaches,
    # tied to the top face's pour
    via("GND_CHAIN", (284.4, 15.6))
    # IO7 and IO1 leave the odd row on the top face, nested down its back, under the
    # header's low end, then cross to the bottom face below the others' lanes
    for net, k, xv, yc, lane, tgt, xvia in (("/IO7", 19, 240.7, 19.4, 7, J3(4), 259.0),
                                             ("/IO1", 21, 240.1, 18.7, 8, J3(10), 260.2)):
        x0, y0 = j2(k)
        yr = band[lane]
        xd = 249.5 + (yc - yr)                      # where the 45-degree run from 249.5 reaches the lane
        T.append((net, F, [(x0, y0), (xv + C, y0), (xv, y0 - C), (xv, yc + C), (xv + C, yc), (249.5, yc), (xd, yr), (xvia, yr)]))
        via(net, (xvia, yr))
        T.append((net, B, [(xvia, yr), (tgt[0], yr)]))
        via(net, (tgt[0], yr))
        T.append((net, F, [(tgt[0], yr), tgt]))
    return T, V


def to_pcb(p):
    return pcb.to_pcb(*p)


def rule_area(board, poly):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.B_Cu)
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowCopperPour(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in list(poly.exterior.coords)[:-1]:
        ol.Append(pcb.MM(x), pcb.MM(y))
    board.Add(z)
    return z


def draw(board):
    T, V = routes()
    lid = {F: pcbnew.F_Cu, B: pcbnew.B_Cu}
    for net, layer, pts in T:
        ni = board.FindNet(net)
        assert ni is not None, net
        for a, b in zip(pts, pts[1:]):
            if math.dist(a, b) < 1e-6:
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcb.V(*to_pcb(a)))
            t.SetEnd(pcb.V(*to_pcb(b)))
            t.SetWidth(pcb.MM(TW))
            t.SetLayer(lid[layer])
            t.SetNet(ni)
            board.Add(t)
    for net, p in V:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcb.V(*to_pcb(p)))
        v.SetWidth(pcb.MM(VIA))
        v.SetDrill(pcb.MM(DRILL))
        v.SetNet(board.FindNet(net))
        board.Add(v)


def keepouts(board):
    T, V = routes()
    zs = []
    for _, _, pts in T:
        zs.append(rule_area(board, LineString([to_pcb(p) for p in pts]).buffer(KEEP, cap_style=2, join_style=2)))
    for _, p in V:
        zs.append(rule_area(board, Point(*to_pcb(p)).buffer(VIA / 2 + 0.2 + 0.1, 16)))
    return zs


_route = pcb_route.route


def route(board, lay):
    """pcb_route.route with the Matrix's parts' nets held out and their routes kept clear;
    then the routes drawn."""
    held = {}
    for ref in HELD:
        for pad in board.FindFootprintByReference(ref).Pads():
            held[(ref, pad.GetNumber())] = pad.GetNetCode()
            pad.SetNetCode(0)
    zs = keepouts(board)
    failed = _route(board, lay)
    for z in zs:
        board.Remove(z)
    for (ref, num), code in held.items():
        for pad in board.FindFootprintByReference(ref).Pads():
            if pad.GetNumber() == num:
                pad.SetNetCode(code)
    draw(board)
    return failed


def silk_on_board(path):
    """A silkscreen reference the tool put over the rails' open middle goes onto its
    part's own rail, beside its pin row's mouth end."""
    board = pcbnew.LoadBoard(path)
    ol = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(ol)
    moved = []
    for d in board.GetDrawings():
        if not isinstance(d, pcbnew.PCB_TEXT) or d.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        if ol.Contains(d.GetPosition()):
            continue
        txt = d.GetText()
        where = {"J3": (269.0, 15.6), "J4": (269.0, 41.4)}.get(txt)
        if where is None:
            continue
        d.SetPosition(pcb.V(*to_pcb(where)))
        moved.append(txt)
    pcbnew.SaveBoard(path, board)
    return moved


if __name__ == "__main__":
    pcb_route.route = route
    rc = pcb.cmd_layout(BDIR, True, True) or 0
    if not rc:
        out = os.path.join(BDIR, "key-board-rh.kicad_pcb")
        print("matrix_routes: silk moved onto the board:", silk_on_board(out))
        pcb._fill(out)
    sys.exit(rc)
