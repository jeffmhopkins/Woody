#!/usr/bin/env python3
"""The Matrix carrier laid out by hand on ONE FACE (issue #48, ADR 0030), with the Matrix
ribbon's pins re-ordered so that no line crosses another (owner, 2026-11-20, chose
"Re-order the ribbon pins"). NO ROUTER OF ANY KIND IS CALLED: every track is written out below.

    python3 hardware/boards/matrix-carrier/carrier_layout.py     # rewrites matrix-carrier.kicad_pcb
    python3 tools/pcb.py check hardware/boards/matrix-carrier

THE RECORD of this board's copper (owner, 2026-11-20: "Awesome. Lock that in"). It READS
matrix-carrier.kicad_pcb for what the body CAD and the sheet fix (the outline, the three
connectors, the mounts, the silkscreen), strips its copper, gives J-MCU-C the footprint its
sheet names (pcb_hand.refit: the same pads in the same places), holds its pads to the nets
of PINS below (the sheet's, matrix-carrier.kicad_sch: pcb.py check proves the two agree), and
draws the tracks. Run twice it writes the same board.

THE FLOORPLAN. There is nothing to place: all three connectors are the body CAD's. What is
decided here is the order of the ribbon's 24 pins, and it is decided by where each line ends:

1. EVERY LINE IS ON THE TOP FACE, where the Matrix's two surface-mount pad rows are. The
   bottom face is one whole ground plane; the top face has no pour. The only via is the
   one that takes the Matrix's ground pad down to the plane.
2. J-MCU-C stands straight down from the arm (ADR 0018, Amendment of 2026-11-21), its two
   rows along the body. Its front row leaves toward the far side and its back row toward the near edge,
   each pin onto a lane of its own, the pin furthest from the Matrix on the outermost lane.
   So the order of the pins along the header IS the order of the lanes, and the order of
   the lanes is the order the lines peel off as they pass under the Matrix's near pad row.
3. That row (J2) stands across the way to the far row (J3). Its feet alternate, so a line
   passes between one foot and the next: three lines go up between pads 1 and 2 at once
   (necked to 0.2 mm there, the only neck on the board), and the rest run on under the
   row and turn up one gap at a time.
4. The four ribbon grounds are spread along the back row and go straight into the plane.
"""
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import pcbnew       # noqa: E402
import pcb          # noqa: E402  (frames only; nothing that routes)
import pcb_hand     # noqa: E402

NAME = "matrix-carrier"
SRC = os.path.join(HERE, NAME + ".kicad_pcb")
LAY = os.path.join(HERE, "layout.yaml")
F = pcbnew.F_Cu
TW, NW, PW = 0.25, 0.2, 0.4          # a line, a line necked through the one tight gap, a supply line
C = 0.3                              # a 45-degree corner
GND, V5, V33 = "PWR_GND", "/INST_5V_A", "/DEV_3V3"

# THE RIBBON'S ORDER ALONG THE HEADER, by PLACE: place q -> net. Column i (0 nearest the Matrix)
# holds the back row's place 2i+1 and the front row's place 2i+2. THE PAD AT PLACE q IS PIN
# 25 - q: the header is turned half a turn (owner, 2026-11-22; pre-fab review F3), its key
# toward the far side, so that its pin k is J-MCU's pin k and a ribbon made pin 1 to pin 1
# joins them. No pad moved when it was turned; only the numbers did. Place 19 (pin 6) is the
# ribbon's spare, on ground at both ends.
MX = 3.685                           # how far the Matrix stands from where this was first drawn: half of what the tail grew by (boards.umb_socket_d), 2026-11-22
PINS = {
    2: "/IO39", 4: "/IO6", 6: "/IO7", 8: "/IO38", 10: V33, 12: "/IO37", 14: "/IO36", 16: "/IO35", 18: "/IO34", 20: "/IO33",
    22: V5, 24: V5,
    1: "/IO40", 3: "/U0TXD", 5: GND, 7: "/U0RXD", 9: "/IO2", 11: GND, 13: "/IO1", 15: "/IO3", 17: GND, 19: GND,
    21: GND, 23: V5,
}


def j1(k):
    return (269.255 - 1.27 * ((k - 1) // 2), 11.385 if k % 2 else 12.655)


def j2(n):                    # the near pad row, 5V..IO1: odd pins' feet toward the far side
    return (272.97 + MX + 2.54 * (n - 1), 18.67 if n % 2 else 15.47)


def j3(n):                    # the far pad row, IO33..RX
    return (272.97 + MX + 2.54 * (n - 1), 41.53 if n % 2 else 38.33)


def routes(cu):
    def t(net, pts, w=TW):
        cu.track(net, pts, w, layer=F)

    def net_of(i):
        return PINS[2 * i + 2]

    # ---- the arm: the front row's lanes, pin column 1 lowest. J-MCU-C's pads stand off their
    # holes, away from the other row, so the first lane is 0.2 clear of the pads' far ends.
    north = {1: 13.945, 2: 14.395, 3: 14.845, 4: 15.295, 5: 15.745, 6: 16.195, 7: 16.645, 8: 17.095, 9: 17.545}

    def rise(i):
        x, y = j1(2 * i + 2)
        return [(x, y), (x, north[i] - C), (x + C, north[i])]

    # ---- the band under J2: thirteen lanes, the northmost leaving first ----------------------
    band = [13.5, 13.05, 12.525, 12.0, 11.55, 11.1, 10.65, 10.2, 9.75, 9.3, 8.85, 8.4, 7.95]

    def fall(i, lane, c):
        """Front column i from its arm lane down at 45 onto band lane `lane`, along x + y = c."""
        return rise(i) + [(c - north[i], north[i]), (c - band[lane], band[lane])]

    def up(x, y, to):
        """From a band lane at height y, turned up at column x and on to height `to`."""
        return [(x - C, y), (x, y + C), (x, to)]

    # the six lines for J3's pads 1..6 go round by the strip between J2 and the USB-C slot,
    # turn up beside the slot's end, and the first three come back over the slot
    strip = {1: 22.65, 2: 22.2, 3: 21.75, 4: 21.3, 5: 20.85, 6: 20.4}
    col = {n: 280.325 + MX + 0.45 * (n - 1) for n in range(1, 7)}       # their way up, beside the slot

    def far(n):
        """Along strip lane n, up beside the slot, and into J3 pad n."""
        x, s = col[n], strip[n]
        p = [(x - C, s), (x, s + C)]
        px, py = j3(n)
        if n <= 3:                                   # back over the slot, then up into the pad
            y = 34.175 + 0.45 * (n - 1)
            return p + [(x, y - C), (x - C, y), (px + C, y), (px, y + C), (px, py)]
        if n == 4:                                   # pad 4's foot is just to the left of its way up
            return p + [(x, 36.0), (x - 0.775, 36.775), (x - 0.775, py)]
        if n == 5:
            return p + [(x, py - (px - x)), (px, py)]
        return p + [(x, 33.2), (px, 33.2 + px - x), (px, py)]

    # J3 pads 1..3: front columns 9, 8, 7. Each dips 0.6 to pass under J2 pad 1's foot, then
    # goes up between J2's pads 1 and 2, necked to 0.2 there: the one neck on the board.
    for n, i, c, gx in ((1, 9, 289.24, 273.82 + MX), (2, 8, 288.6, 274.25 + MX), (3, 7, 287.96, 274.68 + MX)):
        y, net, s = north[i] - 0.6, net_of(i), strip[n]
        t(net, rise(i) + [(c - north[i], north[i]), (c - y, y), (272.9 + MX, y)])
        t(net, [(272.9 + MX, y), (gx - 0.2, y), (gx, y + 0.2), (gx, s - C), (gx + C, s)], NW)
        t(net, [(gx + C, s)] + far(n))

    # J3 pads 4, 5: front columns 6 and 5, up between J2's pads 2 and 3
    for n, i, lane, c, gx in ((4, 6, 0, 287.32, 276.36 + MX), (5, 5, 1, 286.68, 276.81 + MX)):
        t(net_of(i), fall(i, lane, c) + up(gx, band[lane], strip[n] - C) + [(gx + C, strip[n])] + far(n))
    # 3V3: front column 4, wide from where it leaves the arm, straight up into J2 pad 3
    i, c = 4, 285.93
    t(V33, rise(i) + [(c - north[i], north[i]), (c - north[i] + 0.4, north[i] - 0.4)])     # narrow until clear of its neighbours' lanes
    t(V33, [(c - north[i] + 0.4, north[i] - 0.4), (c - band[2], band[2])] + up(j2(3)[0], band[2], j2(3)[1]), PW)
    # J3 pad 6: front column 3, up between J2's pads 3 and 4
    t(net_of(3), fall(3, 3, 285.18) + up(278.9 + MX, band[3], strip[6] - C) + [(278.9 + MX + C, strip[6])] + far(6))
    # IO7 and IO6 straight up into J2's pads 4 and 5
    t("/IO7", fall(2, 4, 284.54) + up(j2(4)[0], band[4], j2(4)[1]))
    t("/IO6", fall(1, 5, 283.9) + up(j2(5)[0], band[5], j2(5)[1]))

    def diag_up(net, pts, lane, gx, y0, n):
        """Along band lane `lane`, up column gx to y0, across at 45 to stand under J3 pad n, and into it."""
        px, py = j3(n)
        t(net, pts + up(gx, band[lane], y0) + [(px, y0 + px - gx), (px, py)])

    # ---- column 0: both pins straight out toward the Matrix, onto lanes 6 and 7 ----------------
    x, y = j1(2)
    diag_up("/IO39", [(x, y), (282.2 - y, y), (282.2 - band[6], band[6])], 6, 283.98 + MX, 33.68, 7)
    x, y = j1(1)
    diag_up("/IO40", [(x, y), (270.0, y), (270.0 + y - band[7], band[7])], 7, 284.43 + MX, 30.28, 8)

    # ---- the back row: five lanes under the header ---------------------------------------------
    back = {}
    for k, lane in ((3, 8), (7, 9), (9, 10), (13, 11), (15, 12)):
        x, y = j1(k)
        back[k] = [(x, y), (x, band[lane] + C), (x + C, band[lane])]
    diag_up("/U0TXD", back[3], 8, 286.52 + MX, 31.22, 9)
    diag_up("/U0RXD", back[7], 9, 286.97 + MX, 27.67, 10)

    # IO2, IO1 and IO3 pass the near mount on its mouth side
    t("/IO2", back[9] + up(287.42 + MX, band[10], 13.0) + [(289.095 + MX, 14.675), (289.095 + MX, 17.7), (289.595 + MX, 18.2), (j2(9)[0], 18.2)])
    t("/IO1", back[13] + up(287.87 + MX, band[11], 12.36) + [(289.545 + MX, 14.035), (289.545 + MX, 16.8), (290.045 + MX, 17.3), (291.9 + MX, 17.3),
                                                              (292.3 + MX, 16.9), (294.0 + MX, 16.9), (295.0 + MX, 15.9), (j2(10)[0], 15.9)])
    t("/IO3", back[15] + up(288.32 + MX, band[12], 12.015) + [(290.75 + MX, 14.445)])

    # ---- 5V: three pins strapped at the header's far end, one lane along the arm into J2 pad 1 --
    t(V5, [j1(23), j1(24), j1(22), (j1(22)[0], 18.67 - C), (j1(22)[0] + C, 18.67), j2(1)], PW)

    # ---- ground: the Matrix's ground pad to the plane ------------------------------------------
    gx, gy = j2(2)
    t(GND, [(gx, gy), (gx, 17.6)])
    cu.via(GND, (gx, 17.6))


def main():
    board = pcbnew.LoadBoard(SRC)
    for t in list(board.GetTracks()):                    # the copper goes; the silkscreen stays
        board.Delete(t)
    for z in list(board.Zones()):                        # no pour on the face the lines are on
        if z.GetIsRuleArea():
            continue
        if z.IsOnLayer(F):
            board.Delete(z)
        else:
            z.UnFill()
    for z in board.Zones():
        if z.GetNetname() == GND:
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    comps, nets = pcb.sheet_netlist(os.path.join(HERE, NAME + ".kicad_sch"))
    for n, _ in nets:                                    # a pad the sheet leaves open has a net of its own, named for it
        if board.FindNet(n) is None:
            board.Add(pcbnew.NETINFO_ITEM(board, n))
    pcb_hand.refit(board, comps, nets)
    j = next(f for f in board.GetFootprints() if f.GetReference() == "J1")
    for k, net in PINS.items():
        pad = j.FindPadByNumber(str(25 - k))
        got = pcb_hand.body_xy(pad.GetPosition())
        assert abs(got[0] - j1(k)[0]) < 0.01 and abs(got[1] - j1(k)[1]) < 0.01, (k, got, j1(k))
        if net is None:              # on no net: KiCad's own name for such a pad, so the sheet's parity holds
            net = f"unconnected-({j.GetReference()}-Pin_{25 - k}-Pad{25 - k})"
            if board.FindNet(net) is None:
                board.Add(pcbnew.NETINFO_ITEM(board, net))
        pad.SetNetCode(board.FindNet(net).GetNetCode())
        if net == GND:               # boxed in by its neighbours' pads: one spoke is all that fits, so it joins whole
            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    for f in board.GetFootprints():                      # the mounts are bolted, not soldered: whole
        if f.GetReference().startswith("H"):
            for pad in f.Pads():
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    cu = pcb_hand.Copper()
    routes(cu)
    cu.draw(board)
    lay = yaml.safe_load(open(LAY))
    silk = lay["silk"]                                   # the title block's and the silkscreen's
    tb = board.GetTitleBlock()
    tb.SetDate(silk["date"])
    tb.SetRevision(silk["rev"])
    for d in list(board.GetDrawings()):
        if not isinstance(d, pcbnew.PCB_TEXT):
            continue
        if d.GetText().startswith("rev "):
            d.SetText(f"rev {silk['rev']}  {silk['date']}")
        elif d.GetText() == "J1" or d.GetText().startswith("J-MCU-C"):
            board.Delete(d)                              # written for the header this board had; put back below
    # J-MCU-C's marks, on the arm's underside beside it, on its far side (its near side is the
    # board's edge): its reference, and which way its key faces, since its outline is not printed
    # (it overhangs the arm's end, and pcb.fit_footprint_silk takes such an outline off)
    pcb.fit_footprint_silk(board, lay["fab"])
    pcb.silk_text(board, "J1", *pcb.to_pcb(262.27, 16.5))
    pcb.silk_text(board, "J-MCU-C KEY: FAR SIDE", *pcb.to_pcb(262.27, 18.3))
    pcbnew.SaveBoard(SRC, board)
    pcb_hand.fill(SRC)
    print(f"carrier_layout: {cu.segments()} track segment(s), {len(cu.vias)} via(s); wrote {os.path.relpath(SRC, ROOT)}")


if __name__ == "__main__":
    main()
