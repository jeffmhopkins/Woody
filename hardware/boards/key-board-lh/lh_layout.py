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
   (11, 9, 7, 5).
2. J-CHAIN'S MOUTH FACES THE MOUTH END (owner, 2026-11-20: "Seems like maybe we could turn
   the header 180"; config/body.yaml routing.chain_fold), so its signal row - the row
   behind the mouth - faces the register, and the bus runs straight from the header's
   pads into the register's end: no line wraps the header, none crosses another, no via.
3. U1 stands just past the header's pin rows, its pin-8/9 end toward them and its key
   inputs (pins 3..6) facing the key row, so LH1..LH4 arrive in pin order from the side
   their switches are on, and LH5 leaves the far row toward its own switch.
4. EACH KEY'S NETWORK STANDS OUTSIDE ITS OWN SWITCH'S PINS, the same way round all five:
   the series resistor beside pin 1 (the switch leg) on the mouth side, the capacitor
   beside pin 2 (ground) on the tail side, each joined to its pin by one short neck; the
   node runs between them under both pins with the pull-up hanging from its middle, its
   rail end toward the near edge. Nothing passes between a pin and the pole, and the key
   line leaves whichever end of the node faces the register.
5. 3V3 IS ONE TRUNK. Out of the header's pin 3 straight into C7 (the reservoir), along
   the far row: R11 (the free input's pull-up), C8 across pins 12/13, under the body to
   pin 16 and C6 across 16/15; then on between LH5's and LH4's lines to their
   pull-ups, round LH4 and back along the near edge through the three row keys' pull-ups.
6. GROUND IS THE SWITCH-SIDE FACE, whole, and the parts face has no pour at all. Every switch's and the header's ground
   pin is a through-hole into it; the register's ground pins and the capacitors reach
   it by a via each. No ground track but each capacitor's neck to its switch's pin.
   The switches' and the header's ground pins join the plane by relief spokes.
"""
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import pcbnew       # noqa: E402
import yaml         # noqa: E402
import pcb          # noqa: E402  (frames, the sheets' netlist, the silkscreen steps; nothing that routes)

NAME = "key-board-lh"
SRC = os.path.join(HERE, NAME + ".kicad_pcb")
OUT = SRC

# ---- the register and its own parts ------------------------------------------------------------
# J-CHAIN's pads, once seated where the body CAD puts it (seat_chain, below): the signal
# row (odd pins) at JX, pin 1 at the far-edge end, 1.27 between pins.
JX, JY1 = 83.36, 45.19


def jpin(k):
    return (JX if k % 2 else JX - 1.27, JY1 - 1.27 * ((k - 1) // 2))


# U1's centre. x: pin 4 (LH3's input) straight above the line LH3's key line climbs past its
# own switch's pole on, 3.4 toward the tail from the switch's centre (the body CAD's LH3,
# pcb-geometry.echo) - which also leaves the bus room to step from the header's 1.27 pitch
# to the channel's. y: SH/LD (J-CHAIN pin 9) runs dead straight from its pad down the
# channel, half a pitch below the channel's middle line.
UX, UY = 90.0 + 3.4 - 1.27 / 2, jpin(9)[1] + 0.5
PITCH = 1.27


def upin(n):
    """U1 pad n's centre: pins 1..8 on the key row's side, pin 8 at the header end."""
    if n <= 8:
        return (UX + PITCH * (4.5 - n), UY - 2.475)
    return (UX + PITCH * (n - 12.5), UY + 2.475)


Y_CAPS = UY + 4.7             # C8, C6: their courtyards clear of U1's
Y_RAIL = UY + 6.43            # the 3V3 spine past the far row: through R11.1

# (x, y, which way pad 1 faces) - the way is found on the board, not assumed (seat(), below)
PLACE = {
    "U1": (UX, UY, None),                                 # turned as rev A has it: pins 1..8 toward the key row
    "C7": (85.3, jpin(3)[1] + 0.95, "-y"),                # C-BULK-CHAIN: its 3V3 pad level with J-CHAIN pin 3, one straight stub; ground end toward the far edge
    "R11": (upin(11)[0] - 0.5, Y_RAIL - 0.9125, "+y"),    # FREE3's pull-up: pad 2 down onto pin 11, pad 1 on the spine
    "C8": (upin(12)[0] + 0.95, Y_CAPS, "-x"),             # across pins 12 (3V3) and 13 (ground)
    "C6": (upin(15)[0] + 0.95, Y_CAPS, "+x"),             # across pins 16 (VCC) and 15 (ground)
}

# ---- a key's network, relative to its switch's centre -------------------------------------------
# The switch's pins (hardware/lib, SW_Gateron_KS33_1u): pin 1, the leg, at (-4.4, -4.7);
# pin 2, ground, at (+2.6, -5.75); the pole's hole, 5.25 across, at the centre.
# NOTHING PASSES BETWEEN A PIN AND THE POLE (owner, 2026-11-20, of the line that did: "Each of
# these need work too"). That gap is 2 mm, and a line through it cut the ground pin's relief
# ring and dropped into the node between two pads. So each part stands OUTSIDE its own pin,
# beside it and level with it, joined by one short straight neck: the series resistor on the
# mouth side of the leg pin, the capacitor on the tail side of the ground pin. The node runs
# between the two under both pins, DROP below the centre, with the pull-up hanging from its
# middle. Its two ends are free, and the key line leaves from the one facing the register.
DROP = 8.5                    # the node: clear of the ground pin's relief ring above it, and LH4's pull-up below it clear of the board's edge by a strip of pour
X_SER, X_CAP = -7.8, 6.0      # the two parts' columns: a millimetre of mask between pad and pin
KEY_NET = {
    "R-KEY-SER": (X_SER, -4.7 - 0.9125, "-y"),            # pad 2 (the leg) level with pin 1, pad 1 (the node) below it
    "R-KEY-PU": (-0.94, -DROP - 0.9125, "-y"),            # pad 2 at the node, pad 1 (3V3) toward the near edge
    "C-KEY": (X_CAP, -5.75 - 0.9125, "-y"),               # pad 2 (ground) level with pin 2, pad 1 (the node) below it
}
BODY = ("SW", "J", "H")


def body_xy(p):
    return (pcbnew.ToMM(p.x) - pcb.OX, pcb.OY - pcbnew.ToMM(p.y))


def seat(fp, x, y, way):
    """fp to body (x, y), turned so its pad 1 lies toward `way` from its centre. The turn is
    found by trying the four: on the underside KiCad mirrors rotation."""
    fp.SetPosition(pcb.V(*pcb.to_pcb(x, y)))
    if way is None:
        return
    want = {"+x": (1, 0), "-x": (-1, 0), "+y": (0, 1), "-y": (0, -1)}[way]
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        px, py = body_xy(fp.FindPadByNumber("1").GetPosition())
        d = (px - x, py - y)
        n = math.hypot(*d)
        if n > 1e-6 and abs(d[0] / n - want[0]) < 1e-3 and abs(d[1] / n - want[1]) < 1e-3:
            return
    raise SystemExit(f"lh_layout: no turn puts {fp.GetReference()}'s pad 1 toward {way}")


def seat_chain(fp, geo):
    """J-CHAIN where the body CAD puts it and facing the way it says (pcb.chain_target):
    the turn is found, as pcb.place_chain finds it for a new board."""
    (tx, ty), d = pcb.chain_target(geo)
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        p1, p2 = fp.FindPadByNumber("1").GetPosition(), fp.FindPadByNumber("2").GetPosition()
        dx, dy = pcbnew.ToMM(p2.x - p1.x), pcbnew.ToMM(p2.y - p1.y)
        if abs(dy) < 1e-3 and dx * d > 0:
            cx, cy = pcb.pads_centre(fp)
            at = fp.GetPosition()
            fp.SetPosition(pcb.V(pcbnew.ToMM(at.x) + tx - cx, pcbnew.ToMM(at.y) + ty - cy))
            for k in (1, 3, 11, 12):
                got, want = body_xy(fp.FindPadByNumber(str(k)).GetPosition()), jpin(k)
                if math.dist(got, want) > 0.01:
                    raise SystemExit(f"lh_layout: J-CHAIN pin {k} is at {got}, and this layout is drawn for {want} - "
                                     "the body CAD moved the header (pcb-geometry.echo); move JX, JY1 and what follows from them")
            return
    raise SystemExit("lh_layout: no turn puts J-CHAIN's mouth where the body CAD faces it")


def placement(board, comps):
    geo = pcb.cad_geometry("left_hand")
    place = dict(PLACE)
    for key, (sx, sy, sr) in geo["switches"].items():
        assert sr == 0, f"{key}: the key network is drawn for a switch at 0 degrees"
        for row, (dx, dy, way) in KEY_NET.items():
            place[pcb.ref_of(comps, row, key)] = (sx + dx, sy + dy, way)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    seat_chain(fps[pcb.ref_of(comps, "J-CHAIN")], geo)
    loose = sorted(r for r in fps if not r.startswith(BODY) and r not in place)
    if loose:
        raise SystemExit(f"lh_layout: no place given for {', '.join(loose)}")
    for ref, (x, y, way) in place.items():
        seat(fps[ref], x, y, way)
    return place


def strip(board):
    """Rev A's copper and silkscreen go; the zones' outlines stay, emptied."""
    for t in list(board.GetTracks()):
        board.Delete(t)
    for z in board.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    for d in [d for d in board.GetDrawings() if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]:
        board.Delete(d)


# ---- the copper: every track and via, by hand ---------------------------------------------------
# All of it on the parts face (B.Cu); the switch-side face is ground and nothing else. Each
# line is a list of points in the body frame, drawn at 0, 45 and 90 degrees. T: (net, width,
# points); VIAS: (net, point), ground only.
TW, PW = 0.25, 0.4            # signal and 3V3 (layout.yaml rules: track, power_track)
VIA, DRILL = 0.7, 0.3         # layout.yaml rules: via, via_drill
GND, V33 = "GND_CHAIN", "V3V3_CHAIN_LH"
STEM = 3.4                    # a key line climbs past its switch's pole this far from its centre, either side
T, VIAS = [], []


def track(net, pts, w=TW, layer=pcbnew.B_Cu):
    for a, b in zip(pts, pts[1:]):
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        assert dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-6, f"{net}: {a} -> {b} is not at 0, 45 or 90 degrees"
    T.append((net, w, pts, layer))


def ch(d):
    """A line's height in the channel under U1, d from its middle."""
    return UY + d


def routes(geo):
    # -- the chain bus: straight out of J-CHAIN's signal row into the channel under U1. From
    # the key row's side the channel holds SCK, SH/LD, SER, QH at half-millimetre steps, the
    # header's own order; each steps once from its pad's height to its channel height (SH/LD
    # not at all) and turns into its pad from inside.
    (x9, y9), (x10, y10), (x1, y1), (x2, y2) = upin(9), upin(10), upin(1), upin(2)
    j = jpin(5)
    track("/HOP_LH_LT", [j, (84.55, j[1]), (84.55 + j[1] - ch(0.5), ch(0.5)), (x9 - 0.5, ch(0.5)), (x9, ch(1.0)), (x9, y9)])
    j = jpin(7)
    track("/CHAIN_SER_LH", [j, (84.55, j[1]), (84.55 + j[1] - ch(0), ch(0)), (x10 - 1.0, ch(0)), (x10, ch(1.0)), (x10, y10)])
    j = jpin(9)
    track("/CHAIN_SHLD", [j, (x1 - 0.5, ch(-0.5)), (x1, ch(-1.0)), (x1, y1)])
    j = jpin(11)
    track("/CHAIN_SCK", [j, (84.6, j[1]), (84.6 + ch(-1.0) - j[1], ch(-1.0)), (x2 - 0.3, ch(-1.0)), (x2, ch(-1.3)), (x2, y2)])

    # -- 3V3, one trunk. Pin 3 straight into C7; up to the spine past the far row and along it
    # through R11 to C8 and pin 12; under the body to pin 16 and out to C6; then between
    # LH5's line and LH4's down to LH5's pull-up, round LH4 by the tail side to its pull-up,
    # and back along the near edge through the row keys' pull-ups, ending at LH1's.
    sw = geo["switches"]
    pu1 = {k: (x - 0.94, y - DROP - 1.825) for k, (x, y, _) in sw.items()}       # each pull-up's rail pad
    j, c7 = jpin(3), (PLACE["C7"][0], jpin(3)[1])
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
    track(V33, [j, c7, (c7[0] + 1.0, c7[1]), (c7[0] + 1.0 + Y_RAIL - c7[1], Y_RAIL), r11, (x12 - 0.5, Y_RAIL), (x12, Y_RAIL - 0.5),
                (x12, Y_CAPS), upin(12), (x12, ch(1.7)), (x12 + 0.8, ch(0.9)), (x16 - 0.8, ch(0.9)), (x16, ch(1.7)), upin(16),
                (x16, UY + 3.45), (c6[0], UY + 3.45 + c6[0] - x16), c6, (xt, c6[1] - (xt - c6[0])), (xt, yr5 + 3.0), (xt + 3.0, yr5),
                pu1["LH5"], (xe - 6.3, yr5), (xe, yr5 - 6.3), (xe, yr4 + 1.5), (xe - 1.5, yr4), pu1["LH4"], (xw + 3.8, yr4),
                (xw, yr4 + 3.8), (xw, yr - 3.2), (xw - 3.2, yr), pu1["LH3"], pu1["LH2"], pu1["LH1"]], PW)

    # -- each key, the same copper at all five: a neck from each pin straight out to its part,
    # and the node from the resistor's lower pad down at 45, along under both pins through the
    # pull-up, and up at 45 into the capacitor's lower pad.
    ser = {k: (x + X_SER, y - 4.7 - 1.825) for k, (x, y, _) in sw.items()}     # each node's mouth end
    cap = {k: (x + X_CAP, y - 5.75 - 1.825) for k, (x, y, _) in sw.items()}    # and its tail end
    for k, (sx, sy, _) in sw.items():
        ry, cy = sy - DROP - ser[k][1], sy - DROP - cap[k][1]
        track("/KEY_" + k, [ser[k], (ser[k][0] - ry, sy - DROP), (cap[k][0] + cy, sy - DROP), cap[k]])
        track(f"/{k}/SWITCH_LEG", [(sx - 4.4, sy - 4.7), (sx + X_SER, sy - 4.7)])
        track(GND, [(sx + 2.6, sy - 5.75), (sx + X_CAP, sy - 5.75)])

    # -- the key lines. Each leaves the end of its node that faces the register (owner,
    # 2026-11-20): LH1..LH3 the tail end, LH4 and LH5 the mouth end. It steps sideways off the
    # pad, clear of the pad above it, and climbs.
    def tail_end(k):
        (x, y) = cap[k]
        return [(x, y), (x + 0.8, y), (x + 1.3, y + 0.5)]

    def mouth_end(k, to):
        """To the column x = `to`, mouth side of the resistor."""
        (x, y) = ser[k]
        return [(x, y), (to + 0.5, y), (to, y + 0.5)]

    (x6, y6), (x5, y5), (x4, y4), (x3, y3), (x14, y14) = upin(6), upin(5), upin(4), upin(3), upin(14)
    # LH1 and LH2 climb beside their own capacitor to a little past the pole, cross at 45 to
    # their height under the header's pin rows, and turn up into pins 6 and 5, LH1 nearer
    for k, lvl, (px, py) in (("LH1", ch(-4.0), (x6, y6)), ("LH2", ch(-4.5), (x5, y5))):
        xc, yt = cap[k][0] + 1.3, sw[k][1] + 0.9
        track("/KEY_" + k, tail_end(k) + [(xc, yt), (xc + lvl - yt, lvl), (px - 0.5, lvl), (px, lvl + 0.5), (px, py)])
    # The corridor between LH3's capacitor and LH5's resistor carries four lines side by side,
    # in the order they reach the register and the trunk reaches LH5: LH3, LH4, 3V3, LH5.
    xl3 = cap["LH3"][0] + 1.3
    xl4, xt, xl5 = xl3 + 0.6, xl3 + 1.2, xl3 + 1.8
    assert xl5 + 0.125 + 0.2 <= ser["LH5"][0] - 0.725 + 1e-6, "LH5's line fouls its own resistor"
    # LH3 and LH4 cross together at 45 to stand under pins 4 and 3
    track("/KEY_LH3", tail_end("LH3") + [(xl3, 31.5), (x4, 31.5 + xl3 - x4), (x4, y4)])
    track("/KEY_LH4", mouth_end("LH4", xl4) + [(xl4, 32.1), (x3, 32.1 + xl4 - x3), (x3, y3)])
    # LH5: out of the far row between C8 and C6, over C6's ground via, and straight down the corridor
    track("/KEY_LH5", [(x14, y14), (x14, UY + 3.6), (x14 + 0.3, UY + 3.9), (x14 + 0.3, Y_VIA + 0.55), (x14 + 0.8, Y_VIA + 1.05),
                       (xl5 - 0.5, Y_VIA + 1.05), (xl5, Y_VIA + 0.55)] + mouth_end("LH5", xl5)[::-1])
    # the free input: pin 11 up into its pull-up
    x11, y11 = upin(11)
    track("/KEY_FREE3", [(x11, y11), (x11, UY + 3.4), (x11 - 0.5, UY + 3.9), (x11 - 0.5, Y_RAIL - 1.825)])

    # -- ground: no track runs anywhere. Each of these is a pad's own short stub to a via
    # into the switch-side face.
    x8, y8 = upin(8)
    track(GND, [(x8, y8), (x8 - 1.3, y8)])                       # U1's ground pin, toward the header
    VIAS.append((GND, (x8 - 1.3, y8)))
    x13, y13 = upin(13)
    c82 = (x12 + 1.9, Y_CAPS)
    track(GND, [(x13, y13), (x13, UY + 3.6), (x13 + 0.5, UY + 4.1)])   # pin 13 into C8's ground pad
    track(GND, [c82, (c82[0], Y_VIA)])
    VIAS.append((GND, (c82[0], Y_VIA)))
    x15, y15 = upin(15)
    track(GND, [(x15, y15), (x15, Y_VIA)])                       # pin 15 up through C6's ground pad
    VIAS.append((GND, (x15, Y_VIA)))
    c72 = (PLACE["C7"][0], jpin(3)[1] + 1.9)
    track(GND, [c72, (c72[0], c72[1] + 1.5)])                    # C7's ground end
    VIAS.append((GND, (c72[0], c72[1] + 1.5)))


Y_VIA = Y_CAPS + 1.65         # C8's and C6's ground vias, past their pads


def draw(board):
    for net, w, pts, layer in T:
        ni = board.FindNet(net)
        assert ni is not None, net
        for a, b in zip(pts, pts[1:]):
            if math.dist(a, b) < 1e-6:
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcb.V(*pcb.to_pcb(*a)))
            t.SetEnd(pcb.V(*pcb.to_pcb(*b)))
            t.SetWidth(pcb.MM(w))
            t.SetLayer(layer)
            t.SetNet(ni)
            board.Add(t)
    for net, p in VIAS + [(GND, q) for q in STITCH]:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcb.V(*pcb.to_pcb(*p)))
        v.SetWidth(pcbnew.F_Cu, pcb.MM(VIA))
        v.SetDrill(pcb.MM(DRILL))
        v.SetNet(board.FindNet(net))
        board.Add(v)


STITCH = []


def no_parts_face_pour(board):
    """NO PARTS-FACE POUR (owner, 2026-11-20: "if we had the ground plane on the bottom, we
    don't need to fill in the top layer correct?"). Correct: the switch-side face is one whole
    ground plane under every line, and these are slow lines. The parts face's fill added
    nothing to it, and the tracks cut it into regions joined by necks, slivers between pads
    and a closed pocket by the register - each of which was then a thing to fix. Every
    ground pad on this face reaches the plane without it: the capacitors by their necks to
    the switches' through-hole pins or by their own vias, the register's pins by vias, the
    header's by its pins. So rev A's parts-face zone is deleted, not refilled."""
    for z in list(board.Zones()):
        if not z.GetIsRuleArea() and z.GetNetname() == GND and z.IsOnLayer(pcbnew.B_Cu) and not z.IsOnLayer(pcbnew.F_Cu):
            board.Delete(z)


def relieve(board):
    """Every ground pad the plane meets is joined to it by relief spokes (owner, 2026-11-20:
    "Do the resistors that land on ground need their own ground pad so they can actually be
    soldered?"), so no pad to be soldered is one piece with a plane. Vias stay solid."""
    for z in board.Zones():
        if z.GetNetname() == GND:
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)


def fill(path):
    """The zones filled in a process of their own: filling a board just edited in memory
    crashes KiCad 9's Python. ZONE_FILLER pours the planes; it routes nothing."""
    code = ("import pcbnew, sys; b = pcbnew.LoadBoard(sys.argv[1]); b.BuildConnectivity(); "
            "pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[1], b)")
    subprocess.run([sys.executable, "-c", code, path], check=True)


def main():
    lay = yaml.safe_load(open(os.path.join(HERE, "layout.yaml")))
    comps, _ = pcb.sheet_netlist(os.path.join(HERE, NAME + ".kicad_sch"))
    board = pcbnew.LoadBoard(SRC)
    strip(board)
    place = placement(board, comps)
    if "--place-only" not in sys.argv:
        routes(pcb.cad_geometry("left_hand"))
        draw(board)
    board.GetTitleBlock().SetDate(lay["silk"]["date"])
    relieve(board)
    no_parts_face_pour(board)
    pcb.add_silk_generic(board, lay, comps)
    pcb.silk_off_vias(board)
    pcbnew.SaveBoard(OUT, board)
    fill(OUT)
    n = sum(len(pts) - 1 for _, _, pts, _ in T)
    print(f"lh_layout: {len(place)} part(s) seated, {n} track segment(s), {len(VIAS)} via(s) by pads, "
          f"{len(STITCH)} stitching via(s); wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
