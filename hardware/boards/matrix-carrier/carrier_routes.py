#!/usr/bin/env python3
"""The Matrix carrier's routes, drawn by hand (2026-10-03).

    python3 hardware/boards/matrix-carrier/carrier_routes.py

WHY BY HAND. The owner asked for an orderly bus, not the autorouter's diagonals,
and one thing makes a plain bus impossible: J-MCU-C's pin order. Its back row
(the odd pins) can leave only toward the board's near edge, so any one-layer
path from it to the Matrix's far pad row (J3) arrives in its pins' order
reversed, and J3 wants them in another order again. The bus therefore runs
in two layers with ONE ladder where the order is changed:

- J-MCU-C's back row leaves toward the near edge, five lines a face (the
  1.27 mm rows have 0.2 between pads); its front row leaves the other way, on
  the top face. Past the header the bottom-face lines fan up, and the top-face
  ones step through a diagonal of vias onto the bottom face.
- Along the near strip, the bus is TWELVE BOTTOM-FACE LINES at 0.7 mm (a via
  fits between any two), and each turns north in turn, at 45 degrees, into a
  column beside the USB-C slot.
- THE LADDER: each column ends in a via at its own height, and a top-face
  run takes it across to the J2 or J3 pad it is for, then straight into
  that pad. The rows are stacked so that no run crosses a column still
  climbing beside it. The four lines for the J3 pads over the slot step west
  together once the rest have left, then run over the slot's end.
- 5V and 3V3 go straight from J-MCU-C to J2 on the top face, 0.4 mm wide;
  J-MCU-C's third 5V pin joins them through a via. Ground runs the same way,
  0.4 mm, from J-MCU-C's pin 10 into the Matrix's ground pad. IO7 and IO1 run along the
  near edge to J2's pads from below; IO1 passes under the near mount.
- PWR_GND is poured on both faces (layout.yaml planes) and stitched.

Re-running re-makes the board from layout.yaml (as pcb.py layout --force)
with these routes drawn before the planes are filled and the silkscreen is
placed; nothing is left to the autorouter. The .kicad_pcb is the source
afterwards (ADR 0019). Body frame throughout: x along the body from the mouth,
y across from the near side, mm.
"""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import pcb  # noqa: E402
import pcb_route  # noqa: E402
import pcbnew  # noqa: E402

BDIR = os.path.join(ROOT, "hardware", "boards", "matrix-carrier")
F, B = "F", "B"
TW, PW = 0.25, 0.4            # signal and power track (layout.yaml rules)
VIA, DRILL = 0.7, 0.3
C = 0.5                       # 45-degree corner


# J-MCU-C (J1): pin 1 at the header's tail end, its back row (odd) nearer the board's edge
def j1(k):
    i = (k - 1) // 2
    return (269.255 - 1.27 * i, 11.385 if k % 2 else 12.655)


def j2(n):                    # HDR-MATRIX 5V..IO1: staggered feet, odd pins toward the slot
    return (272.97 + 2.54 * (n - 1), 18.67 if n % 2 else 15.47)


def j3(n):                    # HDR-MATRIX IO33..RX: odd pins away from the slot
    return (272.97 + 2.54 * (n - 1), 41.53 if n % 2 else 38.33)


def j2_in(n):                 # a point inside J2 pad n, on the side a track comes in by
    x, y = j2(n)
    return (x, y)


def j3_in(n):
    x, y = j3(n)
    return (x, y - 0.8 if n % 2 == 0 else y - 0.5)


T, V = [], []                 # (net, layer, points, width), (net, point)


def track(net, layer, pts, w=TW):
    T.append((net, layer, pts, w))


def via(net, p):
    V.append((net, p))


def down(k, y):
    """A back-row pin straight down to its lane, a 45-degree corner, then toward the tail."""
    x, y0 = j1(k)
    return [(x, y0), (x, y + C), (x + C, y)]


def up(k, y):
    x, y0 = j1(k)
    return [(x, y0), (x, y - C), (x + C, y)]


# ---- J-MCU-C's back row, down to five lanes a face under it ------------------------
LANES = [9.95, 9.45, 8.95, 8.45, 7.95]
# Bottom face: TX, IO40, IO37, IO39 fan up past the header to the bus; IO1 stays low.
BUS_B = {"/U0TXD": (3, 11.1, 270.4), "/IO40": (5, 10.4, 270.6), "/IO37": (7, 9.7, 270.8), "/IO39": (9, 9.0, 271.0)}
for (net, (k, yb, xs)), yl in zip(BUS_B.items(), LANES):
    rise = yb - yl
    track(net, B, down(k, yl) + [(xs, yl), (xs + rise, yb)])
track("/IO1", B, down(21, 7.95))
# Top face: IO34, IO36, IO35, IO38 rise past the header and step down to the bottom
# face in a diagonal of vias; IO7 stays low.
BUS_F = {"/IO34": (11, 13.9, 271.1), "/IO36": (13, 13.2, 271.8), "/IO35": (15, 12.5, 272.5), "/IO38": (17, 11.8, 273.2)}
for (net, (k, yb, xv)), yl in zip(BUS_F.items(), LANES):
    track(net, F, down(k, yl) + [(xv - C, yl), (xv, yl + C), (xv, yb)])
    via(net, (xv, yb))
track("/IO7", F, down(19, 7.95))

# ---- the front row, up on the top face -----------------------------------------------
FRONT = {"/U0RXD": (4, 14.6, 270.4), "/IO33": (6, 15.3, 271.1), "/IO3": (18, 17.7, 270.4), "/IO2": (20, 18.4, 271.1)}
for net, (k, yb, xv) in FRONT.items():
    track(net, F, up(k, yb) + [(xv, yb)])
    via(net, (xv, yb))
# 5V: pins 24 and 22 up to one lane straight into J2.1; pin 8 up the bottom face to it
Y5 = 19.2
track("/INST_5V_A", F, up(24, Y5) + [(j2(1)[0], Y5)], PW)
track("/INST_5V_A", F, [j1(22), (j1(22)[0], Y5)], PW)
track("/INST_5V_A", B, [j1(8), (j1(8)[0], Y5)], PW)
via("/INST_5V_A", (j1(8)[0], Y5))
# GROUND: J-MCU-C's pin 10 straight into the Matrix's ground pad, J2.2, on the top face - the
# Matrix's whole return. The bus closes J-MCU-C off from the rest of the board on both faces,
# so this line is the only way between the arm's pour (J-MCU-C's other grounds) and the main
# pour (J2.2, the mounts).
track("PWR_GND", F, up(10, 16.1) + [(j2(2)[0], 16.1)], PW)
# 3V3: under J2.1, up between J2.1 and J2.2, into J2.3
Y3 = 16.85
track("/DEV_3V3", F, up(12, Y3) + [(273.9, Y3), (274.65, 17.6), (j2(3)[0], 17.6)], PW)

# ---- the bus along the near strip (bottom face), each line turning north in turn -------
# (net, its lane's height, the column it climbs)
BUS = [("/IO2", 18.4), ("/IO3", 17.7), ("/IO33", 15.3), ("/U0RXD", 14.6), ("/IO34", 13.9), ("/IO36", 13.2),
       ("/IO35", 12.5), ("/IO38", 11.8), ("/U0TXD", 11.1), ("/IO40", 10.4), ("/IO37", 9.7), ("/IO39", 9.0)]
X0, P = 280.35, 0.7
COL = {net: X0 + P * i for i, (net, _) in enumerate(BUS)}
START = {"/IO2": 271.1, "/IO3": 270.4, "/IO33": 271.1, "/U0RXD": 270.4, "/IO34": 271.1, "/IO36": 271.8,
         "/IO35": 272.5, "/IO38": 273.2, "/U0TXD": 271.55, "/IO40": 271.55, "/IO37": 271.55, "/IO39": 271.55}

# ---- the ladder: each column's height, and its top-face run to its pad ---------------------
ROW = {"/IO3": 20.6, "/IO2": 21.3, "/U0RXD": 22.0, "/U0TXD": 22.7, "/IO40": 23.4, "/IO39": 24.1, "/IO37": 24.8,
       "/IO38": 25.5}
# the four for J3's pads over the slot step west together, then run over the slot's end
WEST = {"/IO33": (X0, 34.3, 1), "/IO34": (X0 + P, 35.0, 2), "/IO36": (X0 + 2 * P, 36.4, 4), "/IO35": (X0 + 3 * P, 35.7, 3)}
YJOG = 26.2
for net, yl in BUS:
    x = COL[net]
    pts = [(START[net], yl), (x - C, yl), (x, yl + C)]
    if net in WEST:
        xw, yr, n = WEST[net]
        pts += [(x, YJOG), (xw, YJOG + (x - xw)), (xw, yr)]
        track(net, B, pts)
        via(net, (xw, yr))
        xt = j3(n)[0]
        if n == 4:      # IO36: J3.4 is just west of its column
            track(net, F, [(xw, yr), (xt + 0.41, yr), (xt, yr + 0.41), j3_in(n)])
        else:
            track(net, F, [(xw, yr), (xt + C, yr), (xt, yr + C), j3_in(n)])
        continue
    yr = ROW[net]
    track(net, B, pts + [(x, yr)])
    via(net, (x, yr))
    if net == "/IO3":     # down into J2.8, from above
        xt = j2(8)[0]
        track(net, F, [(x, yr), (xt - C, yr), (xt, yr - C), (xt, 16.5)])
    elif net == "/IO2":   # down into J2.9, from above
        xt = j2(9)[0]
        track(net, F, [(x, yr), (xt - C, yr), (xt, yr - C), (xt, 19.0)])
    elif net == "/IO39":  # its column lands on J3.7 as it stands
        track(net, F, [(x, yr), (x, j3(7)[1] - 0.5)])
    elif net == "/IO38":  # J3.6 just east of its column
        xt = j3(6)[0]
        track(net, F, [(x, yr), (xt, yr + (xt - x)), j3_in(6)])
    elif net == "/IO37":  # west to J3.5
        xt = j3(5)[0]
        track(net, F, [(x, yr), (xt + C, yr), (xt, yr + C), j3_in(5)])
    else:                 # RX, TX, IO40: east to their pads
        n = {"/U0RXD": 10, "/U0TXD": 9, "/IO40": 8}[net]
        xt = j3(n)[0]
        track(net, F, [(x, yr), (xt - C, yr), (xt, yr + C), j3_in(n)])

# IO7 and IO1 to J2 from below; IO1 under the near mount, then up to J2.10 by a via
track("/IO7", F, [down(19, 7.95)[-1], (j2(4)[0] - C, 7.95), (j2(4)[0], 7.95 + C), j2_in(4)])
x10 = j2(10)[0]
track("/IO1", B, [down(21, 7.95)[-1], (x10 - C, 7.95), (x10, 7.95 + C), (x10, 13.4)])
via("/IO1", (x10, 13.4))
track("/IO1", F, [(x10, 13.4), j2_in(10)])

# ---- ground stitching: the two pours joined where both are open ------------------------------
STITCH = [(296.6, 25.0), (296.6, 18.5), (294.0, 30.0), (290.0, 30.0), (286.9, 30.0), (290.0, 34.0),
          (294.0, 34.0), (284.4, 31.0), (276.0, 42.4), (253.2, 14.0), (253.2, 9.0), (296.5, 46.5), (284.5, 46.5)]


def to_pcb(p):
    return pcb.to_pcb(*p)


def draw(board):
    lid = {F: pcbnew.F_Cu, B: pcbnew.B_Cu}
    for net, layer, pts, w in T:
        ni = board.FindNet(net)
        assert ni is not None, net
        for a, b in zip(pts, pts[1:]):
            if math.dist(a, b) < 1e-6:
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcb.V(*to_pcb(a)))
            t.SetEnd(pcb.V(*to_pcb(b)))
            t.SetWidth(pcb.MM(w))
            t.SetLayer(lid[layer])
            t.SetNet(ni)
            board.Add(t)
    vias(board, V)


def vias(board, vs):
    for net, p in vs:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcb.V(*to_pcb(p)))
        v.SetWidth(pcb.MM(VIA))
        v.SetDrill(pcb.MM(DRILL))
        v.SetNet(board.FindNet(net))
        board.Add(v)


# Builder's marks the layout does not place: each header's pin 1, and J-MCU-C's, which
# hangs under the arm (bottom face), with the way its mouth and the ribbon face.
MARKS = [(True, "1", (j2(1)[0], 21.4)), (True, "1", (j3(1)[0], 44.2)),
         (False, "J-MCU-C MOUTH: FAR SIDE", (274.0, 8.2))]


def marks(board):
    for top, text, p in MARKS:
        x, y = to_pcb(p)
        pcb.silk_text(board, text, x, y, top=top)


_prepare = pcb_route.prepare


def prepare(board, lay):
    """pcb_route.prepare, then every route drawn: the autorouter that follows finds nothing to do."""
    _prepare(board, lay)
    draw(board)


if __name__ == "__main__":
    pcb_route.prepare = prepare
    rc = pcb.cmd_layout(BDIR, True, True) or 0
    if not rc:
        # the stitching vias after the layout's tidy, which takes a via on nothing but an
        # unfilled pour for a dangling one; then the pours filled round them
        out = os.path.join(BDIR, "matrix-carrier.kicad_pcb")
        board = pcbnew.LoadBoard(out)
        vias(board, [("PWR_GND", p) for p in STITCH])
        marks(board)
        pcbnew.SaveBoard(out, board)
        pcb._fill(out)
        print("carrier_routes: %d stitching vias" % len(STITCH))
    sys.exit(rc)
