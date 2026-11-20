#!/usr/bin/env python3
"""The right key board laid out by hand (issue #48, ADR 0030): every part placed on purpose
here, and every track and via written out below the placement. NO ROUTER OF ANY KIND IS CALLED.
THE PLACEMENT IS UNDER REVIEW: the tracks below are the plan drawn over it, not accepted copper.

    python3 hardware/boards/key-board-rh/rh_layout.py            # writes key-board-rh.hand.kicad_pcb (--place-only: no copper)

It READS key-board-rh.kicad_pcb (rev A, which stays the source until this board is
accepted) for what the body CAD and the sheets fix, strips its copper, and seats the
parts. Body frame throughout: x along the body from the mouth, y across it from the near
side, mm, seen from above; all parts but the switches are on the underside.

THE FLOORPLAN is the left-hand board's (hardware/boards/key-board-lh/lh_layout.py), 108 mm
toward the tail, with a sixth key. The two registers have the same pins for the chain and
for the four keys of the near row, so what decided that board decides this one:

1. THE CHAIN BUS RUNS UNDER THE REGISTER, between its pad rows, in J-CHAIN's own pin order.
2. THAT NEEDS J-CHAIN'S MOUTH TOWARD THE MOUTH END, as the left hand's now is. THE BODY CAD
   STILL FACES THIS ONE TOWARD THE TAIL (config/body.yaml routing.chain_fold), and the
   owner has not decided to turn it: this script seats the header TURNED, as a proposal
   (FACE, below), and says so when it runs. Facing the tail, the header's signal row is on
   its mouth side, and the register behind it would have its four near-row key inputs
   facing the far edge, away from every switch.
3. U1 stands as close behind the header as the left hand's does (owner, 2026-11-20, chose
   "Register closer to the header"), so the bus is as short as on the left. That puts the
   register on the mouth side of RH3, so RH3's line leaves the mouth end of its node, as
   RH4's and RH5's do; RH1 and RH2 still leave the tail end.
4. EACH KEY'S NETWORK STANDS OUTSIDE ITS OWN SWITCH'S PINS (tools/pcb_hand.py, KEY_NET).
5. The register's two decouplers each stand across a 3V3 pin and the ground pin beside
   it on the far row: C7 across pins 11 and 12, C9 across 16 and 15. RH6 and RH5 (pins 13
   and 14) leave between them. C8, the reservoir, stands at J-CHAIN's 3V3 pin.
6. RH6, the sixth key, is reached past RH5 and RH4 along the far edge and down the tail
   side of RH4's network.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import pcbnew       # noqa: E402
import yaml         # noqa: E402
import pcb          # noqa: E402  (frames, the sheets' netlist, the silkscreen steps; nothing that routes)
import pcb_hand     # noqa: E402  (what every hand-laid board shares: seating, the key pattern, the plane's rules)
from pcb_hand import GND, PITCH, PW, X_CAP, mouth_end, tail_end      # noqa: E402

NAME, CLUSTER = "key-board-rh", "right_hand"
SRC = os.path.join(HERE, NAME + ".kicad_pcb")
OUT = os.path.join(HERE, NAME + ".hand.kicad_pcb")
V33 = "V3V3_CHAIN_RH"

# PROPOSED, NOT DECIDED: J-CHAIN's mouth toward the mouth end (-1). The body CAD says +1.
# When the owner decides, config/body.yaml routing.chain_fold moves and this line goes.
FACE = -1

# J-CHAIN's pads with the header turned about its pad centre: the signal row (odd pins) at
# JX, pin 1 at the far-edge end, 1.27 between pins.
JX, JY1 = 183.41, 45.19


def jpin(k):
    return (JX if k % 2 else JX - PITCH, JY1 - PITCH * ((k - 1) // 2))


UX, UY = JX + 9.405, jpin(9)[1] + 0.5        # the left hand's distance from its header's signal row


def upin(n):
    """U1 pad n's centre: pins 1..8 on the key row's side, pin 8 at the header end."""
    if n <= 8:
        return (UX + PITCH * (4.5 - n), UY - 2.475)
    return (UX + PITCH * (n - 12.5), UY + 2.475)


def ch(d):
    """A line's height in the channel under U1, d from its middle."""
    return UY + d


Y_CAPS = UY + 4.7             # C7, C9: their courtyards clear of U1's
Y_RAIL = UY + 6.43            # the 3V3 spine past the far row
Y_VIA = Y_CAPS + 1.65         # C7's and C9's ground vias, past their pads

# (x, y, which way pad 1 faces)
PLACE = {
    "U1": (UX, UY, None),                                              # as rev A has it: pins 1..8 toward the key row
    "C8": (JX + 1.94, jpin(3)[1] + 0.95, "-y"),                        # C-BULK-CHAIN: its 3V3 pad level with J-CHAIN pin 3
    "C7": ((upin(11)[0] + upin(12)[0]) / 2, Y_CAPS, "-x"),             # across pins 11 (3V3) and 12 (ground)
    "C9": ((upin(15)[0] + upin(16)[0]) / 2, Y_CAPS, "+x"),             # across pins 16 (VCC) and 15 (ground)
}


def routes(cu, sw):
    ser, cap, pu1 = cu.keys(sw)

    # -- the chain bus: straight out of J-CHAIN's signal row into the channel under U1, in the
    # header's own order (the left-hand board's bus, 8 mm longer)
    (x9, y9), (x10, y10), (x1, y1), (x2, y2) = upin(9), upin(10), upin(1), upin(2)
    j = jpin(5)
    cu.track("/HOP_RH_RT", [j, (JX + 1.19, j[1]), (JX + 1.19 + j[1] - ch(0.5), ch(0.5)), (x9 - 0.5, ch(0.5)), (x9, ch(1.0)), (x9, y9)])
    j = jpin(7)
    cu.track("/HOP_LT_RH", [j, (JX + 1.19, j[1]), (JX + 1.19 + j[1] - ch(0), ch(0)), (x10 - 1.0, ch(0)), (x10, ch(1.0)), (x10, y10)])
    j = jpin(9)
    cu.track("/CHAIN_SHLD", [j, (x1 - 0.5, ch(-0.5)), (x1, ch(-1.0)), (x1, y1)])
    j = jpin(11)
    cu.track("/CHAIN_SCK", [j, (JX + 1.24, j[1]), (JX + 1.24 + ch(-1.0) - j[1], ch(-1.0)), (x2 - 0.3, ch(-1.0)), (x2, ch(-1.3)), (x2, y2)])

    # -- the corridor between RH3's capacitor and RH5's resistor: RH4, 3V3, RH5 side by side
    xw = cap["RH3"][0] + 1.3      # the rail's way back up to the row keys, mouth side of RH4's line
    xl4, xt, xl5 = xw + 0.6, xw + 1.2, xw + 1.8
    assert xl5 + 0.125 + 0.2 <= ser["RH5"][0] - 0.725 + 1e-6, "RH5's line fouls its own resistor"
    x6c = ser["RH6"][0] - 1.7     # RH6's way down, between the trunk's ring round RH4 and RH6's own resistor

    # -- 3V3, one trunk. Pin 3 into C8; the spine past the far row to C7 and pin 11; under the
    # body to pin 16 and C9; down the corridor to RH5's pull-up; round RH4 by the tail side;
    # then one rail along the near edge, out to RH6's pull-up one way and through RH4's and
    # the row keys' the other. The ring meets that rail square.
    j, c8 = jpin(3), (PLACE["C8"][0], jpin(3)[1])
    x11, x16 = upin(11)[0], upin(16)[0]
    c9 = (PLACE["C9"][0] + 0.9125, Y_CAPS)
    yr5, yr4, yr = pu1["RH5"][1], pu1["RH4"][1], pu1["RH3"][1]
    xe = sw["RH4"][0] + X_CAP + 1.3      # round RH4, outside its capacitor
    cu.track(V33, [j, c8, (c8[0] + 1.0, c8[1]), (c8[0] + 1.0 + Y_RAIL - c8[1], Y_RAIL), (x11 - 0.5, Y_RAIL), (x11, Y_RAIL - 0.5),
                   (x11, Y_CAPS), upin(11), (x11, ch(1.7)), (x11 + 0.8, ch(0.9)), (x16 - 0.8, ch(0.9)), (x16, ch(1.7)), upin(16),
                   (x16, Y_CAPS), c9, (xt, c9[1] - (xt - c9[0])), (xt, yr5 + 3.0), (xt + 3.0, yr5),
                   pu1["RH5"], (xe - 6.3, yr5), (xe, yr5 - 6.3), (xe, yr4)], PW)
    cu.track(V33, [pu1["RH6"], pu1["RH4"], (xw + 3.8, yr4), (xw, yr4 + 3.8), (xw, yr - 3.2), (xw - 3.2, yr),
                   pu1["RH3"], pu1["RH2"], pu1["RH1"]], PW)

    # -- the key lines, each from the end of its node that faces the register
    (x6, y6), (x5, y5), (x4, y4), (x3, y3), (x13, y13), (x14, y14) = upin(6), upin(5), upin(4), upin(3), upin(13), upin(14)
    # RH1 climbs beside its capacitor, crosses at 45 to its height under the header's pin
    # rows, and turns up into pin 6
    xc, yt, lvl = cap["RH1"][0] + 1.3, sw["RH1"][1] + 0.9, ch(-4.0)
    cu.track("/KEY_RH1", tail_end(cap, "RH1") + [(xc, yt), (xc + lvl - yt, lvl), (x6 - 0.5, lvl), (x6, lvl + 0.5), (x6, y6)])
    # RH2: beside its capacitor, then one diagonal to stand under pin 5
    xc = cap["RH2"][0] + 1.3
    cu.track("/KEY_RH2", tail_end(cap, "RH2") + [(xc, ch(-4.5) - (x5 - xc)), (x5, ch(-4.5)), (x5, y5)])
    # RH3: up the mouth side of its resistor, then a diagonal parallel to RH2's to stand under pin 4
    xc = ser["RH3"][0] - 1.2
    cu.track("/KEY_RH3", mouth_end(ser, "RH3", xc) + [(xc, ch(-5.1) - (x4 - xc)), (x4, ch(-5.1)), (x4, y4)])
    # RH4: up the corridor, then one diagonal over RH3's switch straight to the foot of pin 3
    # (owner, 2026-11-20: "this spot should just be one diagonal going down to the left")
    cu.track("/KEY_RH4", mouth_end(ser, "RH4", xl4) + [(xl4, ch(-4.1) - (xl4 - x3)), (x3, ch(-4.1)), (x3, y3)])
    # RH5 and RH6 leave the far row between C7 and C9 and go over C9 toward the tail, RH5 inside.
    # Each comes down to its key on one long diagonal rather than round a square corner (owner,
    # 2026-11-20: "need to be routed diagonally down"): RH5's runs beside the rail's, RH6's passes
    # the far side of RH5's switch.
    D5, D6 = 10.0, 14.0        # as long as C9's ground via and RH5's ground pin allow
    cu.track("/KEY_RH5", [(x14, y14), (x14, Y_VIA + 0.55), (x14 + 0.5, Y_VIA + 1.05), (xl5 - D5, Y_VIA + 1.05), (xl5, Y_VIA + 1.05 - D5)]
             + mouth_end(ser, "RH5", xl5)[::-1])
    cu.track("/KEY_RH6", [(x13, y13), (x13, Y_VIA + 1.15), (x13 + 0.5, Y_VIA + 1.65), (x6c - D6, Y_VIA + 1.65), (x6c, Y_VIA + 1.65 - D6)]
             + mouth_end(ser, "RH6", x6c)[::-1])

    # -- ground: each of these is a pad's own short stub to a via into the switch-side face
    x8, y8 = upin(8)
    cu.track(GND, [(x8, y8), (x8 - 1.3, y8)])
    cu.via(GND, (x8 - 1.3, y8))
    for n in (12, 15):                                             # up through C7's and C9's ground pads
        x, y = upin(n)
        cu.track(GND, [(x, y), (x, Y_VIA)])
        cu.via(GND, (x, Y_VIA))
    c82 = (PLACE["C8"][0], jpin(3)[1] + 1.9)
    cu.track(GND, [c82, (c82[0], c82[1] + 1.5)])
    cu.via(GND, (c82[0], c82[1] + 1.5))


def main():
    lay = yaml.safe_load(open(os.path.join(HERE, "layout.yaml")))
    comps, _ = pcb.sheet_netlist(os.path.join(HERE, NAME + ".kicad_sch"))
    geo = pcb.cad_geometry(CLUSTER)
    board = pcbnew.LoadBoard(SRC)
    pcb_hand.strip(board)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    pcb_hand.seat_chain(fps[pcb.ref_of(comps, "J-CHAIN")], geo, jpin, face=FACE)
    place = {**PLACE, **pcb_hand.key_places(comps, geo["switches"])}
    pcb_hand.seat_all(board, place)
    cu = pcb_hand.Copper()
    if "--place-only" not in sys.argv:
        routes(cu, geo["switches"])
        cu.draw(board)
    pcb_hand.finish(board, lay, comps, OUT)
    print(f"rh_layout: {len(place)} part(s) seated, {cu.segments()} track segment(s), {len(cu.vias)} ground via(s); J-CHAIN seated TURNED as a proposal (the body CAD faces it "
          f"the other way); wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
