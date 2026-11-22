#!/usr/bin/env python3
"""The left key board laid out by hand (issue #48): every part placed on purpose here,
and every track and via written out below the placement.
NO ROUTER OF ANY KIND IS CALLED: not tools/pcb_route*.py, not Freerouting, not KiCad's.

    python3 hardware/boards/key-board-lh/lh_layout.py            # rewrites key-board-lh.kicad_pcb (--place-only: no copper)

It is THE RECORD OF THIS BOARD'S LAYOUT and rewrites key-board-lh.kicad_pcb in place. From
the board it keeps what the body CAD and the sheets fix - the outline, the five switches,
the four mounts and their keep-outs, the switch-side ground zone's outline, every pad's
net - and replaces the rest: it strips the copper and silkscreen, seats J-CHAIN where the
body CAD puts it and every other part where PLACE says, and draws the tracks. Running it
twice gives the same board. Then: tools/pcb.py check, tools/pcb.py render. Body frame throughout:
x along the body from the mouth, y across it from the near side, mm, seen from above;
all parts but the switches are on the underside.

THE FLOORPLAN, and why each part is where it is.

1. THE REGISTER'S PINOUT DECIDES THE BOARD. Going round U1: SH/LD and CLK (pins 1, 2),
   the keys LH4, LH3, LH2, LH1 (pins 3..6), ground (8), then QH and SER (9, 10), the
   free input and its rail (11, 12), ground, LH5 (14), ground, VCC (16). The chain's four
   lines sit at its four corners and LH5 sits alone on the far row. Routed from the pads
   outward, the chain lines have to wrap the register (rev A took SH/LD and SCK round the
   far edge), and LH5 crosses them.
   THE CHAIN BUS THEREFORE RUNS UNDER THE REGISTER, between its pad rows: all four lines
   enter at the pin-8/9 end and turn into their pads from inside. Across that end, from
   the key row's side, they lie SCK, SH/LD, SER, QH - which is J-CHAIN's own pin order
   (2, 4, 6, 8).
2. J-CHAIN STANDS VERTICAL, ITS SIGNAL ROW TOWARD THE REGISTER (ADR 0017 amended
   2026-11-21). The ribbon folds toward the mouth end (config/body.yaml routing.chain_fold)
   and the socket on this end of it has its even row away from the fold, so the even row -
   the four lines and 3V3 - faces the register and the odd row, all ground, faces the
   mouth. The bus runs from the header's pads, each by one 45, into the register's end: no
   line wraps the header, none crosses another, no via.
3. U1 stands past the header's pin rows, its pin-8/9 end toward them and its key
   inputs (pins 3..6) facing the key row, so LH1..LH4 arrive in pin order from the side
   their switches are on, and LH5 leaves the far row toward its own switch.
4. EACH KEY'S NETWORK STANDS OUTSIDE ITS OWN SWITCH'S PINS, the same way round all five:
   the series resistor beside pin 1 (the switch leg) on the mouth side, the capacitor
   beside pin 2 (ground) on the tail side, each joined to its pin by one short neck; the
   node runs between them under both pins with the pull-up hanging from its middle, its
   rail end toward the near edge. Nothing passes between a pin and the pole, and the key
   line leaves whichever end of the node faces the register.
5. 3V3 IS ONE TRUNK. Out of the header's pin 10 straight into C7 (the reservoir), along
   the far row: R11 (the free input's pull-up), C8 across pins 12/13, under the body to
   pin 16 and C6 across 16/15; then on between LH5's and LH4's lines to their
   pull-ups, round LH4 and back along the near edge through the three row keys' pull-ups.
6. GROUND IS THE SWITCH-SIDE FACE, whole, and the parts face has no pour at all. Every switch's and the header's ground
   pin is a through-hole into it; the register's ground pins and the capacitors reach
   it by a via each. No ground track but each capacitor's neck to its switch's pin.
   The switches' and the header's ground pins join the plane by relief spokes.
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
from pcb_hand import DROP, GND, PITCH, PW, X_CAP, mouth_end, tail_end      # noqa: E402

NAME, CLUSTER = "key-board-lh", "left_hand"
SRC = os.path.join(HERE, NAME + ".kicad_pcb")
V33 = "V3V3_CHAIN_LH"

# ---- the register and its own parts ------------------------------------------------------------
# J-CHAIN's pads, once seated where the body CAD puts it (pcb_hand.seat_chain): the signal
# row (even pins) at JX, the ground row (odd pins) a pitch toward the mouth, pins 1 and 2
# at the near-edge end, 1.27 between pins.
JX, JY1 = 79.135, 39.29
X_FAN = JX + 1.265            # where the bus turns onto its 45: clear of the header's pads


def jpin(k):
    return (JX if k % 2 == 0 else JX - PITCH, JY1 + PITCH * ((k - 1) // 2))


# U1's centre. x: pin 4 (LH3's input) 3.4 toward the tail from LH3's switch's centre (the
# body CAD's LH3, pcb-geometry.echo), which leaves the bus room to step from the header's
# 1.27 pitch to the channel's. y: its far row's parts (C8, C6, R11, the 3V3 spine) clear of
# the far edge; every bus line then steps from its header pad to its channel height, SCK least.
UX, UY = 90.0 + 3.4 - PITCH / 2, 40.61


def upin(n):
    """U1 pad n's centre: pins 1..8 on the key row's side, pin 8 at the header end."""
    if n <= 8:
        return (UX + PITCH * (4.5 - n), UY - 2.475)
    return (UX + PITCH * (n - 12.5), UY + 2.475)


def ch(d):
    """A line's height in the channel under U1, d from its middle."""
    return UY + d


Y_CAPS = UY + 4.7             # C8, C6: their courtyards clear of U1's
Y_RAIL = UY + 6.43            # the 3V3 spine past the far row: through R11.1
Y_VIA = Y_CAPS + 1.65         # C8's and C6's ground vias, past their pads

# (x, y, which way pad 1 faces) - the way is found on the board, not assumed (pcb_hand.seat)
PLACE = {
    "U1": (UX, UY, None),                                 # turned as rev A had it: pins 1..8 toward the key row
    "C7": (JX + 3.365, jpin(10)[1] + 0.95, "-y"),               # C-BULK-CHAIN: its 3V3 pad level with J-CHAIN pin 10, one straight stub clear of the header's courtyard; ground end toward the far edge
    "R11": (upin(11)[0] - 0.5, Y_RAIL - 0.9125, "+y"),    # FREE3's pull-up: pad 2 down onto pin 11, pad 1 on the spine
    "C8": (upin(12)[0] + 0.95, Y_CAPS, "-x"),             # across pins 12 (3V3) and 13 (ground)
    "C6": (upin(15)[0] + 0.95, Y_CAPS, "+x"),             # across pins 16 (VCC) and 15 (ground)
}


def routes(cu, sw):
    ser, cap, pu1 = cu.keys(sw)

    # -- the chain bus: straight out of J-CHAIN's signal row into the channel under U1. From
    # the key row's side the channel holds SCK, SH/LD, SER, QH at half-millimetre steps, the
    # header's own order; each leaves its pad straight, steps to its channel height on one 45
    # from X_FAN - the header's pitch closing to the channel's - and turns into its pad from inside.
    (x9, y9), (x10, y10), (x1, y1), (x2, y2) = upin(9), upin(10), upin(1), upin(2)
    def fan(k, d):
        (_, y) = jpin(k)
        return [jpin(k), (X_FAN, y), (X_FAN + abs(y - ch(d)), ch(d))]

    cu.track("/HOP_LH_LT", fan(8, 0.5) + [(x9 - 0.5, ch(0.5)), (x9, ch(1.0)), (x9, y9)])
    cu.track("/CHAIN_SER_LH", fan(6, 0) + [(x10 - 1.0, ch(0)), (x10, ch(1.0)), (x10, y10)])
    cu.track("/CHAIN_SHLD", fan(4, -0.5) + [(x1 - 0.5, ch(-0.5)), (x1, ch(-1.0)), (x1, y1)])
    cu.track("/CHAIN_SCK", fan(2, -1.0) + [(x2 - 0.3, ch(-1.0)), (x2, ch(-1.3)), (x2, y2)])

    # -- 3V3, one trunk. Pin 10 straight into C7; up to the spine past the far row and along it
    # through R11 to C8 and pin 12; under the body to pin 16 and out to C6; then between
    # LH5's line and LH4's down to LH5's pull-up, round LH4 by the tail side to its pull-up,
    # and back along the near edge through the row keys' pull-ups, ending at LH1's.
    j, c7 = jpin(10), (PLACE["C7"][0], jpin(10)[1])
    r11 = (PLACE["R11"][0], Y_RAIL)
    x12, x16 = upin(12)[0], upin(16)[0]
    c6 = (upin(15)[0] + 1.9, Y_CAPS)
    xt = sw["LH3"][0] + X_CAP + 1.3 + 1.2      # the trunk's way down: third of the corridor's four lines (below)
    yr5, yr4, yr = pu1["LH5"][1], pu1["LH4"][1], pu1["LH3"][1]
    # The trunk rings LH4: LH4's line leaves its switch on the mouth side, so on one face the
    # rail reaches LH4's pull-up and the row keys' only round LH4's tail side. With no pour on
    # this face (NO PARTS-FACE POUR, below) the ring encloses nothing.
    # Every corner of the ring is cut at 45 as far as what stands inside it allows (owner,
    # 2026-11-20: "some of the 3 volt rail looks like it could use more diagonal").
    xe = sw["LH4"][0] + X_CAP + 1.3      # round LH4, outside its capacitor
    xw = sw["LH3"][0] + X_CAP + 1.3      # back up to the row keys' rail, mouth side of LH4's line
    # C6 hangs off the trunk by its own short neck: the trunk turns below the pad and does not
    # fold back inside it (owner, 2026-11-22: no two tracks meeting at a point in a pad)
    c6t = (c6[0], UY + 3.45 + c6[0] - x16)
    cu.track(V33, [c6t, c6], PW)
    cu.track(V33, [j, c7, (c7[0] + 1.0, c7[1]), (c7[0] + 1.0 + Y_RAIL - c7[1], Y_RAIL), r11, (x12 - 0.5, Y_RAIL), (x12, Y_RAIL - 0.5),
                (x12, Y_CAPS), upin(12), (x12, ch(1.7)), (x12 + 0.8, ch(0.9)), (x16 - 0.8, ch(0.9)), (x16, ch(1.7)), upin(16),
                (x16, UY + 3.45), c6t, (xt, c6t[1] - (xt - c6[0])), (xt, yr5 + 3.0), (xt + 3.0, yr5),
                pu1["LH5"], (xe - 6.3, yr5), (xe, yr5 - 6.3), (xe, yr4 + 1.5), (xe - 1.5, yr4), pu1["LH4"], (xw + 3.8, yr4),
                (xw + 3.8 - (yr - yr4), yr), pu1["LH3"], pu1["LH2"], pu1["LH1"]], PW)

    # -- the key lines. Each leaves the end of its node that faces the register (owner,
    # 2026-11-20): LH1..LH3 the tail end, LH4 and LH5 the mouth end.
    (x6, y6), (x5, y5), (x4, y4), (x3, y3), (x14, y14) = upin(6), upin(5), upin(4), upin(3), upin(14)
    # LH1 and LH2 each leave their capacitor on one diagonal (owner, 2026-11-20, on the
    # right-hand board: "should do a full diagonal"): LH1 to its height under the header's pin
    # rows and along into pin 6, LH2 straight to stand under pin 5
    (xc, yc), lvl = cap["LH1"], ch(-4.0)
    cu.track("/KEY_LH1", [(xc, yc), (xc + 0.8, yc), (xc + 0.8 + lvl - yc, lvl), (x6 - 0.5, lvl), (x6, lvl + 0.5), (x6, y6)])
    xc, yc = cap["LH2"]
    cu.track("/KEY_LH2", [(xc, yc), (xc + 0.8, yc), (x5, yc + x5 - xc - 0.8), (x5, y5)])
    # The corridor between LH3's capacitor and LH5's resistor carries four lines side by side,
    # in the order they reach the register and the trunk reaches LH5: LH3, LH4, 3V3, LH5.
    xl3 = cap["LH3"][0] + 1.3
    xl4, xt, xl5 = xl3 + 0.6, xl3 + 1.2, xl3 + 1.8
    assert xl5 + 0.125 + 0.2 <= ser["LH5"][0] - 0.725 + 1e-6, "LH5's line fouls its own resistor"
    # LH3 and LH4 cross together at 45 to stand under pins 4 and 3
    cu.track("/KEY_LH3", tail_end(cap, "LH3") + [(xl3, 31.5), (x4, 31.5 + xl3 - x4), (x4, y4)])
    cu.track("/KEY_LH4", mouth_end(ser, "LH4", xl4) + [(xl4, 32.1), (x3, 32.1 + xl4 - x3), (x3, y3)])
    # LH5: out of the far row between C8 and C6, over C6's ground via, and straight down the corridor
    cu.track("/KEY_LH5", [(x14, y14), (x14, UY + 3.6), (x14 + 0.3, UY + 3.9), (x14 + 0.3, Y_VIA + 0.55), (x14 + 0.8, Y_VIA + 1.05),
                       (xl5 - 2.0, Y_VIA + 1.05), (xl5, Y_VIA - 0.95)] + mouth_end(ser, "LH5", xl5)[::-1])
    # the free input: pin 11 up into its pull-up
    x11, y11 = upin(11)
    cu.track("/KEY_FREE3", [(x11, y11), (x11, UY + 3.4), (x11 - 0.5, UY + 3.9), (x11 - 0.5, Y_RAIL - 1.825)])

    # -- ground: no track runs anywhere. Each of these is a pad's own short stub to a via
    # into the switch-side face.
    x8, y8 = upin(8)
    cu.track(GND, [(x8, y8), (x8 - 1.3, y8)])                       # U1's ground pin, toward the header
    cu.via(GND, (x8 - 1.3, y8))
    x13, y13 = upin(13)
    c82 = (x12 + 1.9, Y_CAPS)
    cu.track(GND, [(x13, y13), (x13, UY + 3.6), (x13 + 0.5, UY + 4.1)])   # pin 13 into C8's ground pad
    cu.track(GND, [c82, (c82[0], Y_VIA)])
    cu.via(GND, (c82[0], Y_VIA))
    x15, y15 = upin(15)
    cu.track(GND, [(x15, y15), (x15, Y_VIA)])                       # pin 15 up through C6's ground pad
    cu.via(GND, (x15, Y_VIA))
    c72 = (PLACE["C7"][0], jpin(10)[1] + 1.9)
    cu.track(GND, [c72, (c72[0], c72[1] + 1.5)])                    # C7's ground end
    cu.via(GND, (c72[0], c72[1] + 1.5))



# R11 stands between C8 and J-CHAIN with a part or a pad on every side the silkscreen step
# tries, so its reference is put by hand in the clear strip between it and the far edge,
# directly over it: nearer R11 than anything else, and C8's own reference reads the other way.
LABELS = {"R11": (90.36, 48.45, 0)}


def main():
    lay = yaml.safe_load(open(os.path.join(HERE, "layout.yaml")))
    comps, nets = pcb.sheet_netlist(os.path.join(HERE, NAME + ".kicad_sch"))
    geo = pcb.cad_geometry(CLUSTER)
    board = pcbnew.LoadBoard(SRC)
    pcb_hand.strip(board)
    pcb_hand.refit(board, comps, nets)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    pcb_hand.seat_chain(fps[pcb.ref_of(comps, "J-CHAIN")], geo, jpin)
    place = {**PLACE, **pcb_hand.key_places(comps, geo["switches"])}
    pcb_hand.seat_all(board, place)
    cu = pcb_hand.Copper()
    if "--place-only" not in sys.argv:
        routes(cu, geo["switches"])
        cu.draw(board)
    pcb_hand.finish(board, lay, comps, SRC, labels=LABELS)
    print(f"lh_layout: {len(place)} part(s) seated, {cu.segments()} track segment(s), {len(cu.vias)} ground via(s); "
          f"wrote {os.path.relpath(SRC, ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
